<template>
  <div class="detection-page">
    <!-- 上传区域 -->
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span class="title">📸 智能检测系统</span>
          <el-tag>YOLO + LLM</el-tag>
        </div>
      </template>

      <el-upload
        drag
        :http-request="uploadRequest"
        :on-success="onUploadSuccess"
        :on-error="onUploadError"
        :before-upload="beforeUpload"
        accept=".jpg,.jpeg,.png,.gif,.mp4,.avi,.mov,.webm"
        multiple
        class="upload-area"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">拖拽或点击上传</div>
        <template #tip>
          <div class="el-upload__tip">支持JPG/PNG/GIF图片 和 MP4/WebM视频（最大200MB）</div>
        </template>
      </el-upload>
    </el-card>

    <!-- 检测结果 -->
    <div v-if="results.length > 0" class="results-section">
      <div class="section-header">
        <h3>🎯 检测结果</h3>
        <el-button type="primary" link @click="clearResults">清空历史</el-button>
      </div>

      <div class="results-grid">
        <el-card v-for="(result, index) in results" :key="index" class="result-card">
          <!-- 进度条 -->
          <el-progress
            v-if="result.processing"
            :percentage="result.progress || 0"
            :status="result.progress === 100 ? 'success' : 'exception'"
            class="processing-bar"
          />

          <!-- 标注图片 -->
          <div v-if="result.annotated_image" class="image-box">
            <img :src="result.annotated_image" :alt="`检测 ${index}`" class="detection-image" />
            <div class="image-info">
              <span>{{ new Date(result.timestamp).toLocaleTimeString('zh-CN') }}</span>
            </div>
          </div>

          <!-- YOLO检测结果 -->
          <div v-if="result.detections && result.detections.length > 0" class="yolo-section">
            <div class="section-title">
              <el-icon><Setting /></el-icon> YOLO检测 ({{ result.detections.length }})
            </div>
            <div class="detection-items">
              <div v-for="(det, i) in result.detections" :key="i" class="detection-item">
                <el-tag
                  :type="getConfidenceType(det.confidence)"
                  :style="{ opacity: det.confidence }"
                  effect="light"
                  class="detection-tag"
                >
                  <span class="class-name">{{ det.class }}</span>
                  <span class="confidence">{{ (det.confidence * 100).toFixed(0) }}%</span>
                </el-tag>
              </div>
            </div>
          </div>

          <div v-if="result.video_samples && result.video_samples.length > 0" class="llm-section">
            <div class="section-title">
              <el-icon><Film /></el-icon> 视频命中样本 ({{ result.video_samples.length }})
            </div>
            <div class="detection-items">
              <a
                v-for="(sample, si) in result.video_samples"
                :key="si"
                :href="sample.image_url"
                target="_blank"
                rel="noopener noreferrer"
                class="video-sample-link"
              >
                帧 {{ sample.frame_index }}
              </a>
            </div>
          </div>

          <!-- 智能分析/任务摘要 -->
          <div v-if="result.llm_description" class="llm-section">
            <div class="section-title">
              <el-icon><DataAnalysis /></el-icon> 智能分析
            </div>
            <div class="llm-content">
              {{ result.llm_description }}
            </div>
          </div>

          <!-- 错误提示 -->
          <el-alert
            v-if="result.error"
            :title="`错误: ${result.error}`"
            type="error"
            :closable="false"
            style="margin-top: 16px"
          />

          <!-- 操作按钮 -->
          <div class="result-actions">
            <el-button type="primary" link @click="downloadResult(result)">
              <el-icon><Download /></el-icon> 下载
            </el-button>
            <el-button type="danger" link @click="deleteResult(index)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 统计信息 -->
    <el-card v-if="results.length > 0" class="stats-card">
      <template #header>
        <div class="card-header">
          <span class="title">📊 统计信息</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-item">
            <div class="stat-value">{{ totalDetections }}</div>
            <div class="stat-label">总检测数</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-item">
            <div class="stat-value">{{ results.length }}</div>
            <div class="stat-label">图片/视频数</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-item">
            <div class="stat-value">{{ avgConfidence }}</div>
            <div class="stat-label">平均置信度</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-item">
            <div class="stat-value">{{ topClass }}</div>
            <div class="stat-label">最常检测对象</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Download, Delete, Setting, DataAnalysis, Film } from '@element-plus/icons-vue'
import { getApiErrorMessage } from '../utils/error'

const authStore = useAuthStore()

const results = ref<any[]>([])
const taskPollers = new Map<string, number>()
const apiOrigin = (import.meta.env.VITE_API_BASE || 'http://localhost:9500/api').replace(/\/api\/?$/, '')

const normalizeMediaUrl = (url: string) => {
  if (!url) return url
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) return url
  return `${apiOrigin}${url}`
}

const uploadRequest = async (options: any) => {
  const file = options.file
  const formData = new FormData()
  formData.append('file', file)

  const isVideo = typeof file?.type === 'string' && file.type.startsWith('video/')

  if (isVideo) {
    const videoResult = {
      timestamp: new Date().toISOString(),
      processing: true,
      progress: 0,
      detections: [],
      llm_description: '视频检测任务创建中...',
      task_id: '',
      file_name: file.name,
      is_video: true,
      video_samples: [] as any[]
    }
    results.value.unshift(videoResult)

    try {
      const res = await authStore.api.post('/detect/video', formData, {
        timeout: 180000,
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      if (!res.data.success || !res.data.task_id) {
        throw new Error(res.data.message || '任务创建失败')
      }

      videoResult.task_id = res.data.task_id
      videoResult.llm_description = '视频检测任务处理中...'
      startTaskPolling(videoResult)
      options.onSuccess?.({ success: true, task_id: res.data.task_id, is_video: true })
    } catch (e: any) {
      results.value = results.value.filter(r => r !== videoResult)
      options.onError?.(e)
    }
    return
  }

  try {
    // 图片检测 + LLM 可能较慢，单独延长超时
    const res = await authStore.api.post('/detect', formData, {
      timeout: 180000,
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    options.onSuccess?.(res.data)
  } catch (e: any) {
    options.onError?.(e)
  }
}

const startTaskPolling = (resultItem: any) => {
  if (!resultItem.task_id) return

  const timer = window.setInterval(async () => {
    try {
      const res = await authStore.api.get(`/detect/video/tasks/${resultItem.task_id}`)
      if (!res.data.success) return

      const task = res.data.task || {}
      resultItem.progress = task.progress || 0
      resultItem.processing = task.status === 'pending' || task.status === 'running'

      if (task.status === 'completed') {
        resultItem.processing = false
        resultItem.progress = 100
        resultItem.llm_description = task.summary || '视频检测完成'
        resultItem.video_samples = (task.samples || []).map((sample: any) => ({
          ...sample,
          image_url: normalizeMediaUrl(sample.image_url)
        }))

        if (resultItem.video_samples.length > 0) {
          resultItem.annotated_image = resultItem.video_samples[0].image_url
          resultItem.detections = resultItem.video_samples[0].detections || []
        } else {
          resultItem.detections = []
        }

        clearTaskPolling(resultItem.task_id)
        ElMessage.success('视频检测完成')
      } else if (task.status === 'failed') {
        resultItem.processing = false
        resultItem.error = task.message || '视频检测失败'
        resultItem.llm_description = ''
        clearTaskPolling(resultItem.task_id)
        ElMessage.error(resultItem.error)
      }
    } catch (_e) {
      // 轮询期间网络抖动时忽略一次
    }
  }, 1500)

  taskPollers.set(resultItem.task_id, timer)
}

const clearTaskPolling = (taskId: string) => {
  const timer = taskPollers.get(taskId)
  if (timer) {
    clearInterval(timer)
    taskPollers.delete(taskId)
  }
}

const beforeUpload = (file: any) => {
  const validTypes = [
    'image/jpeg', 'image/png', 'image/gif',
    'video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/webm'
  ]

  const isValid = validTypes.includes(file.type)
  const isLt200M = file.size / 1024 / 1024 < 200

  if (!isValid) {
    ElMessage.error('仅支持JPG/PNG/GIF图片或MP4/WebM视频')
    return false
  }

  if (!isLt200M) {
    ElMessage.error('文件大小不能超过200MB')
    return false
  }

  return true
}

const onUploadSuccess = (response: any) => {
  if (response?.is_video) {
    return
  }

  if (response.success) {
    const result = {
      ...response,
      timestamp: new Date().toISOString(),
      processing: false
    }
    results.value.unshift(result)
    ElMessage.success('检测成功！')
  } else {
    ElMessage.error(response.message || '检测失败')
  }
}

const onUploadError = (error: any) => {
  console.error('Upload error:', error)
  ElMessage.error(getApiErrorMessage(error, '上传失败'))
}

const getConfidenceType = (confidence: number) => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'warning'
  return 'info'
}

const downloadResult = (result: any) => {
  if (result.annotated_image) {
    const link = document.createElement('a')
    link.href = result.annotated_image
    link.download = `detection-${Date.now()}.jpg`
    link.click()
    ElMessage.success('开始下载')
  }
}

const deleteResult = async (index: number) => {
  await ElMessageBox.confirm('确定删除此条检测记录？', '提示', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
  results.value.splice(index, 1)
  ElMessage.success('已删除')
}

const clearResults = async () => {
  await ElMessageBox.confirm('确定清空所有检测历史？', '提示', {
    confirmButtonText: '清空',
    cancelButtonText: '取消',
    type: 'warning',
  })
  results.value = []
  ElMessage.success('已清空')
}

const totalDetections = computed(() => {
  return results.value.reduce((sum, r) => sum + (r.detections?.length || 0), 0)
})

const avgConfidence = computed(() => {
  if (totalDetections.value === 0) return '0%'
  const sum = results.value.reduce((acc, r) => {
    if (!r.detections) return acc
    return acc + r.detections.reduce((s: number, d: any) => s + (d.confidence || 0), 0)
  }, 0)
  return ((sum / totalDetections.value) * 100).toFixed(1) + '%'
})

const topClass = computed(() => {
  const classes: Record<string, number> = {}
  results.value.forEach(r => {
    r.detections?.forEach((d: any) => {
      classes[d.class] = (classes[d.class] || 0) + 1
    })
  })
  const sorted = Object.entries(classes).sort((a, b) => b[1] - a[1])
  return sorted.length > 0 ? sorted[0][0] : '无'
})

onMounted(() => {
  const saved = localStorage.getItem('detection_results')
  if (saved) {
    results.value = JSON.parse(saved)
  }
})

onUnmounted(() => {
  taskPollers.forEach(timer => clearInterval(timer))
  taskPollers.clear()
})

watch(results, (newVal) => {
  localStorage.setItem('detection_results', JSON.stringify(newVal.slice(0, 20)))
}, { deep: true })
</script>

<style scoped>
.detection-page {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #7c3aed;
}

.upload-card {
  background: linear-gradient(135deg, #fff 0%, #faf5ff 100%);
  border: 2px dashed #d084d0;
}

.upload-area {
  width: 100%;
}

.results-section {
  animation: slideUp 0.4s ease;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.section-header h3 {
  margin: 0;
  color: #7c3aed;
  font-size: 18px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 20px;
}

.result-card {
  background: linear-gradient(135deg, #fff 0%, #faf5ff 100%);
  border: 1px solid #ede5f5;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.result-card:hover {
  box-shadow: 0 8px 24px rgba(208, 132, 208, 0.15);
  transform: translateY(-2px);
}

.processing-bar {
  margin-bottom: 16px;
}

.image-box {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
  background: #f5f5f5;
}

.detection-image {
  width: 100%;
  height: auto;
  max-height: 300px;
  object-fit: cover;
  display: block;
}

.image-info {
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.05);
  font-size: 12px;
  color: #9380c5;
}

.yolo-section,
.llm-section {
  margin-bottom: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 600;
  color: #7c3aed;
}

.section-title :deep(.el-icon) {
  color: #d084d0;
}

.detection-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detection-item {
  display: inline-block;
}

.detection-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, rgba(208, 132, 208, 0.1) 0%, rgba(167, 139, 219, 0.05) 100%);
}

.video-sample-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(124, 58, 237, 0.08);
  color: #7c3aed;
  text-decoration: none;
  font-size: 12px;
}

.class-name {
  font-weight: 600;
}

.confidence {
  font-size: 12px;
  opacity: 0.8;
}

.llm-content {
  padding: 12px;
  background: #faf5ff;
  border-left: 3px solid #d084d0;
  border-radius: 4px;
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
}

.result-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ede5f5;
}

.stats-card {
  background: linear-gradient(135deg, #fff 0%, #faf5ff 100%);
  border: 1px solid #ede5f5;
}

.stat-item {
  text-align: center;
  padding: 12px;
  border-radius: 8px;
  background: rgba(208, 132, 208, 0.05);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #7c3aed;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: #9380c5;
  margin-top: 4px;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .results-grid {
    grid-template-columns: 1fr;
  }
}
</style>
