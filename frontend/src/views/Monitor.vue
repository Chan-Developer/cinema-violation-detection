<template>
  <div class="monitor">
    <div class="monitor-toolbar">
      <el-select v-model="selectedCinema" placeholder="选择影院" clearable @change="loadCameras" style="width: 220px">
        <el-option v-for="c in cinemas" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
    </div>

    <div class="monitor-body">
      <!-- 摄像头列表 -->
      <div class="camera-panel">
        <div class="panel-head">
          <span>摄像头列表</span>
          <el-tag size="small" round>{{ cameras.length }} 台</el-tag>
        </div>
        <div class="camera-list">
          <div
            v-for="cam in cameras"
            :key="cam.id"
            class="camera-item"
            :class="{ active: selectedCamera?.id === cam.id }"
            @click="selectCamera(cam)"
          >
            <div class="cam-indicator" :class="cam.stream_status === 1 ? 'online' : 'offline'"></div>
            <div class="cam-info">
              <div class="cam-name">{{ cam.name }}</div>
              <div class="cam-meta">{{ cam.position || '未设置位置' }}</div>
            </div>
            <el-tag :type="cam.stream_status === 1 ? 'success' : 'info'" size="small" effect="plain" round>
              {{ cam.stream_status === 1 ? '推流中' : '离线' }}
            </el-tag>
          </div>
          <el-empty v-if="cameras.length === 0" description="暂无摄像头" :image-size="60" />
        </div>
      </div>

      <!-- 视频播放区 -->
      <div class="video-panel">
        <template v-if="!selectedCamera">
          <div class="empty-video">
            <el-icon :size="64" color="#ddd"><VideoCamera /></el-icon>
            <p>请从左侧选择一个摄像头</p>
          </div>
        </template>
        <template v-else>
          <div class="video-head">
            <div>
              <h3>{{ selectedCamera.name }}</h3>
              <span class="video-sub">{{ selectedCamera.position }} &middot; {{ selectedCamera.hall_name || '未分配影厅' }}</span>
            </div>
            <div class="video-actions">
              <el-button
                :type="selectedCamera.stream_status === 1 ? 'danger' : 'primary'"
                size="small"
                round
                @click="toggleStream"
              >
                <el-icon><VideoPlay v-if="selectedCamera.stream_status !== 1" /><VideoPause v-else /></el-icon>
                {{ selectedCamera.stream_status === 1 ? '停止推流' : '开始推流' }}
              </el-button>
              <el-button
                type="success"
                size="small"
                round
                @click="startDetection"
                :disabled="selectedCamera.stream_status !== 1"
              >
                <el-icon><View /></el-icon>
                开始检测
              </el-button>
            </div>
          </div>
          <div class="video-player">
            <img v-if="currentFrame" :src="currentFrame" alt="视频流" />
            <div v-else class="no-stream">
              <el-icon :size="80" color="rgba(255,255,255,0.2)"><VideoCamera /></el-icon>
              <p>视频流未启动</p>
            </div>
          </div>
          <!-- 检测结果 -->
          <div class="detection-list" v-if="detectionResults.length > 0">
            <el-alert
              v-for="(result, idx) in detectionResults"
              :key="idx"
              :title="getDetectionLabel(result.type)"
              :type="getDetectionAlertType(result.type)"
              :description="`置信度: ${(result.confidence * 100).toFixed(1)}%`"
              show-icon
              :closable="false"
            />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'
import { io } from 'socket.io-client'

const authStore = useAuthStore()

const cinemas = ref<any[]>([])
const cameras = ref<any[]>([])
const selectedCinema = ref<number | null>(null)
const selectedCamera = ref<any>(null)
const currentFrame = ref('')
const detectionResults = ref<any[]>([])

let socket: any = null
let frameTimer: number | null = null

const loadCinemas = async () => {
  try {
    const res = await authStore.api.get('/cinemas?per_page=100')
    if (res.data.success) {
      cinemas.value = res.data.cinemas
      if (cinemas.value.length > 0 && !selectedCinema.value) {
        selectedCinema.value = cinemas.value[0].id
        loadCameras()
      }
    }
  } catch (e) {
    console.error('获取影院失败', e)
  }
}

const loadCameras = async () => {
  if (!selectedCinema.value) { cameras.value = []; return }
  try {
    const res = await authStore.api.get(`/cameras?cinema_id=${selectedCinema.value}&per_page=100`)
    if (res.data.success) cameras.value = res.data.cameras
  } catch (e) {
    console.error('获取摄像头失败', e)
  }
}

const selectCamera = (cam: any) => {
  selectedCamera.value = cam
  detectionResults.value = []
  currentFrame.value = ''
  if (frameTimer) { clearInterval(frameTimer); frameTimer = null }
  if (cam.stream_status === 1) {
    fetchFrame()
    frameTimer = window.setInterval(fetchFrame, 1000)
  }
}

const fetchFrame = async () => {
  if (!selectedCamera.value) return
  try {
    const res = await authStore.api.get(`/streams/${selectedCamera.value.id}/frame`)
    if (res.data.success && res.data.frame) currentFrame.value = res.data.frame
  } catch (_e) { /* ignore */ }
}

const toggleStream = async () => {
  if (!selectedCamera.value) return
  const action = selectedCamera.value.stream_status === 1 ? 'stop' : 'start'
  try {
    const res = await authStore.api.post(`/streams/${selectedCamera.value.id}/${action}`)
    ElMessage.success(res.data.message)
    loadCameras()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '操作失败')
  }
}

const startDetection = () => { ElMessage.info('检测功能已启动') }

const getDetectionLabel = (type: string) =>
  ({ photo: '盗摄检测', smoke: '吸烟检测', crowd: '拥堵检测', walk: '随意走动' } as Record<string, string>)[type] || type

const getDetectionAlertType = (type: string) =>
  ({ photo: 'warning', smoke: 'error', crowd: 'warning', walk: 'info' } as Record<string, string>)[type] || 'info'

const initSocket = () => {
  socket = io('http://localhost:9500', { transports: ['websocket'] })
  socket.on('connect', () => {
    const user = authStore.user
    if (user) {
      socket.emit('authenticate', {
        user_id: user.id, username: user.username,
        role: user.role, cinema_id: user.cinema_id
      })
    }
  })
  socket.on('detection_result', (data: any) => {
    if (selectedCamera.value && data.camera_id === selectedCamera.value.id) {
      detectionResults.value = data.result?.results || []
    }
  })
  socket.on('new_alarm', (data: any) => {
    ElMessage.warning(`新报警: ${data.title}`)
    authStore.fetchPendingAlarms()
  })
}

onMounted(() => { loadCinemas(); initSocket() })
onUnmounted(() => {
  if (frameTimer) clearInterval(frameTimer)
  if (socket) socket.disconnect()
})
</script>

<style scoped>
.monitor {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: calc(100vh - 64px - 48px);
}

.monitor-toolbar {
  display: flex;
  align-items: center;
}

.monitor-body {
  flex: 1;
  display: flex;
  gap: 20px;
  min-height: 0;
}

/* Camera Panel */
.camera-panel {
  width: 300px;
  min-width: 300px;
  background: #fff;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 18px;
  border-bottom: 1px solid #f0f0f0;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}
.camera-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.camera-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.camera-item:hover { background: #f7f8fa; }
.camera-item.active {
  background: linear-gradient(135deg, rgba(102,126,234,0.08), rgba(118,75,162,0.06));
  box-shadow: inset 3px 0 0 #667eea;
}

.cam-indicator {
  width: 8px; height: 8px; min-width: 8px;
  border-radius: 50%;
}
.cam-indicator.online { background: #52c41a; box-shadow: 0 0 6px rgba(82, 196, 26, 0.4); }
.cam-indicator.offline { background: #d9d9d9; }

.cam-info { flex: 1; min-width: 0; }
.cam-name { font-size: 13px; font-weight: 500; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cam-meta { font-size: 11px; color: #bbb; margin-top: 2px; }

/* Video Panel */
.video-panel {
  flex: 1;
  background: #fff;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}
.empty-video {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #ccc;
}
.empty-video p { font-size: 14px; }

.video-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}
.video-head h3 { font-size: 15px; font-weight: 600; color: #333; margin: 0; }
.video-sub { font-size: 12px; color: #bbb; }
.video-actions { display: flex; gap: 8px; }

.video-player {
  flex: 1;
  background: #111;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}
.video-player img { max-width: 100%; max-height: 100%; object-fit: contain; }
.no-stream { text-align: center; color: rgba(255, 255, 255, 0.3); }
.no-stream p { margin-top: 8px; font-size: 14px; }

.detection-list {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-top: 1px solid #f0f0f0;
}
</style>
