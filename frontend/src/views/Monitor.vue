<template>
  <div class="video-monitor">
    <el-card class="upload-card">
      <template #header>
        <div class="header-row">
          <span class="title">视频识别监控（上传视频代替摄像头）</span>
          <el-tag type="danger" effect="light" round>
            待处理告警 {{ authStore.pendingAlarmCount }}
          </el-tag>
        </div>
      </template>

      <div class="toolbar">
        <el-form inline>
          <el-form-item label="采样间隔">
            <el-input-number v-model="frameInterval" :min="1" :max="300" :step="1" />
            <span class="hint">每 {{ frameInterval }} 帧检测一次</span>
          </el-form-item>
          <el-form-item label="检测类型">
            <el-checkbox-group v-model="detectionTypes">
              <el-checkbox label="photo">盗摄</el-checkbox>
              <el-checkbox label="smoke">吸烟</el-checkbox>
              <el-checkbox label="crowd">拥堵</el-checkbox>
              <el-checkbox label="walk">走动</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </el-form>
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
          <div class="el-upload__tip">视频上传后会自动检测并产生日志与告警</div>
        </template>
      </el-upload>
    </el-card>

    <el-card>
      <template #header>
        <div class="header-row">
          <span class="title">检测任务</span>
          <el-button type="primary" text @click="$router.push('/alarms')">查看告警列表</el-button>
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
            <span>告警数: {{ task.alarms_created || 0 }}</span>
          </div>

          <div v-if="task.summary" class="summary">{{ task.summary }}</div>
          <div v-if="task.message && task.status === 'failed'" class="error">{{ task.message }}</div>

          <div v-if="task.samples && task.samples.length > 0" class="samples">
            <a
              v-for="(sample, index) in task.samples.slice(0, 10)"
              :key="index"
              :href="normalizeMediaUrl(sample.image_url)"
              target="_blank"
              rel="noopener noreferrer"
              class="sample-link"
            >
              帧 {{ sample.frame_index }}
            </a>
          </div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const frameInterval = ref(90)
const detectionTypes = ref(['photo', 'smoke', 'crowd', 'walk'])
const tasks = ref<any[]>([])
const pollTimers = new Map<string, number>()

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

const uploadVideo = async (options: any) => {
  const formData = new FormData()
  formData.append('file', options.file)
  formData.append('frame_interval', String(frameInterval.value || 90))
  formData.append('detection_types', detectionTypes.value.join(','))

  try {
    const res = await authStore.api.post('/detect/video', formData, {
      timeout: 180000,
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (!res.data.success) throw new Error(res.data.message || '任务创建失败')

    const task = {
      task_id: res.data.task_id,
      file_name: options.file?.name,
      status: 'pending',
      progress: 0,
      processed_frames: 0,
      sampled_frames: 0,
      alarms_created: 0,
      samples: []
    }

    tasks.value.unshift(task)
    startPolling(task.task_id)
    ElMessage.success('视频任务已创建，开始检测')
    options.onSuccess?.(res.data)
  } catch (e: any) {
    options.onError?.(e)
    ElMessage.error(e?.response?.data?.message || e?.message || '上传失败')
  }
}

const updateTask = (taskId: string, taskData: any) => {
  const idx = tasks.value.findIndex(t => t.task_id === taskId)
  if (idx < 0) return
  tasks.value[idx] = {
    ...tasks.value[idx],
    ...taskData
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
        clearPolling(taskId)
        authStore.fetchPendingAlarms()
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

onMounted(() => {
  authStore.fetchPendingAlarms()
})

onUnmounted(() => {
  pollTimers.forEach((timer) => clearInterval(timer))
  pollTimers.clear()
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
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
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
