import os
import cv2
import time
import threading
import uuid
from datetime import datetime

from models import (
    db, Cinema, Camera, Alarm, AlarmType, AlarmLevel, AlarmActionLog,
    ALARM_STATUS_PENDING
)
from services.detection import DetectionWorker
from services.websocket import socketio, emit_alarm


class VideoDetectionTaskManager:
    """上传视频检测任务管理器（每隔 N 帧检测一次）"""

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.tasks = {}
            self.lock = threading.Lock()
            self.initialized = True

    def start_task(
        self,
        app,
        video_path,
        camera_id=None,
        cinema_id=None,
        detection_types='',
        frame_interval=90,
        created_by=None
    ):
        frame_interval = max(1, int(frame_interval or 90))
        task_id = uuid.uuid4().hex
        now = datetime.now().isoformat()

        task = {
            'task_id': task_id,
            'status': 'pending',  # pending, running, completed, failed
            'message': '任务已创建',
            'progress': 0,
            'frame_interval': frame_interval,
            'camera_id': camera_id,
            'cinema_id': cinema_id,
            'created_by': created_by,
            'video_path': video_path,
            'total_frames': 0,
            'processed_frames': 0,
            'sampled_frames': 0,
            'hit_samples': 0,
            'alarms_created': 0,
            'samples': [],
            'created_at': now,
            'updated_at': now,
            'finished_at': None,
            'summary': None,
        }

        with self.lock:
            self.tasks[task_id] = task

        worker = threading.Thread(
            target=self._run_task,
            args=(app, task_id, detection_types),
            daemon=True
        )
        worker.start()
        return task_id

    def get_task(self, task_id):
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            return dict(task)

    def _update_task(self, task_id, **kwargs):
        with self.lock:
            if task_id not in self.tasks:
                return
            self.tasks[task_id].update(kwargs)
            self.tasks[task_id]['updated_at'] = datetime.now().isoformat()

    def _run_task(self, app, task_id, detection_types):
        task = self.get_task(task_id)
        if not task:
            return

        video_path = task['video_path']
        frame_interval = task['frame_interval']
        camera_id = task['camera_id']
        cinema_id = task.get('cinema_id')
        alarms_created = 0
        sampled_frames = 0
        hit_samples = 0
        frame_index = 0
        cooldown_map = {}

        self._update_task(task_id, status='running', message='开始处理视频')
        cap = None

        try:
            with app.app_context():
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    raise RuntimeError('无法打开视频文件')

                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                self._update_task(task_id, total_frames=total_frames)

                camera = Camera.query.get(camera_id) if camera_id else None
                if not detection_types and camera and camera.detection_types:
                    detection_types = camera.detection_types
                if not detection_types:
                    detection_types = 'photo,smoke,crowd,walk,phone,person'

                detector = DetectionWorker(camera_id=camera_id or 0, detection_types=detection_types)

                while True:
                    ok, frame = cap.read()
                    if not ok:
                        break

                    frame_index += 1
                    progress = int((frame_index / total_frames) * 100) if total_frames else 0
                    self._update_task(
                        task_id,
                        processed_frames=frame_index,
                        progress=min(progress, 99)
                    )

                    if frame_index % frame_interval != 0:
                        continue

                    sampled_frames += 1
                    detector.last_detection_time = {}
                    detections_raw = detector._detect(frame)
                    detections = self._normalize_detections(detections_raw)
                    if not detections:
                        continue

                    hit_samples += 1
                    image_url = self._save_annotated_frame(task_id, frame_index, frame.copy(), detections)
                    alarm_codes = self._infer_alarm_codes(detections)

                    alarm_ids = []
                    for alarm_code in alarm_codes:
                        alarm_id = self._create_alarm_from_detection(
                            camera_id=camera_id,
                            cinema_id=cinema_id,
                            alarm_code=alarm_code,
                            frame_index=frame_index,
                            image_url=image_url,
                            detections=detections,
                            task_id=task_id,
                            cooldown_map=cooldown_map,
                        )
                        if alarm_id:
                            alarms_created += 1
                            alarm_ids.append(alarm_id)

                    sample = {
                        'frame_index': frame_index,
                        'image_url': image_url,
                        'detections': detections,
                        'alarm_codes': alarm_codes,
                        'alarm_ids': alarm_ids,
                    }
                    self._append_sample(task_id, sample)

                    socketio.emit('video_detection_progress', {
                        'task_id': task_id,
                        'progress': min(progress, 99),
                        'sample': sample
                    })

                summary = (
                    f"视频处理完成：共处理{frame_index}帧，采样{sampled_frames}帧，"
                    f"命中{hit_samples}次，创建{alarms_created}条告警。"
                )
                self._update_task(
                    task_id,
                    status='completed',
                    progress=100,
                    message='处理完成',
                    sampled_frames=sampled_frames,
                    hit_samples=hit_samples,
                    alarms_created=alarms_created,
                    summary=summary,
                    finished_at=datetime.now().isoformat()
                )
                socketio.emit('video_detection_done', {
                    'task_id': task_id,
                    'status': 'completed',
                    'summary': summary
                })

        except Exception as e:
            self._update_task(
                task_id,
                status='failed',
                message=f'处理失败: {e}',
                sampled_frames=sampled_frames,
                hit_samples=hit_samples,
                alarms_created=alarms_created,
                finished_at=datetime.now().isoformat()
            )
            socketio.emit('video_detection_done', {
                'task_id': task_id,
                'status': 'failed',
                'message': str(e)
            })
        finally:
            if cap:
                cap.release()

    def _append_sample(self, task_id, sample):
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return
            task['samples'].append(sample)
            # 防止内存持续膨胀，最多保留 100 个命中样本
            if len(task['samples']) > 100:
                task['samples'] = task['samples'][-100:]
            task['updated_at'] = datetime.now().isoformat()

    @staticmethod
    def _normalize_detections(detections_raw):
        normalized = []
        for det in detections_raw or []:
            normalized.append({
                'class': det.get('type'),
                'confidence': det.get('confidence'),
                'box': det.get('box')
            })
        return normalized

    @staticmethod
    def _infer_alarm_codes(detections):
        classes = {d.get('class') for d in detections if d.get('class')}
        alarm_codes = set()

        if 'photo' in classes or 'phone' in classes:
            alarm_codes.add('photo')
        if 'smoke' in classes:
            alarm_codes.add('smoke')
        if 'crowd' in classes:
            alarm_codes.add('crowd')
        if 'walk' in classes:
            alarm_codes.add('walk')

        return sorted(alarm_codes)

    @staticmethod
    def _save_annotated_frame(task_id, frame_index, frame, detections):
        for det in detections:
            x1, y1, x2, y2 = det['box']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            label = f"{det['class']}: {det['confidence']:.2f}"
            cv2.putText(frame, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)

        alarm_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'alarms', 'video')
        os.makedirs(alarm_dir, exist_ok=True)
        filename = f"{task_id}_{frame_index}.jpg"
        filepath = os.path.join(alarm_dir, filename)
        cv2.imwrite(filepath, frame)
        return f"/static/alarms/video/{filename}"

    @staticmethod
    def _pick_level(max_confidence):
        if max_confidence >= 0.8:
            return AlarmLevel.query.filter_by(code='critical').first()
        if max_confidence >= 0.7:
            return AlarmLevel.query.filter_by(code='high').first()
        if max_confidence >= 0.6:
            return AlarmLevel.query.filter_by(code='medium').first()
        return AlarmLevel.query.filter_by(code='low').first()

    def _get_or_create_upload_camera(self, preferred_cinema_id=None):
        """在无摄像头模式下，使用“视频上传源”作为告警来源"""
        cinema = None
        if preferred_cinema_id:
            cinema = Cinema.query.get(preferred_cinema_id)
        if not cinema:
            cinema = Cinema.query.order_by(Cinema.id.asc()).first()
        if not cinema:
            cinema = Cinema(
                name='默认影院',
                address='',
                city='',
                district='',
                phone='',
                contact='系统自动创建',
                status=1
            )
            db.session.add(cinema)
            db.session.commit()

        camera = Camera.query.filter_by(cinema_id=cinema.id, name='视频上传源').first()
        if camera:
            return camera

        camera = Camera(
            name='视频上传源',
            cinema_id=cinema.id,
            hall_id=None,
            rtsp_url='upload://local-video',
            position='上传视频',
            detection_enabled=1,
            detection_types='photo,smoke,crowd,walk',
            status=1,
            stream_status=0,
            manufacturer='SYSTEM',
            model='UPLOAD_SOURCE'
        )
        db.session.add(camera)
        db.session.commit()
        return camera

    def _create_alarm_from_detection(
        self, camera_id, cinema_id, alarm_code, frame_index, image_url, detections, task_id, cooldown_map
    ):
        camera = Camera.query.get(camera_id) if camera_id else None
        if not camera:
            camera = self._get_or_create_upload_camera(preferred_cinema_id=cinema_id)
        if not camera:
            return None

        alarm_type = AlarmType.query.filter_by(code=alarm_code).first()
        if not alarm_type:
            return None

        source_camera_id = camera.id
        cooldown_key = f"{source_camera_id}:{alarm_code}"
        now_ts = time.time()
        last_ts = cooldown_map.get(cooldown_key, 0)
        if now_ts - last_ts < 60:
            return None

        max_confidence = max((d.get('confidence') or 0) for d in detections)
        level = self._pick_level(max_confidence)

        alarm = Alarm(
            alarm_type_id=alarm_type.id,
            camera_id=source_camera_id,
            level_id=level.id if level else 1,
            title=f'{alarm_type.name} - {camera.name}',
            description=(
                f'上传视频检测命中：第{frame_index}帧检测到{alarm_type.name}，'
                f'最大置信度 {max_confidence:.2%}'
            ),
            location=f'{camera.cinema.name if camera.cinema else ""} - {camera.hall.name if camera.hall else ""} - {camera.position or ""}',
            image_url=image_url,
            confidence=max_confidence,
            status=ALARM_STATUS_PENDING,
            occurred_at=datetime.now()
        )
        db.session.add(alarm)
        db.session.commit()

        db.session.add(AlarmActionLog(
            alarm_id=alarm.id,
            user_id=None,
            action='created',
            from_status=None,
            to_status=ALARM_STATUS_PENDING,
            note=f'视频检测任务自动创建告警 task={task_id} frame={frame_index}'
        ))
        db.session.commit()

        emit_alarm(alarm.to_dict(), target_roles=['admin', 'operator', 'manager'], target_cinema_id=camera.cinema_id)
        cooldown_map[cooldown_key] = now_ts
        return alarm.id


video_detection_manager = VideoDetectionTaskManager()
