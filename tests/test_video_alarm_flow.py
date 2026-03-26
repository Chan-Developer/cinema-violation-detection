import io
import os
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np

from app import create_app
from config import config as app_config
from models import (
    db, Alarm, AlarmType, AlarmLevel, Camera, AlarmActionLog,
    ALARM_STATUS_PENDING, ALARM_STATUS_CONFIRMED, ALARM_STATUS_PROCESSING,
    ALARM_STATUS_RESOLVED, ALARM_STATUS_IGNORED
)
from services.video_detection import video_detection_manager


class VideoAndAlarmFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, 'test.db')
        app_config['testing'].SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"

        self.app, _ = create_app('testing')
        self.client = self.app.test_client()
        self.auth_headers = self._login_headers()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
        self.temp_dir.cleanup()

    def _login_headers(self):
        resp = self.client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        token = data['access_token']
        return {'Authorization': f'Bearer {token}'}

    def _create_alarm(self, alarm_code='photo'):
        with self.app.app_context():
            camera = Camera.query.first()
            alarm_type = AlarmType.query.filter_by(code=alarm_code).first()
            level = AlarmLevel.query.filter_by(code='low').first()
            alarm = Alarm(
                alarm_type_id=alarm_type.id,
                camera_id=camera.id,
                level_id=level.id,
                title='单元测试告警',
                description='test',
                location='test-location',
                confidence=0.61,
                status=ALARM_STATUS_PENDING
            )
            db.session.add(alarm)
            db.session.commit()
            return alarm.id

    def test_alarm_status_flow_and_action_logs(self):
        alarm_id = self._create_alarm('photo')

        resp_confirm = self.client.post(f'/api/alarms/{alarm_id}/confirm', headers=self.auth_headers)
        self.assertEqual(resp_confirm.status_code, 200)
        self.assertTrue(resp_confirm.get_json()['success'])

        resp_process = self.client.post(
            f'/api/alarms/{alarm_id}/process',
            json={'note': '现场核查中'},
            headers=self.auth_headers
        )
        self.assertEqual(resp_process.status_code, 200)
        self.assertTrue(resp_process.get_json()['success'])

        resp_resolve = self.client.post(
            f'/api/alarms/{alarm_id}/resolve',
            json={'note': '已处置完成'},
            headers=self.auth_headers
        )
        self.assertEqual(resp_resolve.status_code, 200)
        self.assertTrue(resp_resolve.get_json()['success'])

        with self.app.app_context():
            alarm = Alarm.query.get(alarm_id)
            self.assertEqual(alarm.status, ALARM_STATUS_RESOLVED)

        logs_resp = self.client.get(f'/api/alarms/{alarm_id}/logs', headers=self.auth_headers)
        self.assertEqual(logs_resp.status_code, 200)
        logs = logs_resp.get_json()['logs']
        actions = [entry['action'] for entry in logs]
        self.assertEqual(actions, ['confirm', 'process', 'resolve'])

    def test_ignore_alarm_flow(self):
        alarm_id = self._create_alarm('smoke')

        resp_ignore = self.client.post(
            f'/api/alarms/{alarm_id}/ignore',
            json={'note': '误报，忽略'},
            headers=self.auth_headers
        )
        self.assertEqual(resp_ignore.status_code, 200)
        self.assertTrue(resp_ignore.get_json()['success'])

        with self.app.app_context():
            alarm = Alarm.query.get(alarm_id)
            self.assertEqual(alarm.status, ALARM_STATUS_IGNORED)
            logs = AlarmActionLog.query.filter_by(alarm_id=alarm_id).all()
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].action, 'ignore')

    def test_video_upload_endpoint_creates_task(self):
        with patch('api.detect.video_detection_manager.start_task', return_value='task-001') as mocked:
            resp = self.client.post(
                '/api/detect/video',
                data={
                    'file': (io.BytesIO(b'fake-video-bytes'), 'demo.mp4'),
                    'frame_interval': '90'
                },
                headers=self.auth_headers,
                content_type='multipart/form-data'
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data['success'])
            self.assertEqual(data['task_id'], 'task-001')
            mocked.assert_called_once()

    def test_video_task_detects_every_90_frames_and_keeps_images(self):
        class FakeVideoCapture:
            def __init__(self, _path):
                self.total = 200
                self.idx = 0

            def isOpened(self):
                return True

            def get(self, prop):
                if int(prop) == 7:  # cv2.CAP_PROP_FRAME_COUNT
                    return self.total
                return 30

            def read(self):
                if self.idx >= self.total:
                    return False, None
                self.idx += 1
                frame = np.zeros((64, 64, 3), dtype=np.uint8)
                return True, frame

            def release(self):
                return None

        class FakeDetector:
            calls = 0

            def __init__(self, camera_id, detection_types):
                self.camera_id = camera_id
                self.detection_types = detection_types
                self.last_detection_time = {}

            def _detect(self, _frame):
                FakeDetector.calls += 1
                return [{
                    'type': 'phone',
                    'box': [5, 5, 30, 30],
                    'confidence': 0.91
                }]

        with self.app.app_context():
            camera = Camera.query.first()
            camera_id = camera.id

        with patch('services.video_detection.cv2.VideoCapture', FakeVideoCapture), \
                patch('services.video_detection.DetectionWorker', FakeDetector), \
                patch('services.video_detection.socketio.emit', lambda *args, **kwargs: None):

            task_id = video_detection_manager.start_task(
                app=self.app,
                video_path='/tmp/fake.mp4',
                camera_id=camera_id,
                detection_types='phone',
                frame_interval=90,
                created_by=1
            )

            task = None
            for _ in range(200):
                task = video_detection_manager.get_task(task_id)
                if task and task['status'] in ('completed', 'failed'):
                    break
                time.sleep(0.05)

            self.assertIsNotNone(task)
            self.assertEqual(task['status'], 'completed')
            self.assertEqual(task['sampled_frames'], 2)
            self.assertEqual(FakeDetector.calls, 2)
            self.assertEqual(len(task['samples']), 2)
            self.assertGreaterEqual(task['alarms_created'], 1)

            project_root = os.path.dirname(os.path.dirname(__file__))
            for sample in task['samples']:
                image_url = sample['image_url']
                self.assertTrue(image_url.startswith('/static/alarms/video/'))
                image_name = image_url.split('/static/alarms/video/', 1)[1]
                image_path = os.path.join(project_root, 'static', 'alarms', 'video', image_name)
                self.assertTrue(os.path.exists(image_path))

        with self.app.app_context():
            alarms = Alarm.query.filter_by(camera_id=camera_id).all()
            self.assertGreaterEqual(len(alarms), 1)
            created_logs = AlarmActionLog.query.filter_by(action='created').all()
            self.assertGreaterEqual(len(created_logs), 1)

    def test_video_task_without_camera_uses_upload_source(self):
        class FakeVideoCapture:
            def __init__(self, _path):
                self.total = 100
                self.idx = 0

            def isOpened(self):
                return True

            def get(self, prop):
                if int(prop) == 7:
                    return self.total
                return 25

            def read(self):
                if self.idx >= self.total:
                    return False, None
                self.idx += 1
                frame = np.zeros((48, 48, 3), dtype=np.uint8)
                return True, frame

            def release(self):
                return None

        class FakeDetector:
            def __init__(self, camera_id, detection_types):
                self.camera_id = camera_id
                self.detection_types = detection_types
                self.last_detection_time = {}

            def _detect(self, _frame):
                return [{
                    'type': 'smoke',
                    'box': [2, 2, 20, 20],
                    'confidence': 0.88
                }]

        with patch('services.video_detection.cv2.VideoCapture', FakeVideoCapture), \
                patch('services.video_detection.DetectionWorker', FakeDetector), \
                patch('services.video_detection.socketio.emit', lambda *args, **kwargs: None):
            task_id = video_detection_manager.start_task(
                app=self.app,
                video_path='/tmp/upload_only.mp4',
                camera_id=None,
                cinema_id=None,
                detection_types='smoke',
                frame_interval=90,
                created_by=1
            )

            task = None
            for _ in range(200):
                task = video_detection_manager.get_task(task_id)
                if task and task['status'] in ('completed', 'failed'):
                    break
                time.sleep(0.05)

            self.assertIsNotNone(task)
            self.assertEqual(task['status'], 'completed')
            self.assertGreaterEqual(task['alarms_created'], 1)

        with self.app.app_context():
            upload_camera = Camera.query.filter_by(name='视频上传源').first()
            self.assertIsNotNone(upload_camera)
            alarms = Alarm.query.filter_by(camera_id=upload_camera.id).all()
            self.assertGreaterEqual(len(alarms), 1)


if __name__ == '__main__':
    unittest.main()
