import cv2
import threading
import time
import queue
import numpy as np
from datetime import datetime
from services.websocket import socketio, emit_stream_status
from models import db, Camera, VideoStream

class VideoStreamManager:
    """视频流管理器"""
    
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
            self.streams = {}  # camera_id -> StreamWorker
            self.frame_queues = {}  # camera_id -> queue
            self.initialized = True
    
    def start_stream(self, camera_id):
        """启动视频流"""
        with self._lock:
            if camera_id in self.streams:
                return {'success': False, 'message': '流已在运行'}
            
            camera = Camera.query.get(camera_id)
            if not camera:
                return {'success': False, 'message': '摄像头不存在'}
            
            if not camera.rtsp_url:
                return {'success': False, 'message': '未配置RTSP地址'}
            
            # 创建帧队列
            frame_queue = queue.Queue(maxsize=10)
            self.frame_queues[camera_id] = frame_queue
            
            # 创建并启动工作线程
            worker = StreamWorker(camera_id, camera.rtsp_url, camera.username, camera.password, frame_queue)
            self.streams[camera_id] = worker
            worker.start()
            
            # 更新数据库状态
            stream = VideoStream.query.filter_by(camera_id=camera_id).first()
            if not stream:
                stream = VideoStream(camera_id=camera_id, stream_url=camera.rtsp_url)
                db.session.add(stream)
            stream.status = 1
            stream.started_at = datetime.now()
            db.session.commit()
            
            camera.stream_status = 1
            camera.status = 1  # 在线
            db.session.commit()
            
            emit_stream_status(camera_id, 1)
            
            return {'success': True, 'message': '视频流已启动'}
    
    def stop_stream(self, camera_id):
        """停止视频流"""
        with self._lock:
            if camera_id not in self.streams:
                return {'success': False, 'message': '流未运行'}
            
            worker = self.streams[camera_id]
            worker.stop()
            del self.streams[camera_id]
            
            if camera_id in self.frame_queues:
                del self.frame_queues[camera_id]
            
            # 更新数据库状态
            camera = Camera.query.get(camera_id)
            if camera:
                camera.stream_status = 0
                db.session.commit()
            
            stream = VideoStream.query.filter_by(camera_id=camera_id).first()
            if stream:
                stream.status = 0
                stream.stopped_at = datetime.now()
                db.session.commit()
            
            emit_stream_status(camera_id, 0)
            
            return {'success': True, 'message': '视频流已停止'}
    
    def get_frame(self, camera_id):
        """获取最新帧"""
        if camera_id in self.frame_queues:
            try:
                return self.frame_queues[camera_id].get_nowait()
            except queue.Empty:
                return None
        return None
    
    def get_stream_status(self, camera_id):
        """获取流状态"""
        if camera_id in self.streams:
            worker = self.streams[camera_id]
            return {
                'running': worker.is_running(),
                'fps': worker.get_fps(),
                'frame_count': worker.frame_count
            }
        return {'running': False, 'fps': 0, 'frame_count': 0}
    
    def stop_all(self):
        """停止所有流"""
        with self._lock:
            for camera_id in list(self.streams.keys()):
                self.stop_stream(camera_id)


class StreamWorker(threading.Thread):
    """视频流工作线程"""
    
    def __init__(self, camera_id, rtsp_url, username, password, frame_queue):
        super().__init__(daemon=True)
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.username = username
        self.password = password
        self.frame_queue = frame_queue
        self.running = False
        self._running = threading.Event()
        
        self.frame_count = 0
        self.fps = 0
        self._fps_start_time = time.time()
        self._fps_frame_count = 0
        
        self.cap = None
        
    def run(self):
        self.running = True
        self._running.set()
        self._connect()
    
    def _connect(self):
        """连接视频流"""
        # 构建认证URL
        url = self.rtsp_url
        if self.username and self.password:
            # 简单处理: 替换rtsp://为rtsp://username:password@
            if url.startswith('rtsp://'):
                parts = url.replace('rtsp://', '').split('@')
                if len(parts) > 1:
                    url = f"rtsp://{self.username}:{self.password}@{parts[1]}"
                else:
                    url = f"rtsp://{self.username}:{self.password}@{url.replace('rtsp://', '')}"
        
        self.cap = cv2.VideoCapture(url)
        
        if not self.cap.isOpened():
            print(f"无法打开视频流: {url}")
            socketio.emit('stream_error', {
                'camera_id': self.camera_id,
                'message': '无法连接视频流'
            })
            return
        
        print(f"视频流连接成功: camera_id={self.camera_id}")
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print(f"读取帧失败: camera_id={self.camera_id}")
                time.sleep(1)
                continue
            
            self.frame_count += 1
            self._fps_frame_count += 1
            
            # 计算FPS
            elapsed = time.time() - self._fps_start_time
            if elapsed > 1.0:
                self.fps = self._fps_frame_count / elapsed
                self._fps_start_time = time.time()
                self._fps_frame_count = 0
            
            # 放入队列
            try:
                if not self.frame_queue.full():
                    # 转换为JPEG
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_data = buffer.tobytes()
                    self.frame_queue.put({
                        'frame': frame,
                        'frame_data': frame_data,
                        'timestamp': time.time(),
                        'frame_id': self.frame_count
                    })
            except Exception as e:
                print(f"帧处理错误: {e}")
            
            # 控制帧率
            time.sleep(0.03)  # ~30fps
        
        if self.cap:
            self.cap.release()
    
    def stop(self):
        """停止"""
        self.running = False
        self._running.clear()
    
    def is_running(self):
        return self.running and self._running.is_set()
    
    def get_fps(self):
        return round(self.fps, 2)


# 全局实例
stream_manager = VideoStreamManager()
