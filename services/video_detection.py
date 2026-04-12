import os
import cv2
import threading
import uuid
import base64
import re
from datetime import datetime

from models import (
    db, Cinema, Camera, VideoRecognitionResult,
    Alarm, AlarmType, AlarmLevel, AlarmActionLog, ALARM_STATUS_PENDING
)
from services.detection import DetectionWorker
from services.websocket import socketio, emit_alarm
from utils.llm import call_llm_api


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
        created_by=None,
        alarm_window_seconds=60,
        alarm_threshold=3,
        alarm_cooldown_seconds=None
    ):
        frame_interval = max(1, int(frame_interval or 90))
        alarm_window_seconds = max(1, int(alarm_window_seconds or 60))
        alarm_threshold = max(1, int(alarm_threshold or 3))
        if alarm_cooldown_seconds is None:
            alarm_cooldown_seconds = alarm_window_seconds
        alarm_cooldown_seconds = max(1, int(alarm_cooldown_seconds))
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
            'records_saved': 0,
            'violation_frames': 0,
            'alarms_created': 0,
            'alarm_window_seconds': alarm_window_seconds,
            'alarm_threshold': alarm_threshold,
            'alarm_cooldown_seconds': alarm_cooldown_seconds,
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

    def _run_task(self, app, task_id, _detection_types):
        task = self.get_task(task_id)
        if not task:
            return

        video_path = task['video_path']
        frame_interval = task['frame_interval']
        camera_id = task['camera_id']
        cinema_id = task.get('cinema_id')
        records_saved = 0
        violation_frames = 0
        alarms_created = 0
        sampled_frames = 0
        hit_samples = 0
        frame_index = 0
        alarm_ids = []
        violation_events = []
        last_alarm_second = -1e9

        self._update_task(task_id, status='running', message='开始处理视频')
        cap = None

        try:
            with app.app_context():
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    raise RuntimeError('无法打开视频文件')

                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
                if fps <= 0:
                    fps = 25.0
                self._update_task(task_id, total_frames=total_frames, fps=round(fps, 2))

                # 新逻辑：YOLO 只做人检测，违规判定交给大模型
                detector = DetectionWorker(camera_id=camera_id or 0, detection_types='person')

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
                    person_detections = [d for d in detections if d.get('class') == 'person']
                    image_url = self._save_annotated_frame(task_id, frame_index, frame.copy(), person_detections)

                    if person_detections:
                        hit_samples += 1
                        try:
                            llm_analysis = self._analyze_frame_with_llm(frame, person_detections)
                        except Exception as llm_exc:
                            llm_analysis = {
                                'raw_reply': '',
                                'violation': False,
                                'violation_codes': [],
                                'flags': {'smoke': False, 'photo': False, 'other': False},
                                'summary': f'LLM调用失败: {llm_exc}',
                                'llm_skipped': False,
                            }
                    else:
                        llm_analysis = {
                            'raw_reply': '',
                            'violation': False,
                            'violation_codes': [],
                            'flags': {'smoke': False, 'photo': False, 'other': False},
                            'summary': '未检测到人员，跳过大模型判定',
                            'llm_skipped': True,
                        }

                    violation_codes = llm_analysis.get('violation_codes', [])
                    if llm_analysis.get('violation'):
                        violation_frames += 1

                    sample_second = frame_index / fps if fps > 0 else float(frame_index)

                    result_id = self._save_recognition_result(
                        task_id=task_id,
                        camera_id=camera_id,
                        cinema_id=cinema_id,
                        frame_index=frame_index,
                        image_url=image_url,
                        detections=person_detections,
                        llm_analysis=llm_analysis,
                    )
                    if result_id:
                        records_saved += 1

                    sample = {
                        'frame_index': frame_index,
                        'image_url': image_url,
                        'detections': person_detections,
                        'person_count': len(person_detections),
                        'violation': bool(llm_analysis.get('violation')),
                        'violation_codes': violation_codes,
                        'result_id': result_id,
                        'llm_analysis': llm_analysis,
                    }
                    self._append_sample(task_id, sample)

                    if sample['violation']:
                        violation_events.append({
                            'at_second': sample_second,
                            'frame_index': frame_index,
                            'image_url': image_url,
                            'detections': person_detections,
                            'violation_codes': violation_codes,
                            'llm_analysis': llm_analysis,
                        })
                        window_seconds = task.get('alarm_window_seconds', 60)
                        threshold = task.get('alarm_threshold', 3)
                        cooldown_seconds = task.get('alarm_cooldown_seconds', window_seconds)

                        window_start = sample_second - window_seconds
                        violation_events = [e for e in violation_events if e['at_second'] >= window_start]
                        recent_count = len(violation_events)

                        if (
                            recent_count >= threshold and
                            (sample_second - last_alarm_second) >= cooldown_seconds
                        ):
                            alarm_id = self._create_threshold_alarm(
                                task_id=task_id,
                                camera_id=camera_id,
                                cinema_id=cinema_id,
                                latest_sample=sample,
                                recent_count=recent_count,
                                window_seconds=window_seconds,
                                threshold=threshold,
                            )
                            if alarm_id:
                                alarms_created += 1
                                alarm_ids.append(alarm_id)
                                last_alarm_second = sample_second
                                self._update_task(task_id, alarms_created=alarms_created)

                    socketio.emit('video_detection_progress', {
                        'task_id': task_id,
                        'progress': min(progress, 99),
                        'sample': sample
                    })

                summary = (
                    f"视频处理完成：共处理{frame_index}帧，采样{sampled_frames}帧，"
                    f"命中{hit_samples}次，保存{records_saved}条识别结果，"
                    f"其中违规帧{violation_frames}条，触发告警{alarms_created}次。"
                )
                self._update_task(
                    task_id,
                    status='completed',
                    progress=100,
                    message='处理完成',
                    sampled_frames=sampled_frames,
                    hit_samples=hit_samples,
                    records_saved=records_saved,
                    violation_frames=violation_frames,
                    alarms_created=alarms_created,
                    alarm_ids=alarm_ids,
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
                records_saved=records_saved,
                violation_frames=violation_frames,
                alarms_created=alarms_created,
                alarm_ids=alarm_ids,
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
    def _encode_frame_to_base64(frame):
        ok, buffer = cv2.imencode('.jpg', frame)
        if not ok:
            raise RuntimeError('无法编码视频帧')
        return base64.b64encode(buffer.tobytes()).decode('utf-8')

    @staticmethod
    def _parse_llm_analysis(raw_reply):
        text = (raw_reply or '').strip()
        if not text:
            return {
                'violation': False,
                'violation_codes': [],
                'flags': {'smoke': False, 'photo': False, 'walk': False, 'crowd': False, 'other': False},
                'summary': '大模型未返回有效内容',
            }

        def extract_line_value(label):
            pattern = rf"{label}\s*[:：]\s*([^\n\r]+)"
            match = re.search(pattern, text, flags=re.IGNORECASE)
            return match.group(1).strip() if match else ''

        def is_yes(value):
            normalized = (value or '').strip().lower()
            return normalized.startswith('有') or normalized.startswith('疑似有')

        smoke_value = extract_line_value(r"抽烟行为")
        photo_value = extract_line_value(r"拍照/录视频")
        phone_value = extract_line_value(r"手机亮屏影响观影")
        walk_value = extract_line_value(r"走动/站立挡屏")
        crowd_value = extract_line_value(r"聚集/打闹")
        other_value = extract_line_value(r"其他违规")

        smoke_yes = is_yes(smoke_value)
        photo_yes = is_yes(photo_value)
        phone_yes = is_yes(phone_value)
        walk_yes = is_yes(walk_value)
        crowd_yes = is_yes(crowd_value)
        other_yes = is_yes(other_value)

        violation_codes = []
        if smoke_yes:
            violation_codes.append('smoke')
        if photo_yes or phone_yes:
            violation_codes.append('photo')
        if walk_yes or other_yes:
            violation_codes.append('walk')
        if crowd_yes:
            violation_codes.append('crowd')

        conclusion = ''
        conclusion_match = re.search(r"结论\s*[:：]\s*(.+)", text)
        if conclusion_match:
            conclusion = conclusion_match.group(1).strip()

        return {
            'violation': bool(violation_codes),
            'violation_codes': violation_codes,
            'flags': {
                'smoke': smoke_yes,
                'photo': (photo_yes or phone_yes),
                'walk': (walk_yes or other_yes),
                'crowd': crowd_yes,
                'other': other_yes,
            },
            'summary': conclusion or text[:200],
        }

    def _analyze_frame_with_llm(self, frame, person_detections):
        base64_image = self._encode_frame_to_base64(frame)
        llm_reply = call_llm_api(person_detections, base64_image)
        parsed = self._parse_llm_analysis(llm_reply)
        return {
            'raw_reply': llm_reply,
            'violation': parsed['violation'],
            'violation_codes': parsed['violation_codes'],
            'flags': parsed['flags'],
            'summary': parsed['summary'],
            'llm_skipped': False,
        }

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

    def _get_or_create_upload_camera(self, preferred_cinema_id=None):
        """在无摄像头模式下，使用“视频上传源”作为识别来源"""
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

    def _save_recognition_result(
        self, task_id, camera_id, cinema_id, frame_index, image_url, detections, llm_analysis
    ):
        camera = self._resolve_camera(camera_id, cinema_id)
        violation_codes = llm_analysis.get('violation_codes') or []
        result = VideoRecognitionResult(
            task_id=task_id,
            camera_id=camera.id if camera else None,
            cinema_id=(camera.cinema_id if camera else cinema_id),
            frame_index=frame_index,
            image_url=image_url,
            person_count=len(detections or []),
            violation=bool(llm_analysis.get('violation')),
            violation_codes=','.join(violation_codes),
            llm_summary=llm_analysis.get('summary', ''),
            llm_reply=llm_analysis.get('raw_reply', ''),
        )
        db.session.add(result)
        db.session.commit()
        return result.id

    def _resolve_camera(self, camera_id, cinema_id=None):
        camera = Camera.query.get(camera_id) if camera_id else None
        if camera:
            return camera
        return self._get_or_create_upload_camera(preferred_cinema_id=cinema_id)

    @staticmethod
    def _pick_alarm_type_code(violation_codes):
        for code in ('photo', 'smoke', 'walk', 'crowd'):
            if code in (violation_codes or []):
                return code
        return 'photo'

    @staticmethod
    def _pick_alarm_level_code(recent_count, threshold):
        if recent_count >= threshold * 2:
            return 'critical'
        if recent_count >= threshold:
            return 'high'
        return 'medium'

    def _create_threshold_alarm(self, task_id, camera_id, cinema_id, latest_sample, recent_count, window_seconds, threshold):
        camera = self._resolve_camera(camera_id, cinema_id)
        violation_codes = latest_sample.get('violation_codes') or []
        llm_analysis = latest_sample.get('llm_analysis') or {}
        alarm_type_code = self._pick_alarm_type_code(violation_codes)
        alarm_type = AlarmType.query.filter_by(code=alarm_type_code).first()
        if not alarm_type:
            alarm_type = AlarmType.query.filter_by(code='photo').first()
        if not alarm_type:
            return None

        level_code = self._pick_alarm_level_code(recent_count, max(1, int(threshold or 1)))
        level = AlarmLevel.query.filter_by(code=level_code).first()
        if not level:
            level = AlarmLevel.query.filter_by(code='high').first()

        detections = latest_sample.get('detections') or []
        detection_box = ''
        confidence = 0.0
        if detections:
            detection_box = ','.join(map(str, detections[0].get('box') or []))
            confidence = max(float(d.get('confidence') or 0.0) for d in detections)

        location = ''
        if camera:
            cinema_name = camera.cinema.name if camera.cinema else ''
            hall_name = camera.hall.name if camera.hall else ''
            position = camera.position or ''
            location = f'{cinema_name} - {hall_name} - {position}'.strip(' -')

        llm_summary = llm_analysis.get('summary') or '未提供大模型结论'
        frame_index = latest_sample.get('frame_index')

        alarm = Alarm(
            alarm_type_id=alarm_type.id,
            camera_id=camera.id,
            level_id=level.id if level else 1,
            title=f'视频识别阈值告警 - {alarm_type.name}',
            description=(
                f'在{window_seconds}秒内累计检测到{recent_count}次违规。'
                f'最新命中帧：#{frame_index}。'
                f'大模型结论：{llm_summary}'
            ),
            location=location,
            image_url=latest_sample.get('image_url'),
            detection_box=detection_box,
            confidence=confidence,
            status=ALARM_STATUS_PENDING,
            occurred_at=datetime.now(),
        )
        db.session.add(alarm)
        db.session.commit()

        db.session.add(AlarmActionLog(
            alarm_id=alarm.id,
            user_id=None,
            action='created',
            from_status=None,
            to_status=ALARM_STATUS_PENDING,
            note=f'视频识别阈值触发自动告警 task_id={task_id}, recent_count={recent_count}, window={window_seconds}s'
        ))
        db.session.commit()

        emit_alarm(
            alarm.to_dict(),
            target_roles=['admin', 'operator', 'manager'],
            target_cinema_id=camera.cinema_id
        )
        return alarm.id


video_detection_manager = VideoDetectionTaskManager()
