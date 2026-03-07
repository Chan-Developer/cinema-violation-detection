import cv2
import numpy as np
import threading
import time
import random
import os
from datetime import datetime
from services.websocket import socketio, emit_detection_result, emit_alarm
from services.video_stream import stream_manager
from models import db, Camera, Alarm, AlarmType, AlarmLevel

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
    
    def __init__(self, camera_id, detection_types):
        super().__init__(daemon=True)
        self.camera_id = camera_id
        self.detection_types = detection_types.split(',') if detection_types else []
        self.running = False
        self._running = threading.Event()
        
        self.detection_count = 0
        self.last_detection_time = {}
        
        # 模拟检测配置
        self.detection_interval = 2.0  # 检测间隔(秒)
        self.confidence_threshold = 0.5
        
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
        """执行检测 - 模拟实现"""
        # 模拟随机检测结果
        # 实际项目中可以接入YOLO/ONNX模型
        
        results = []
        current_time = time.time()
        
        for det_type in self.detection_types:
            det_type = det_type.strip()
            if not det_type:
                continue
            
            # 检查检测间隔
            last_time = self.last_detection_time.get(det_type, 0)
            if current_time - last_time < 10:  # 同一类型10秒内不重复报警
                continue
            
            # 模拟检测概率 (10%概率触发)
            if random.random() < 0.1:
                # 生成检测框
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
