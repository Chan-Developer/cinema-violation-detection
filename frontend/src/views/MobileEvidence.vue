<template>
  <div class="mobile-evidence-page">
    <section class="desktop-gate">
      <div class="gate-panel">
        <el-icon :size="40"><Iphone /></el-icon>
        <h1>手机端留证页面</h1>
        <p>该页面仅适配手机端，用手机浏览器访问 /mobile/evidence 后可拍照上传现场证据。</p>
      </div>
    </section>

    <section class="phone-app">
      <header class="phone-header">
        <div>
          <p class="eyebrow">现场留证</p>
          <h1>拍照上传证据</h1>
        </div>
        <el-tag type="success" effect="light" round>手机端</el-tag>
      </header>

      <main class="phone-content">
        <div class="capture-panel">
          <div v-if="previewUrl" class="preview-wrap">
            <img :src="previewUrl" alt="留证预览" class="preview-image" />
          </div>
          <label v-else class="capture-empty" for="evidence-file">
            <el-icon :size="46"><Camera /></el-icon>
            <span>拍照或选择图片</span>
          </label>

          <input
            id="evidence-file"
            ref="fileInputRef"
            class="file-input"
            type="file"
            accept="image/*"
            capture="environment"
            @change="handleFileChange"
          />

          <div class="capture-actions">
            <el-button round @click="openPicker">
              <el-icon><Camera /></el-icon>
              选择照片
            </el-button>
            <el-button v-if="selectedFile" round @click="clearSelected">
              <el-icon><RefreshLeft /></el-icon>
              重选
            </el-button>
          </div>
        </div>

        <el-form label-position="top" class="evidence-form">
          <el-form-item label="关联影院">
            <el-select v-model="form.cinema_id" placeholder="可选" clearable @change="handleCinemaChange">
              <el-option v-for="cinema in cinemas" :key="cinema.id" :label="cinema.name" :value="cinema.id" />
            </el-select>
          </el-form-item>

          <el-form-item label="关联摄像头">
            <el-select v-model="form.camera_id" placeholder="可选" clearable>
              <el-option
                v-for="camera in filteredCameras"
                :key="camera.id"
                :label="camera.name"
                :value="camera.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="现场位置">
            <el-input v-model="form.location_text" placeholder="例如 3号厅后排入口" />
          </el-form-item>

          <el-form-item label="情况说明">
            <el-input
              v-model="form.note"
              type="textarea"
              :rows="3"
              maxlength="200"
              show-word-limit
              placeholder="补充说明现场情况"
            />
          </el-form-item>
        </el-form>

        <el-button
          class="submit-button"
          type="primary"
          round
          :loading="uploading"
          :disabled="!selectedFile"
          @click="submitEvidence"
        >
          <el-icon><Upload /></el-icon>
          上传留证
        </el-button>

        <section class="recent-section">
          <div class="section-title">
            <span>最近留证</span>
            <el-button link size="small" @click="loadEvidences">刷新</el-button>
          </div>
          <el-empty v-if="evidences.length === 0" description="暂无留证记录" />
          <div v-else class="evidence-list">
            <article v-for="item in evidences" :key="item.id" class="evidence-item">
              <img :src="normalizeMediaUrl(item.image_url)" alt="留证图片" />
              <div>
                <strong>{{ item.location_text || item.camera_name || item.cinema_name || '现场留证' }}</strong>
                <p>{{ item.note || '未填写说明' }}</p>
                <span>{{ item.created_at }}</span>
              </div>
            </article>
          </div>
        </section>
      </main>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { getApiErrorMessage } from '../utils/error'
import { getApiOrigin } from '../utils/apiBase'

const authStore = useAuthStore()

const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const uploading = ref(false)
const cinemas = ref<any[]>([])
const cameras = ref<any[]>([])
const evidences = ref<any[]>([])

const form = reactive({
  cinema_id: null as number | null,
  camera_id: null as number | null,
  location_text: '',
  note: '',
})

const apiOrigin = getApiOrigin()

const filteredCameras = computed(() => {
  if (!form.cinema_id) return cameras.value
  return cameras.value.filter(camera => camera.cinema_id === form.cinema_id)
})

const normalizeMediaUrl = (url?: string) => {
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  return `${apiOrigin}${url}`
}

const openPicker = () => {
  fileInputRef.value?.click()
}

const clearSelected = () => {
  selectedFile.value = null
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  if (fileInputRef.value) fileInputRef.value.value = ''
}

const handleFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过20MB')
    return
  }
  clearSelected()
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
}

const handleCinemaChange = () => {
  if (form.camera_id && !filteredCameras.value.some(camera => camera.id === form.camera_id)) {
    form.camera_id = null
  }
}

const loadOptions = async () => {
  const [cinemaRes, cameraRes] = await Promise.all([
    authStore.api.get('/cinemas?per_page=100'),
    authStore.api.get('/cameras?per_page=100'),
  ])
  if (cinemaRes.data.success) cinemas.value = cinemaRes.data.cinemas || []
  if (cameraRes.data.success) cameras.value = cameraRes.data.cameras || []
}

const loadEvidences = async () => {
  try {
    const res = await authStore.api.get('/evidence/mobile?per_page=20')
    if (res.data.success) evidences.value = res.data.evidences || []
  } catch (e) {
    console.error(e)
  }
}

const submitEvidence = async () => {
  if (!selectedFile.value) {
    ElMessage.error('请先拍照或选择图片')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    if (form.cinema_id) formData.append('cinema_id', String(form.cinema_id))
    if (form.camera_id) formData.append('camera_id', String(form.camera_id))
    formData.append('location_text', form.location_text)
    formData.append('note', form.note)

    const res = await authStore.api.post('/evidence/mobile', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    })

    if (res.data.success) {
      ElMessage.success('留证上传成功')
      clearSelected()
      form.location_text = ''
      form.note = ''
      await loadEvidences()
    }
  } catch (e: any) {
    ElMessage.error(getApiErrorMessage(e, '上传失败'))
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  loadOptions().catch(e => console.error(e))
  loadEvidences()
})

onBeforeUnmount(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})
</script>

<style scoped>
.mobile-evidence-page {
  min-height: 100vh;
  background: #f4f7f2;
}

.desktop-gate {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 40px;
  background: linear-gradient(135deg, #f7fbf7 0%, #edf4ff 100%);
}

.gate-panel {
  width: min(460px, 100%);
  padding: 32px;
  border: 1px solid #d8e3da;
  border-radius: 8px;
  background: #fff;
  color: #1b312d;
  text-align: center;
  box-shadow: 0 18px 40px rgba(34, 61, 56, 0.12);
}

.gate-panel h1 {
  margin: 16px 0 10px;
  font-size: 24px;
}

.gate-panel p {
  color: #66756f;
  line-height: 1.7;
}

.phone-app {
  display: none;
}

@media (max-width: 768px) {
  .desktop-gate {
    display: none;
  }

  .phone-app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background:
      linear-gradient(160deg, rgba(40, 93, 79, 0.96) 0%, rgba(40, 93, 79, 0.86) 34%, transparent 34%),
      #f4f7f2;
  }

  .phone-header {
    padding: 26px 20px 18px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    color: #fff;
  }

  .eyebrow {
    margin-bottom: 4px;
    font-size: 13px;
    opacity: 0.82;
  }

  .phone-header h1 {
    font-size: 28px;
    line-height: 1.2;
  }

  .phone-content {
    padding: 0 14px 28px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .capture-panel,
  .evidence-form,
  .recent-section {
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid #dfe8dd;
    border-radius: 8px;
    box-shadow: 0 14px 34px rgba(37, 68, 58, 0.12);
  }

  .capture-panel {
    padding: 12px;
  }

  .preview-wrap,
  .capture-empty {
    width: 100%;
    aspect-ratio: 4 / 3;
    border-radius: 8px;
    overflow: hidden;
    background: #e8eee6;
  }

  .preview-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .capture-empty {
    display: grid;
    place-items: center;
    gap: 8px;
    color: #2f5f51;
    border: 1px dashed #9bb7aa;
    font-weight: 700;
  }

  .file-input {
    display: none;
  }

  .capture-actions {
    display: flex;
    gap: 10px;
    margin-top: 12px;
  }

  .capture-actions .el-button {
    flex: 1;
  }

  .evidence-form {
    padding: 14px;
  }

  .submit-button {
    width: 100%;
    height: 48px;
    font-size: 16px;
    background: #d96f32;
    border-color: #d96f32;
  }

  .recent-section {
    padding: 14px;
  }

  .section-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    font-weight: 800;
    color: #213a33;
  }

  .evidence-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .evidence-item {
    display: grid;
    grid-template-columns: 72px 1fr;
    gap: 10px;
    align-items: center;
    padding: 8px;
    border-radius: 8px;
    background: #f7faf6;
  }

  .evidence-item img {
    width: 72px;
    height: 72px;
    object-fit: cover;
    border-radius: 6px;
  }

  .evidence-item strong {
    display: block;
    color: #213a33;
    font-size: 14px;
  }

  .evidence-item p {
    margin: 4px 0;
    color: #63736c;
    font-size: 13px;
    line-height: 1.4;
  }

  .evidence-item span {
    color: #88968f;
    font-size: 12px;
  }
}
</style>
