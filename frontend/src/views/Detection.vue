<template>
  <div class="detection-page">
    <el-card class="upload-card">
      <h3>📸 图片/视频检测</h3>
      <el-upload
        drag
        :action="`${apiUrl}/api/detect`"
        :headers="uploadHeaders"
        :on-success="onUploadSuccess"
        :on-error="onUploadError"
        :before-upload="beforeUpload"
        accept=".jpg,.jpeg,.png,.gif,.mp4,.avi,.mov,.webm"
        multiple
        class="upload-area"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">拖拽文件到这里或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">
            支持图片（JPG/PNG/GIF）和视频（MP4/AVI/MOV/WebM），最大 200MB
          </div>
        </template>
      </el-upload>
    </el-card>

    <!-- 检测结果 -->
    <div v-if="results.length > 0" class="results-container">
      <h3>🎯 检测结果</h3>
      <div class="results-grid">
        <el-card v-for="(result, index) in results" :key="index" class="result-card">
          <!-- 标注图片 -->
          <div v-if="result.annotated_image" class="image-container">
            <img :src="result.annotated_image" alt="检测结果" class="annotated-image" />
          </div>

          <!-- 检测到的物体 -->
          <div v-if="result.detections && result.detections.length > 0" class="detections-section">
            <h4>📋 检测到的物体 ({{ result.detections.length }})</h4>
            <div class="detection-list">
              <div v-for="(det, i) in result.detections" :key="i" class="detection-item">
                <el-tag :type="getConfidenceType(det.confidence)" effect="light">
                  {{ det.class }} - {{ (det.confidence * 100).toFixed(1) }}%
                </el-tag>
              </div>
            </div>
          </div>

          <!-- LLM 描述 -->
          <div v-if="result.llm_description" class="description-section">
            <h4>🤖 智能描述</h4>
            <el-alert
              :title="result.llm_description"
              type="info"
              :closable="false"
              description=""
            />
          </div>

          <!-- 错误信息 -->
          <div v-if="result.error" class="error-section">
            <el-alert
              :title="`错误: ${result.error}`"
              type="error"
              :closable="false"
            />
          </div>
        </el-card>
      </div>
    </div>

    <!-- 检测历史 -->
    <el-card v-if="historyVisible" class="history-card">
      <h3>📜 检测历史</h3>
      <el-table :data="results" stripe style="width: 100%">
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="detections" label="检测数" width="80">
          <template #default="{ row }">
            {{ row.detections?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="llm_description" label="描述" min-width="300" show-overflow-tooltip />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="downloadResult(row)">
              下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const authStore = useAuthStore()

const apiUrl = computed(() => {
  return window.location.origin
})

const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

const results = ref<any[]>([])
const historyVisible = ref(false)

const beforeUpload = (file: any) => {
  const isValid = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'video/mp4',
    'video/x-msvideo',
    'video/quicktime',
    'video/webm'
  ].includes(file.type)

  const isLt200M = file.size / 1024 / 1024 < 200

  if (!isValid) {
    ElMessage.error('仅支持 JPG/PNG/GIF 图片或 MP4/AVI/MOV/WebM 视频')
    return false
  }

  if (!isLt200M) {
    ElMessage.error('文件大小不能超过 200MB')
    return false
  }

  return true
}

const onUploadSuccess = (response: any) => {
  if (response.success) {
    const result = {
      ...response,
      timestamp: new Date().toLocaleString('zh-CN'),
      error: null
    }
    results.value.unshift(result)
    ElMessage.success('检测成功！')
    historyVisible.value = true
  } else {
    ElMessage.error(response.message || '检测失败')
  }
}

const onUploadError = (error: any) => {
  console.error('Upload error:', error)
  ElMessage.error('上传失败，请重试')
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

onMounted(() => {
  // Load results from localStorage if available
  const saved = localStorage.getItem('detection_results')
  if (saved) {
    results.value = JSON.parse(saved)
    if (results.value.length > 0) {
      historyVisible.value = true
    }
  }
})

// Save results to localStorage whenever they change
watch(results, (newVal) => {
  localStorage.setItem('detection_results', JSON.stringify(newVal.slice(0, 10)))
}, { deep: true })
</script>

<style scoped>
.detection-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.upload-card {
  border: 1px solid #e0e0e0;
}

.upload-card h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #333;
}

.upload-area {
  width: 100%;
}

.results-container {
  margin-top: 24px;
}

.results-container h3 {
  margin-bottom: 16px;
  font-size: 18px;
  color: #333;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
  gap: 16px;
}

.result-card {
  border: 1px solid #e0e0e0;
  padding: 16px;
}

.image-container {
  margin-bottom: 16px;
  border-radius: 4px;
  overflow: hidden;
  background: #f5f5f5;
}

.annotated-image {
  width: 100%;
  height: auto;
  max-height: 400px;
  object-fit: contain;
}

.detections-section {
  margin-bottom: 16px;
}

.detections-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #333;
}

.detection-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detection-item {
  flex-shrink: 0;
}

.description-section {
  margin-bottom: 16px;
}

.description-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #333;
}

.error-section {
  margin-top: 16px;
}

.history-card {
  margin-top: 24px;
}

.history-card h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #333;
}
</style>
