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
    VideoRecognitionResult,
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
                    'frame_interval': '90',
                    'alarm_window_seconds': '45',
                    'alarm_threshold': '2',
                    'alarm_cooldown_seconds': '30'
                },
                headers=self.auth_headers,
                content_type='multipart/form-data'
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data['success'])
            self.assertEqual(data['task_id'], 'task-001')
            self.assertEqual(data['alarm_policy']['window_seconds'], 45)
            self.assertEqual(data['alarm_policy']['threshold'], 2)
            self.assertEqual(data['alarm_policy']['cooldown_seconds'], 30)
            mocked.assert_called_once()
            kwargs = mocked.call_args.kwargs
            self.assertEqual(kwargs['frame_interval'], 90)
            self.assertEqual(kwargs['alarm_window_seconds'], 45)
            self.assertEqual(kwargs['alarm_threshold'], 2)
            self.assertEqual(kwargs['alarm_cooldown_seconds'], 30)

    def test_video_upload_endpoint_rejects_image_file(self):
        resp = self.client.post(
            '/api/detect/video',
            data={'file': (io.BytesIO(b'fake-image'), 'demo.jpg')},
            headers=self.auth_headers,
            content_type='multipart/form-data'
        )
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data['success'])
        self.assertIn('不支持的文件格式', data['message'])

    def test_video_task_results_endpoint_returns_persisted_records(self):
        with self.app.app_context():
            camera = Camera.query.first()
            rec = VideoRecognitionResult(
                task_id='task-db-001',
                camera_id=camera.id,
                cinema_id=camera.cinema_id,
                frame_index=90,
                image_url='/static/alarms/video/demo.jpg',
                person_count=1,
                violation=True,
                violation_codes='photo',
                llm_summary='存在拍照行为',
                llm_reply='- 拍照/录视频：有'
            )
            db.session.add(rec)
            db.session.commit()

        resp = self.client.get('/api/detect/video/tasks/task-db-001/results', headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['results'][0]['frame_index'], 90)
        self.assertEqual(data['results'][0]['violation_codes'], ['photo'])

    def test_video_task_status_recovers_from_persisted_records_when_memory_missing(self):
        with self.app.app_context():
            camera = Camera.query.first()
            rec1 = VideoRecognitionResult(
                task_id='lost-task-001',
                camera_id=camera.id,
                cinema_id=camera.cinema_id,
                frame_index=90,
                image_url='/static/alarms/video/f1.jpg',
                person_count=1,
                violation=False,
                violation_codes='',
                llm_summary='未见明显违规',
                llm_reply='结论：画面正常'
            )
            rec2 = VideoRecognitionResult(
                task_id='lost-task-001',
                camera_id=camera.id,
                cinema_id=camera.cinema_id,
                frame_index=180,
                image_url='/static/alarms/video/f2.jpg',
                person_count=1,
                violation=True,
                violation_codes='photo',
                llm_summary='发现拍照行为',
                llm_reply='结论：存在拍照风险'
            )
            db.session.add(rec1)
            db.session.add(rec2)
            db.session.commit()

        resp = self.client.get('/api/detect/video/tasks/lost-task-001', headers=self.auth_headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        task = data['task']
        self.assertEqual(task['status'], 'completed')
        self.assertEqual(task['progress'], 100)
        self.assertEqual(task['sampled_frames'], 2)
        self.assertEqual(task['records_saved'], 2)
        self.assertEqual(task['violation_frames'], 1)
        self.assertIn('恢复', task['message'])

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
                    'type': 'person',
                    'box': [5, 5, 30, 30],
                    'confidence': 0.91
                }]

        with self.app.app_context():
            camera = Camera.query.first()
            camera_id = camera.id

        with patch('services.video_detection.cv2.VideoCapture', FakeVideoCapture), \
                patch('services.video_detection.DetectionWorker', FakeDetector), \
                patch('services.video_detection.socketio.emit', lambda *args, **kwargs: None), \
                patch('services.video_detection.call_llm_api', return_value=(
                    "# 影院行为监管员报告\n"
                    "- 抽烟行为：无（未发现）\n"
                    "- 拍照/录视频：有（有人使用手机拍摄）\n"
                    "- 其他违规：无（未发现）\n"
                    "结论：存在盗摄风险，请尽快处置"
                )):

            task_id = video_detection_manager.start_task(
                app=self.app,
                video_path='/tmp/fake.mp4',
                camera_id=camera_id,
                detection_types='person',
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
            self.assertGreaterEqual(task['records_saved'], 1)
            self.assertGreaterEqual(task['violation_frames'], 1)
            for sample in task['samples']:
                self.assertIn('llm_analysis', sample)
                self.assertTrue(sample['llm_analysis']['violation'])
                self.assertIn('photo', sample['llm_analysis']['violation_codes'])

            project_root = os.path.dirname(os.path.dirname(__file__))
            for sample in task['samples']:
                image_url = sample['image_url']
                self.assertTrue(image_url.startswith('/static/alarms/video/'))
                image_name = image_url.split('/static/alarms/video/', 1)[1]
                image_path = os.path.join(project_root, 'static', 'alarms', 'video', image_name)
                self.assertTrue(os.path.exists(image_path))

        with self.app.app_context():
            alarms = Alarm.query.filter_by(camera_id=camera_id).all()
            self.assertEqual(len(alarms), 0)
            results = VideoRecognitionResult.query.filter_by(task_id=task_id).all()
            self.assertGreaterEqual(len(results), 1)
            self.assertIn('拍照/录视频：有', results[0].llm_reply or '')
            self.assertTrue(results[0].violation)
            self.assertIn('photo', (results[0].violation_codes or ''))

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
                    'type': 'person',
                    'box': [2, 2, 20, 20],
                    'confidence': 0.88
                }]

        with patch('services.video_detection.cv2.VideoCapture', FakeVideoCapture), \
                patch('services.video_detection.DetectionWorker', FakeDetector), \
                patch('services.video_detection.socketio.emit', lambda *args, **kwargs: None), \
                patch('services.video_detection.call_llm_api', return_value=(
                    "# 影院行为监管员报告\n"
                    "- 抽烟行为：有（检测到疑似吸烟动作）\n"
                    "- 拍照/录视频：无（未发现）\n"
                    "- 其他违规：无（未发现）\n"
                    "结论：存在吸烟违规，请现场核查"
                )):
            task_id = video_detection_manager.start_task(
                app=self.app,
                video_path='/tmp/upload_only.mp4',
                camera_id=None,
                cinema_id=None,
                detection_types='person',
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
            self.assertGreaterEqual(task['records_saved'], 1)
            self.assertGreaterEqual(task['violation_frames'], 1)

        with self.app.app_context():
            upload_camera = Camera.query.filter_by(name='视频上传源').first()
            self.assertIsNotNone(upload_camera)
            alarms = Alarm.query.filter_by(camera_id=upload_camera.id).all()
            self.assertEqual(len(alarms), 0)
            records = VideoRecognitionResult.query.filter_by(task_id=task_id).all()
            self.assertGreaterEqual(len(records), 1)
            self.assertEqual(records[0].camera_id, upload_camera.id)

    def test_video_task_no_violation_does_not_create_alarm(self):
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
                    'type': 'person',
                    'box': [1, 1, 18, 18],
                    'confidence': 0.77
                }]

        with self.app.app_context():
            camera = Camera.query.first()
            camera_id = camera.id

        with patch('services.video_detection.cv2.VideoCapture', FakeVideoCapture), \
                patch('services.video_detection.DetectionWorker', FakeDetector), \
                patch('services.video_detection.socketio.emit', lambda *args, **kwargs: None), \
                patch('services.video_detection.call_llm_api', return_value=(
                    "# 影院行为监管员报告\n"
                    "- 抽烟行为：无（未发现）\n"
                    "- 拍照/录视频：无（未发现）\n"
                    "- 其他违规：无（未发现）\n"
                    "结论：画面正常，无明显违规"
                )):
            task_id = video_detection_manager.start_task(
                app=self.app,
                video_path='/tmp/no_violation.mp4',
                camera_id=camera_id,
                detection_types='person',
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
            self.assertEqual(task['violation_frames'], 0)
            self.assertGreaterEqual(task['records_saved'], 1)

        with self.app.app_context():
            alarms = Alarm.query.filter_by(camera_id=camera_id).all()
            self.assertEqual(len(alarms), 0)
            results = VideoRecognitionResult.query.filter_by(task_id=task_id).all()
            self.assertGreaterEqual(len(results), 1)
            self.assertFalse(results[0].violation)

    def test_video_task_without_person_still_saves_records(self):
        class FakeVideoCapture:
            def __init__(self, _path):
                self.total = 200
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
                return []

        with self.app.app_context():
            camera = Camera.query.first()
            camera_id = camera.id

        with patch('services.video_detection.cv2.VideoCapture', FakeVideoCapture), \
                patch('services.video_detection.DetectionWorker', FakeDetector), \
                patch('services.video_detection.socketio.emit', lambda *args, **kwargs: None):
            task_id = video_detection_manager.start_task(
                app=self.app,
                video_path='/tmp/no_person.mp4',
                camera_id=camera_id,
                detection_types='person',
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
            self.assertEqual(task['hit_samples'], 0)
            self.assertEqual(task['records_saved'], 2)

        with self.app.app_context():
            results = VideoRecognitionResult.query.filter_by(task_id=task_id).order_by(
                VideoRecognitionResult.frame_index.asc()
            ).all()
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0].person_count, 0)
            self.assertFalse(results[0].violation)
            self.assertIn('未检测到人员', results[0].llm_summary or '')

    def test_video_task_threshold_violation_creates_alarm_with_latest_frame(self):
        class FakeVideoCapture:
            def __init__(self, _path):
                self.total = 120
                self.idx = 0

            def isOpened(self):
                return True

            def get(self, prop):
                if int(prop) == 7:  # cv2.CAP_PROP_FRAME_COUNT
                    return self.total
                if int(prop) == 5:  # cv2.CAP_PROP_FPS
                    return 30
                return 30

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
                    'type': 'person',
                    'box': [8, 8, 32, 32],
                    'confidence': 0.92
                }]

        with self.app.app_context():
            camera = Camera.query.first()
            camera_id = camera.id

        with patch('services.video_detection.cv2.VideoCapture', FakeVideoCapture), \
                patch('services.video_detection.DetectionWorker', FakeDetector), \
                patch('services.video_detection.socketio.emit', lambda *args, **kwargs: None), \
                patch('services.video_detection.emit_alarm', lambda *args, **kwargs: None), \
                patch('services.video_detection.call_llm_api', return_value=(
                    "# 影院行为监管员报告\n"
                    "- 抽烟行为：无（未发现）\n"
                    "- 拍照/录视频：有（有人举起手机）\n"
                    "- 其他违规：无（未发现）\n"
                    "结论：存在持续拍摄风险"
                )):
            task_id = video_detection_manager.start_task(
                app=self.app,
                video_path='/tmp/threshold_alarm.mp4',
                camera_id=camera_id,
                detection_types='person',
                frame_interval=30,
                created_by=1,
                alarm_window_seconds=10,
                alarm_threshold=2,
                alarm_cooldown_seconds=10
            )

            task = None
            for _ in range(240):
                task = video_detection_manager.get_task(task_id)
                if task and task['status'] in ('completed', 'failed'):
                    break
                time.sleep(0.05)

            self.assertIsNotNone(task)
            self.assertEqual(task['status'], 'completed')
            self.assertGreaterEqual(task['violation_frames'], 2)
            self.assertGreaterEqual(task['alarms_created'], 1)

        with self.app.app_context():
            alarms = Alarm.query.filter_by(camera_id=camera_id).all()
            self.assertGreaterEqual(len(alarms), 1)
            latest_alarm = sorted(alarms, key=lambda a: a.id)[-1]
            self.assertIn('累计检测到', latest_alarm.description or '')
            self.assertIn('大模型结论', latest_alarm.description or '')
            self.assertTrue((latest_alarm.image_url or '').startswith('/static/alarms/video/'))
            self.assertEqual(latest_alarm.status, ALARM_STATUS_PENDING)
            self.assertEqual(latest_alarm.alarm_type.code, 'photo')
            logs = AlarmActionLog.query.filter_by(alarm_id=latest_alarm.id).all()
            self.assertTrue(any(log.action == 'created' for log in logs))

    def test_parse_llm_analysis_extracts_expected_flags(self):
        raw = (
            "# 影院行为监管员报告\n"
            "- 抽烟行为：有（有人疑似吸烟）\n"
            "- 拍照/录视频：无（未发现）\n"
            "- 其他违规：有（有人频繁走动）\n"
            "结论：存在吸烟和走动行为，请尽快处置"
        )
        parsed = video_detection_manager._parse_llm_analysis(raw)
        self.assertTrue(parsed['violation'])
        self.assertTrue(parsed['flags']['smoke'])
        self.assertFalse(parsed['flags']['photo'])
        self.assertTrue(parsed['flags']['other'])
        self.assertIn('smoke', parsed['violation_codes'])
        self.assertIn('walk', parsed['violation_codes'])
        self.assertIn('处置', parsed['summary'])

    def test_parse_llm_analysis_with_empty_reply(self):
        parsed = video_detection_manager._parse_llm_analysis('')
        self.assertFalse(parsed['violation'])
        self.assertEqual(parsed['violation_codes'], [])
        self.assertEqual(parsed['summary'], '大模型未返回有效内容')


if __name__ == '__main__':
    unittest.main()
