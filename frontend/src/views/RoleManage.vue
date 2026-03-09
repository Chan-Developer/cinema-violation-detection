<template>
  <div class="role-page">
    <div class="page-toolbar">
      <el-button type="primary" round @click="openAdd">
        <el-icon><Plus /></el-icon> 添加角色
      </el-button>
    </div>

    <el-card>
      <el-table :data="roles" stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="角色名称" width="150" />
        <el-table-column prop="description" label="描述" min-width="300" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editRole(row)" :disabled="['admin', 'manager', 'operator', 'maintenance'].includes(row.name)">编辑</el-button>
            <el-button type="danger" link size="small" @click="deleteRole(row)" :disabled="['admin', 'manager', 'operator', 'maintenance'].includes(row.name)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editingRole ? '编辑角色' : '添加角色'" width="520px" top="8vh">
      <el-form :model="roleForm" label-width="80px">
        <el-form-item label="角色名称">
          <el-input v-model="roleForm.name" :disabled="!!editingRole" placeholder="英文角色名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="roleForm.description" type="textarea" rows="4" placeholder="角色描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRole">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getApiErrorMessage } from '../utils/error'

const authStore = useAuthStore()

const loading = ref(false)
const roles = ref<any[]>([])
const showDialog = ref(false)
const editingRole = ref<any>(null)

const roleForm = reactive({
  name: '',
  description: ''
})

const loadRoles = async () => {
  loading.value = true
  try {
    const res = await authStore.api.get('/roles')
    if (res.data.success) {
      roles.value = res.data.roles
    }
  } catch (e) {
    ElMessage.error('加载角色失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openAdd = () => {
  editingRole.value = null
  Object.assign(roleForm, { name: '', description: '' })
  showDialog.value = true
}

const editRole = (r: any) => {
  editingRole.value = r
  Object.assign(roleForm, {
    name: r.name,
    description: r.description || ''
  })
  showDialog.value = true
}

const saveRole = async () => {
  try {
    if (!roleForm.name) {
      ElMessage.error('角色名称不能为空')
      return
    }

    const payload = { ...roleForm }
    if (editingRole.value) {
      await authStore.api.put(`/roles/${editingRole.value.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await authStore.api.post('/roles', payload)
      ElMessage.success('添加成功')
    }
    showDialog.value = false
    loadRoles()
  } catch (e: any) {
    console.error('saveRole failed:', e)
    ElMessage.error(getApiErrorMessage(e, '操作失败'))
  }
}

const deleteRole = async (r: any) => {
  await ElMessageBox.confirm(`确定删除角色「${r.name}」？`, '提示', { type: 'warning' })
  try {
    await authStore.api.delete(`/roles/${r.id}`)
    ElMessage.success('删除成功')
    loadRoles()
  } catch (e: any) {
    console.error('deleteRole failed:', e)
    ElMessage.error(getApiErrorMessage(e, '删除失败'))
  }
}

onMounted(() => {
  loadRoles()
})
</script>

<style scoped>
.role-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.page-toolbar {
  display: flex;
  justify-content: flex-end;
}
</style>
