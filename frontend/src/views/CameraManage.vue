<template>
  <div class="camera-page">
    <div class="page-toolbar">
      <el-button type="primary" round @click="openAdd">
        <el-icon><Plus /></el-icon> 添加摄像头
      </el-button>
    </div>

    <el-card>
      <el-table :data="cameras" stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="cinema_name" label="影院" width="130" />
        <el-table-column prop="hall_name" label="影厅" width="100" />
        <el-table-column prop="position" label="位置" width="100" />
        <el-table-column prop="rtsp_url" label="RTSP地址" min-width="200" show-overflow-tooltip />
        <el-table-column prop="detection_enabled" label="检测" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.detection_enabled ? 'success' : 'info'" size="small" round>
              {{ row.detection_enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : row.status === 2 ? 'warning' : 'danger'" size="small" round>
              {{ ['离线', '在线', '维护'][row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editCamera(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="deleteCamera(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-footer">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.per_page"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="loadCameras"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editingCamera ? '编辑摄像头' : '添加摄像头'" width="600px" top="6vh">
      <el-form :model="cameraForm" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="cameraForm.name" placeholder="摄像头名称" />
        </el-form-item>
        <el-form-item label="影院">
          <el-select v-model="cameraForm.cinema_id" placeholder="选择影院" style="width: 100%" @change="onCinemaChange">
            <el-option v-for="c in cinemas" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="影厅">
          <el-select v-model="cameraForm.hall_id" placeholder="选择影厅" style="width: 100%">
            <el-option v-for="h in halls" :key="h.id" :label="h.name" :value="h.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="cameraForm.position" placeholder="如: 入口、座位区" />
        </el-form-item>
        <el-form-item label="RTSP地址">
          <el-input v-model="cameraForm.rtsp_url" placeholder="rtsp://..." />
        </el-form-item>
        <el-form-item label="检测类型">
          <el-checkbox-group v-model="cameraForm.detection_types">
            <el-checkbox label="photo" value="photo">盗摄检测</el-checkbox>
            <el-checkbox label="smoke" value="smoke">吸烟检测</el-checkbox>
            <el-checkbox label="crowd" value="crowd">拥堵检测</el-checkbox>
            <el-checkbox label="walk" value="walk">随意走动</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="启用检测">
          <el-switch v-model="cameraForm.detection_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveCamera">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()

const loading = ref(false)
const cameras = ref<any[]>([])
const cinemas = ref<any[]>([])
const halls = ref<any[]>([])
const showDialog = ref(false)
const editingCamera = ref<any>(null)

const cameraForm = reactive({
  name: '', cinema_id: null as number | null, hall_id: null as number | null,
  position: '', rtsp_url: '', detection_types: [] as string[], detection_enabled: true
})
const pagination = reactive({ page: 1, per_page: 20, total: 0 })

const loadCameras = async () => {
  loading.value = true
  try {
    const res = await authStore.api.get(`/cameras?page=${pagination.page}&per_page=${pagination.per_page}`)
    if (res.data.success) {
      cameras.value = res.data.cameras
      pagination.total = res.data.total
    }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const loadCinemas = async () => {
  try {
    const res = await authStore.api.get('/cinemas?per_page=100')
    if (res.data.success) cinemas.value = res.data.cinemas
  } catch (e) { console.error(e) }
}

const onCinemaChange = async () => {
  cameraForm.hall_id = null
  if (!cameraForm.cinema_id) { halls.value = []; return }
  try {
    const res = await authStore.api.get(`/cinemas/${cameraForm.cinema_id}/halls`)
    if (res.data.success) halls.value = res.data.halls
  } catch (e) { console.error(e) }
}

const openAdd = () => {
  editingCamera.value = null
  Object.assign(cameraForm, { name: '', cinema_id: null, hall_id: null, position: '', rtsp_url: '', detection_types: [], detection_enabled: true })
  showDialog.value = true
}

const editCamera = (cam: any) => {
  editingCamera.value = cam
  cameraForm.name = cam.name
  cameraForm.cinema_id = cam.cinema_id
  cameraForm.hall_id = cam.hall_id
  cameraForm.position = cam.position
  cameraForm.rtsp_url = cam.rtsp_url
  cameraForm.detection_types = cam.detection_types || []
  cameraForm.detection_enabled = !!cam.detection_enabled
  showDialog.value = true
  onCinemaChange()
}

const saveCamera = async () => {
  try {
    const data = { ...cameraForm, detection_types: cameraForm.detection_types.join(',') }
    if (editingCamera.value) {
      await authStore.api.put(`/cameras/${editingCamera.value.id}`, data)
      ElMessage.success('更新成功')
    } else {
      await authStore.api.post('/cameras', data)
      ElMessage.success('添加成功')
    }
    showDialog.value = false
    loadCameras()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '操作失败')
  }
}

const deleteCamera = async (cam: any) => {
  await ElMessageBox.confirm(`确定删除摄像头「${cam.name}」？`, '提示', { type: 'warning' })
  try {
    await authStore.api.delete(`/cameras/${cam.id}`)
    ElMessage.success('删除成功')
    loadCameras()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '删除失败')
  }
}

onMounted(() => { loadCameras(); loadCinemas() })
</script>

<style scoped>
.camera-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.page-toolbar {
  display: flex;
  justify-content: flex-end;
}
.table-footer {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
