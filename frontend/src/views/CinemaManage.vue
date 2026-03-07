<template>
  <div class="cinema-page">
    <div class="page-toolbar">
      <el-button type="primary" round @click="openAdd">
        <el-icon><Plus /></el-icon> 添加影院
      </el-button>
    </div>

    <el-card>
      <el-table :data="cinemas" stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="影院名称" min-width="160" />
        <el-table-column prop="city" label="城市" width="100" />
        <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="contact" label="联系人" width="100" />
        <el-table-column prop="hall_count" label="影厅" width="70" align="center" />
        <el-table-column prop="camera_count" label="摄像头" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'danger'" size="small" round>
              {{ row.status ? '营业' : '停业' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editCinema(row)">编辑</el-button>
            <el-button type="success" link size="small" @click="manageHalls(row)">影厅</el-button>
            <el-button type="danger" link size="small" @click="deleteCinema(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editingCinema ? '编辑影院' : '添加影院'" width="520px" top="8vh">
      <el-form :model="form" label-width="80px" :rules="formRules" ref="formRef">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入影院名称" />
        </el-form-item>
        <el-form-item label="城市" prop="city">
          <el-input v-model="form.city" placeholder="如: 北京" />
        </el-form-item>
        <el-form-item label="区域">
          <el-input v-model="form.district" placeholder="如: 朝阳区" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="form.address" placeholder="详细地址" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" placeholder="联系电话" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact" placeholder="负责人姓名" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="营业" inactive-text="停业" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveCinema">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

const authStore = useAuthStore()

const loading = ref(false)
const cinemas = ref<any[]>([])
const showDialog = ref(false)
const editingCinema = ref<any>(null)
const formRef = ref<FormInstance>()

const form = reactive({ name: '', city: '', district: '', address: '', phone: '', contact: '', status: 1 })
const formRules: FormRules = {
  name: [{ required: true, message: '请输入影院名称', trigger: 'blur' }],
  city: [{ required: true, message: '请输入城市', trigger: 'blur' }],
  address: [{ required: true, message: '请输入地址', trigger: 'blur' }],
}

const loadCinemas = async () => {
  loading.value = true
  try {
    const res = await authStore.api.get('/cinemas?per_page=100')
    if (res.data.success) cinemas.value = res.data.cinemas
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const openAdd = () => {
  editingCinema.value = null
  Object.assign(form, { name: '', city: '', district: '', address: '', phone: '', contact: '', status: 1 })
  showDialog.value = true
}

const editCinema = (c: any) => {
  editingCinema.value = c
  Object.assign(form, { name: c.name, city: c.city, district: c.district || '', address: c.address, phone: c.phone, contact: c.contact, status: c.status })
  showDialog.value = true
}

const saveCinema = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      if (editingCinema.value) {
        await authStore.api.put(`/cinemas/${editingCinema.value.id}`, form)
        ElMessage.success('更新成功')
      } else {
        await authStore.api.post('/cinemas', form)
        ElMessage.success('添加成功')
      }
      showDialog.value = false
      loadCinemas()
    } catch (e: any) {
      ElMessage.error(e.response?.data?.message || '操作失败')
    }
  })
}

const deleteCinema = async (c: any) => {
  await ElMessageBox.confirm(`确定删除影院「${c.name}」？`, '提示', { type: 'warning' })
  try {
    await authStore.api.delete(`/cinemas/${c.id}`)
    ElMessage.success('删除成功')
    loadCinemas()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.message || '删除失败')
  }
}

const manageHalls = (c: any) => {
  ElMessage.info(`影厅管理: ${c.name} — 功能开发中`)
}

onMounted(() => loadCinemas())
</script>

<style scoped>
.cinema-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.page-toolbar {
  display: flex;
  justify-content: flex-end;
}
</style>
