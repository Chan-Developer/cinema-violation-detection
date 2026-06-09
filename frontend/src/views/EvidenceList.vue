<template>
  <div class="evidence-page">
    <el-card>
      <template #header>
        <div class="header-row">
          <span class="title">手机留证记录</span>
          <el-button type="primary" plain round @click="loadEvidences">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table :data="evidences" stripe v-loading="loading" style="width: 100%">
        <el-table-column label="图片" width="112">
          <template #default="{ row }">
            <el-image
              class="evidence-thumb"
              :src="normalizeMediaUrl(row.image_url)"
              :preview-src-list="[normalizeMediaUrl(row.image_url)]"
              preview-teleported
              fit="cover"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="170" />
        <el-table-column prop="user_name" label="上传人" width="120" />
        <el-table-column prop="cinema_name" label="影院" width="150" show-overflow-tooltip />
        <el-table-column prop="camera_name" label="关联摄像头" width="150" show-overflow-tooltip />
        <el-table-column prop="location_text" label="现场位置" min-width="160" show-overflow-tooltip />
        <el-table-column prop="note" label="情况说明" min-width="220" show-overflow-tooltip />
      </el-table>

      <div class="table-footer">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.per_page"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="loadEvidences"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getApiOrigin } from '../utils/apiBase'

const authStore = useAuthStore()
const loading = ref(false)
const evidences = ref<any[]>([])
const pagination = reactive({ page: 1, per_page: 20, total: 0 })
const apiOrigin = getApiOrigin()

const normalizeMediaUrl = (url?: string) => {
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  return `${apiOrigin}${url}`
}

const loadEvidences = async () => {
  loading.value = true
  try {
    const res = await authStore.api.get(`/evidence/mobile?page=${pagination.page}&per_page=${pagination.per_page}`)
    if (res.data.success) {
      evidences.value = res.data.evidences || []
      pagination.total = res.data.total || 0
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadEvidences)
</script>

<style scoped>
.evidence-page {
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
  font-weight: 700;
  color: #303133;
}

.evidence-thumb {
  width: 76px;
  height: 76px;
  border-radius: 8px;
  border: 1px solid #e5e8ef;
  overflow: hidden;
}

.table-footer {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
