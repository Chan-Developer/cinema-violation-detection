import cv2
import numpy as np
import threading
import time
import os
from datetime import datetime
from services.websocket import socketio, emit_detection_result, emit_alarm
from services.video_stream import stream_manager
from models import db, Camera, Alarm, AlarmType, AlarmLevel

# YOLO 导入
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️  Warning: ultralytics 未安装，将使用模拟检测模式")

class DetectionService:
    """行为检测服务"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.detectors = {}  # camera_id -> DetectionWorker
            self.initialized = True
    
    def start_detection(self, camera_id):
        """启动检测"""
        with self._lock:
            if camera_id in self.detectors:
                return {'success': False, 'message': '检测已在运行'}
            
            camera = Camera.query.get(camera_id)
            if not camera:
                return {'success': False, 'message': '摄像头不存在'}
            
            if not camera.detection_enabled:
                return {'success': False, 'message': '检测未启用'}
            
            # 创建检测工作线程
            worker = DetectionWorker(camera_id, camera.detection_types)
            self.detectors[camera_id] = worker
            worker.start()
            
            return {'success': True, 'message': '检测已启动'}
    
    def stop_detection(self, camera_id):
        """停止检测"""
        with self._lock:
            if camera_id not in self.detectors:
                return {'success': False, 'message': '检测未运行'}
            
            worker = self.detectors[camera_id]
            worker.stop()
            del self.detectors[camera_id]
            
            return {'success': True, 'message': '检测已停止'}
    
    def stop_all(self):
        """停止所有检测"""
        with self._lock:
            for camera_id in list(self.detectors.keys()):
                self.stop_detection(camera_id)
    
    def get_status(self, camera_id):
        """获取检测状态"""
        if camera_id in self.detectors:
            worker = self.detectors[camera_id]
            return {
                'running': worker.is_running(),
                'detection_count': worker.detection_count
            }
        return {'running': False, 'detection_count': 0}


class DetectionWorker(threading.Thread):
    """检测工作线程"""

    # 类级别的模型缓存（避免重复加载）
    _model = None
    _model_lock = threading.Lock()

    # YOLO 类别到检测类型的映射
    DETECTION_MAPPING = {
        'person': 'person',        # 人
        'smoke': 'smoke',          # 烟雾
        'crowd': 'crowd',          # 拥挤
        'phone': 'phone',          # 手机
    }

    def __init__(self, camera_id, detection_types):
        super().__init__(daemon=True)
        self.camera_id = camera_id
        self.detection_types = detection_types.split(',') if detection_types else []
        self.running = False
        self._running = threading.Event()

        self.detection_count = 0
        self.last_detection_time = {}

        # YOLO 检测配置
        self.detection_interval = 0.5  # 检测间隔(秒) - YOLO 会自动调节
        self.confidence_threshold = 0.5
        self.use_yolo = YOLO_AVAILABLE

        # 加载 YOLO 模型 (仅加载一次)
        if self.use_yolo:
            self._load_model()

    @classmethod
    def _load_model(cls):
        """加载 YOLO 模型 (单例模式)"""
        if cls._model is not None:
            return

        with cls._model_lock:
            if cls._model is not None:
                return

            try:
                model_path = 'yolov8x.pt'
                if os.path.exists(model_path):
                    print(f"正在加载 YOLO 模型: {model_path}")
                    cls._model = YOLO(model_path)
                    cls._model.to('cpu')  # 使用 CPU (如果有 GPU 改为 'cuda')
                    print(f"✓ YOLO 模型加载成功")
                else:
                    print(f"❌ YOLO 权重文件不存在: {model_path}")
                    cls._model = None
            except Exception as e:
                print(f"❌ 加载 YOLO 模型失败: {e}")
                cls._model = None
        
    def run(self):
        self.running = True
        self._running.set()
        
        print(f"检测服务启动: camera_id={self.camera_id}, types={self.detection_types}")
        
        while self.running:
            frame_data = stream_manager.get_frame(self.camera_id)
            
            if frame_data is not None:
                frame = frame_data['frame']
                
                # 执行检测
                results = self._detect(frame)
                
                if results:
                    self._handle_detection_results(results, frame)
                    self.detection_count += len(results)
                
                # 推送检测结果
                emit_detection_result(self.camera_id, {
                    'results': results,
                    'frame_id': frame_data['frame_id']
                })
            
            time.sleep(self.detection_interval)
    
    def _detect(self, frame):
        """执行检测 - 使用 YOLO 实时检测"""
        results = []

        if not self.use_yolo or self._model is None:
            # 降级到模拟检测
            return self._detect_simulated(frame)

        try:
            # 运行 YOLO 检测
            yolo_results = self._model(frame, conf=self.confidence_threshold, verbose=False)

            if yolo_results and len(yolo_results) > 0:
                boxes = yolo_results[0].boxes
                names = yolo_results[0].names

                for box in boxes:
                    # 提取检测信息
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = names[class_id].lower()

                    # 映射到检测类型
                    det_type = self.DETECTION_MAPPING.get(class_name)

                    # 如果没有在映射中，使用类别名称
                    if det_type is None:
                        det_type = class_name

                    # 检查是否在检测类型列表中
                    if det_type not in self.detection_types:
                        # 允许部分匹配 (例如 'person' 匹配 'photo')
                        if not any(det_type in dt for dt in self.detection_types):
                            continue

                    # 检查重复报警间隔
                    current_time = time.time()
                    last_time = self.last_detection_time.get(det_type, 0)
                    if current_time - last_time < 10:  # 10秒内同类型不重复报警
                        continue

                    result = {
                        'type': det_type,
                        'box': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': round(confidence, 2)
                    }
                    results.append(result)
                    self.last_detection_time[det_type] = current_time

        except Exception as e:
            print(f"YOLO 检测错误: {e}")
            return []

        return results

    def _detect_simulated(self, frame):
        """模拟检测 (当 YOLO 不可用时)"""
        import random
        results = []
        current_time = time.time()

        for det_type in self.detection_types:
            det_type = det_type.strip()
            if not det_type:
                continue

            # 检查检测间隔
            last_time = self.last_detection_time.get(det_type, 0)
            if current_time - last_time < 10:
                continue

            # 模拟检测概率
            if random.random() < 0.05:
                h, w = frame.shape[:2]
                x1 = random.randint(0, int(w * 0.7))
                y1 = random.randint(0, int(h * 0.7))
                x2 = random.randint(x1 + 50, w)
                y2 = random.randint(y1 + 50, h)

                confidence = random.uniform(0.5, 0.95)

                result = {
                    'type': det_type,
                    'box': [x1, y1, x2, y2],
                    'confidence': round(confidence, 2)
                }
                results.append(result)
                self.last_detection_time[det_type] = current_time

        return results
    
    def _handle_detection_results(self, results, frame):
        """处理检测结果"""
        camera = Camera.query.get(self.camera_id)
        if not camera:
            return
        
        for result in results:
            # 创建报警记录
            alarm_type = AlarmType.query.filter_by(code=result['type']).first()
            if not alarm_type:
                continue
            
            # 根据置信度确定报警级别
            confidence = result['confidence']
            if confidence >= 0.8:
                level = AlarmLevel.query.filter_by(code='critical').first()
            elif confidence >= 0.7:
                level = AlarmLevel.query.filter_by(code='high').first()
            elif confidence >= 0.6:
                level = AlarmLevel.query.filter_by(code='medium').first()
            else:
                level = AlarmLevel.query.filter_by(code='low').first()
            
            # 生成报警图片
            image_url = self._save_detection_image(frame, result)
            
            # 创建报警
            alarm = Alarm(
                alarm_type_id=alarm_type.id,
                camera_id=self.camera_id,
                level_id=level.id if level else 1,
                title=f'{alarm_type.name} - {camera.name}',
                description=f'在{camera.position or "监控区域"}检测到{alarm_type.name}行为，置信度: {confidence:.2%}',
                location=f'{camera.cinema.name if camera.cinema else ""} - {camera.hall.name if camera.hall else ""} - {camera.position or ""}',
                image_url=image_url,
                detection_box=','.join(map(str, result['box'])),
                confidence=confidence,
                occurred_at=datetime.now()
            )
            db.session.add(alarm)
            db.session.commit()
            
            # 推送报警
            emit_alarm(alarm.to_dict(), target_roles=['admin', 'operator'], target_cinema_id=camera.cinema_id)
    
    def _save_detection_image(self, frame, result):
        """保存检测图片"""
        try:
            # 绘制检测框
            x1, y1, x2, y2 = result['box']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # 添加标签
            label = f"{result['type']}: {result['confidence']:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # 保存图片
            alarm_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'alarms')
            os.makedirs(alarm_dir, exist_ok=True)
            
            filename = f"{self.camera_id}_{int(time.time() * 1000)}.jpg"
            filepath = os.path.join(alarm_dir, filename)
            cv2.imwrite(filepath, frame)
            
            return f"/static/alarms/{filename}"
        except Exception as e:
            print(f"保存检测图片失败: {e}")
            return None
    
    def stop(self):
        """停止"""
        self.running = False
        self._running.clear()
    
    def is_running(self):
        return self.running and self._running.is_set()


# 全局实例
detection_service = DetectionService()
