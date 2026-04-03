<template>
  <div class="video-monitor">
    <el-card class="upload-card">
      <template #header>
        <div class="header-row">
          <span class="title">视频识别监控（上传视频 / 本地摄像头）</span>
          <el-tag type="success" effect="light" round>
            识别结果自动存档
          </el-tag>
        </div>
      </template>

      <div class="toolbar">
        <el-form inline>
          <el-form-item label="采样间隔">
            <el-input-number v-model="frameInterval" :min="1" :max="300" :step="1" />
            <span class="hint">每 {{ frameInterval }} 帧检测一次</span>
          </el-form-item>
        </el-form>
        <div class="hint">当前逻辑：YOLO仅检测“人”，违规行为由大模型结合画面判定。</div>
      </div>

      <el-upload
        drag
        :http-request="uploadVideo"
        :before-upload="beforeUpload"
        accept=".mp4,.avi,.mov,.mkv,.webm"
        :show-file-list="false"
        class="upload-area"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">点击或拖拽上传视频进行识别</div>
        <template #tip>
          <div class="el-upload__tip">视频上传后会按采样帧识别并保存结果</div>
        </template>
      </el-upload>

      <el-divider />

      <div class="webcam-section">
        <div class="webcam-header">
          <div class="title">本地摄像头</div>
          <el-tag :type="isRecording ? 'danger' : webcamStream ? 'success' : 'info'" round>
            {{ isRecording ? '录制中' : webcamStream ? '已连接' : '未连接' }}
          </el-tag>
        </div>

        <div class="webcam-preview-wrap">
          <video ref="webcamVideoRef" class="webcam-preview" autoplay playsinline muted />
          <div v-if="!webcamStream" class="webcam-placeholder">点击“打开摄像头”开始预览</div>
        </div>

        <div class="webcam-actions">
          <el-button type="primary" @click="openWebcam" :disabled="webcamOpening || !!webcamStream">
            打开摄像头
          </el-button>
          <el-button @click="closeWebcam" :disabled="!webcamStream || isRecording">
            关闭摄像头
          </el-button>
          <el-button type="warning" @click="startRecording" :disabled="!webcamStream || isRecording">
            开始录制并上传
          </el-button>
          <el-button type="danger" @click="stopRecording" :disabled="!isRecording">
            停止录制并上传
          </el-button>
          <span class="hint" v-if="isRecording">已录制 {{ recordingSeconds }} 秒</span>
        </div>
      </div>
    </el-card>

    <el-card>
      <template #header>
        <div class="header-row">
          <span class="title">识别任务</span>
        </div>
      </template>

      <el-empty v-if="tasks.length === 0" description="暂无任务，先上传一个视频吧" />

      <div v-else class="task-list">
        <el-card v-for="task in tasks" :key="task.task_id" class="task-item" shadow="never">
          <div class="task-head">
            <div>
              <div class="task-name">{{ task.file_name || task.task_id }}</div>
              <div class="task-meta">任务ID: {{ task.task_id }}</div>
            </div>
            <el-tag :type="statusTag(task.status)" round>{{ statusText(task.status) }}</el-tag>
          </div>

          <el-progress
            :percentage="task.progress || 0"
            :status="task.status === 'failed' ? 'exception' : task.status === 'completed' ? 'success' : ''"
          />

          <div class="task-stats">
            <span>已处理帧: {{ task.processed_frames || 0 }}</span>
            <span>采样帧: {{ task.sampled_frames || 0 }}</span>
            <span>结果数: {{ task.records_saved || 0 }}</span>
            <span>违规帧: {{ task.violation_frames || 0 }}</span>
          </div>

          <div v-if="task.summary" class="summary">{{ task.summary }}</div>
          <div v-if="task.message && task.status === 'failed'" class="error">{{ task.message }}</div>

          <div v-if="task.samples && task.samples.length > 0" class="samples">
            <div
              v-for="(sample, index) in task.samples.slice(-10).reverse()"
              :key="index"
              class="sample-card"
            >
              <div class="sample-head">
                <a
                  :href="normalizeMediaUrl(sample.image_url)"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="sample-link"
                >
                  帧 {{ sample.frame_index }}
                </a>
                <el-tag :type="sample.violation ? 'danger' : 'success'" size="small" round>
                  {{ sample.violation ? '有违规' : '无违规' }}
                </el-tag>
              </div>
              <div class="sample-meta">
                <span v-if="sample.violation_codes && sample.violation_codes.length > 0">
                  违规类型: {{ sample.violation_codes.join(', ') }}
                </span>
                <span v-else>
                  违规类型: 无
                </span>
              </div>
              <div class="sample-summary">
                {{ sample.llm_analysis?.summary || '无大模型结论' }}
              </div>
              <el-collapse class="sample-collapse">
                <el-collapse-item title="查看大模型原文">
                  <pre class="llm-raw">{{ sample.llm_analysis?.raw_reply || '（无）' }}</pre>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const frameInterval = ref(90)
const tasks = ref<any[]>([])
const pollTimers = new Map<string, number>()
const webcamVideoRef = ref<HTMLVideoElement | null>(null)
const webcamStream = ref<MediaStream | null>(null)
const webcamOpening = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordingChunks = ref<Blob[]>([])
const isRecording = ref(false)
const recordingSeconds = ref(0)
let recordingTimer: number | null = null

const apiOrigin = (import.meta.env.VITE_API_BASE || 'http://localhost:9500/api').replace(/\/api\/?$/, '')

const normalizeMediaUrl = (url: string) => {
  if (!url) return url
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) return url
  return `${apiOrigin}${url}`
}

const beforeUpload = (file: any) => {
  const allowed = [
    'video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/webm', 'video/x-matroska'
  ]
  if (!allowed.includes(file.type)) {
    ElMessage.error('仅支持 MP4/AVI/MOV/MKV/WEBM 视频')
    return false
  }

  const isLt200M = file.size / 1024 / 1024 < 200
  if (!isLt200M) {
    ElMessage.error('文件大小不能超过200MB')
    return false
  }
  return true
}

const createTaskFromFile = async (file: File, sourceLabel = '上传视频') => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('frame_interval', String(frameInterval.value || 90))

  const res = await authStore.api.post('/detect/video', formData, {
    timeout: 180000,
    headers: { 'Content-Type': 'multipart/form-data' }
  })

  if (!res.data.success) throw new Error(res.data.message || '任务创建失败')

  const task = {
    task_id: res.data.task_id,
    file_name: file?.name || sourceLabel,
    source: sourceLabel,
    status: 'pending',
    progress: 0,
    processed_frames: 0,
    sampled_frames: 0,
    records_saved: 0,
    violation_frames: 0,
    samples: []
  }

  tasks.value.unshift(task)
  startPolling(task.task_id)
  ElMessage.success(`${sourceLabel}任务已创建，开始检测`)
  return res.data
}

const uploadVideo = async (options: any) => {
  try {
    const file = options.file as File
    const data = await createTaskFromFile(file, '上传视频')
    options.onSuccess?.(data)
  } catch (e: any) {
    options.onError?.(e)
    ElMessage.error(e?.response?.data?.message || e?.message || '上传失败')
  }
}

const openWebcam = async () => {
  if (!navigator.mediaDevices?.getUserMedia) {
    ElMessage.error('当前浏览器不支持摄像头访问')
    return
  }
  webcamOpening.value = true
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    webcamStream.value = stream
    if (webcamVideoRef.value) {
      webcamVideoRef.value.srcObject = stream
      await webcamVideoRef.value.play().catch(() => {})
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '无法打开摄像头，请检查浏览器权限')
  } finally {
    webcamOpening.value = false
  }
}

const closeWebcam = (force = false) => {
  if (isRecording.value && !force) return
  webcamStream.value?.getTracks().forEach(track => track.stop())
  webcamStream.value = null
  if (webcamVideoRef.value) {
    webcamVideoRef.value.srcObject = null
  }
}

const stopRecordingTimer = () => {
  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }
}

const startRecording = () => {
  if (!webcamStream.value) return
  if (typeof MediaRecorder === 'undefined') {
    ElMessage.error('当前浏览器不支持本地录制')
    return
  }
  const candidates = ['video/webm;codecs=vp9', 'video/webm;codecs=vp8', 'video/webm']
  const mimeType = candidates.find(type => MediaRecorder.isTypeSupported(type)) || ''
  recordingChunks.value = []

  const recorder = mimeType
    ? new MediaRecorder(webcamStream.value, { mimeType })
    : new MediaRecorder(webcamStream.value)
  mediaRecorder.value = recorder

  recorder.ondataavailable = (event: BlobEvent) => {
    if (event.data && event.data.size > 0) {
      recordingChunks.value.push(event.data)
    }
  }

  recorder.onstop = async () => {
    isRecording.value = false
    stopRecordingTimer()

    const blob = new Blob(recordingChunks.value, { type: recorder.mimeType || 'video/webm' })
    recordingChunks.value = []

    if (!blob.size) {
      ElMessage.error('未录制到有效视频，请重试')
      return
    }

    const file = new File([blob], `webcam-${Date.now()}.webm`, { type: blob.type || 'video/webm' })
    try {
      await createTaskFromFile(file, '本地摄像头')
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.message || e?.message || '摄像头视频上传失败')
    }
  }

  recorder.start(500)
  isRecording.value = true
  recordingSeconds.value = 0
  recordingTimer = window.setInterval(() => {
    recordingSeconds.value += 1
  }, 1000)
}

const stopRecording = () => {
  if (!mediaRecorder.value || !isRecording.value) return
  mediaRecorder.value.stop()
}

const updateTask = (taskId: string, taskData: any) => {
  const idx = tasks.value.findIndex(t => t.task_id === taskId)
  if (idx < 0) return
  tasks.value[idx] = {
    ...tasks.value[idx],
    ...taskData
  }
}

const fetchTaskResults = async (taskId: string) => {
  try {
    const res = await authStore.api.get(`/detect/video/tasks/${taskId}/results`)
    if (!res.data.success) return []
    return (res.data.results || []).map((item: any) => ({
      frame_index: item.frame_index,
      image_url: normalizeMediaUrl(item.image_url),
      person_count: item.person_count,
      violation: item.violation,
      violation_codes: item.violation_codes || [],
      llm_analysis: {
        summary: item.llm_summary || '',
        raw_reply: item.llm_reply || '',
        violation: item.violation,
        violation_codes: item.violation_codes || [],
        llm_skipped: (item.person_count || 0) === 0
      }
    }))
  } catch (_e) {
    return []
  }
}

const startPolling = (taskId: string) => {
  const timer = window.setInterval(async () => {
    try {
      const res = await authStore.api.get(`/detect/video/tasks/${taskId}`)
      if (!res.data.success) return

      const task = res.data.task
      updateTask(taskId, task)

      if (task.status === 'completed' || task.status === 'failed') {
        if (task.status === 'completed') {
          const persisted = await fetchTaskResults(taskId)
          if (persisted.length > 0) {
            updateTask(taskId, { samples: persisted })
          }
        }
        clearPolling(taskId)
      }
    } catch (_e) {
      // 网络抖动忽略单次错误
    }
  }, 1500)

  pollTimers.set(taskId, timer)
}

const clearPolling = (taskId: string) => {
  const timer = pollTimers.get(taskId)
  if (timer) {
    clearInterval(timer)
    pollTimers.delete(taskId)
  }
}

const statusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '排队中',
    running: '识别中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const statusTag = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

onUnmounted(() => {
  pollTimers.forEach((timer) => clearInterval(timer))
  pollTimers.clear()
  stopRecordingTimer()
  if (isRecording.value && mediaRecorder.value) {
    mediaRecorder.value.stop()
  }
  closeWebcam(true)
})
</script>

<style scoped>
.video-monitor {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  font-weight: 600;
  color: #333;
}

.toolbar {
  margin-bottom: 12px;
}

.hint {
  margin-left: 8px;
  color: #999;
  font-size: 12px;
}

.webcam-section {
  margin-top: 8px;
}

.webcam-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.webcam-preview-wrap {
  position: relative;
  min-height: 220px;
  border: 1px dashed #d9d9d9;
  border-radius: 10px;
  overflow: hidden;
  background: #0f172a;
}

.webcam-preview {
  width: 100%;
  display: block;
  max-height: 360px;
  object-fit: contain;
}

.webcam-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 14px;
}

.webcam-actions {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  border: 1px solid #f0f0f0;
}

.task-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.task-name {
  font-weight: 600;
  color: #222;
}

.task-meta {
  font-size: 12px;
  color: #999;
}

.task-stats {
  margin-top: 10px;
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #666;
}

.summary {
  margin-top: 8px;
  font-size: 13px;
  color: #333;
}

.error {
  margin-top: 8px;
  font-size: 13px;
  color: #f56c6c;
}

.samples {
  margin-top: 10px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 10px;
}

.sample-card {
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 10px;
  background: #fff;
}

.sample-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.sample-meta {
  margin-top: 6px;
  font-size: 12px;
  color: #666;
}

.sample-summary {
  margin-top: 6px;
  font-size: 13px;
  color: #333;
  line-height: 1.5;
}

.sample-collapse {
  margin-top: 6px;
}

.llm-raw {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
  color: #333;
  margin: 0;
  padding: 8px;
  background: #fafafa;
  border-radius: 6px;
}

.sample-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  text-decoration: none;
  color: #7c3aed;
  background: rgba(124, 58, 237, 0.08);
}
</style>
