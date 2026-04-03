<template>
  <div class="role-page">
    <el-card class="relation-card">
      <template #header>
        <div class="relation-header">
          <span>系统角色关系</span>
          <el-tag type="info" round>单一权限定义</el-tag>
        </div>
      </template>
      <el-table :data="roleRelations" size="small" border>
        <el-table-column prop="label" label="角色" width="110" />
        <el-table-column prop="name" label="编码" width="120" />
        <el-table-column prop="scopeText" label="作用域" width="120" />
        <el-table-column prop="description" label="职责说明" min-width="220" />
        <el-table-column label="能力" min-width="260">
          <template #default="{ row }">
            <el-tag
              v-for="cap in row.capabilities"
              :key="cap"
              size="small"
              effect="plain"
              style="margin-right: 6px; margin-bottom: 4px"
            >
              {{ cap }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

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
            <el-button type="primary" link size="small" @click="editRole(row)" :disabled="isSystemRole(row.name)">编辑</el-button>
            <el-button type="danger" link size="small" @click="deleteRole(row)" :disabled="isSystemRole(row.name)">删除</el-button>
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
import { SYSTEM_ROLES } from '../constants/roles'

const authStore = useAuthStore()

const loading = ref(false)
const roles = ref<any[]>([])
const roleRelations = ref<any[]>([])
const showDialog = ref(false)
const editingRole = ref<any>(null)

const roleForm = reactive({
  name: '',
  description: ''
})

const isSystemRole = (name: string) => SYSTEM_ROLES.includes(name as any)

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

const loadRoleRelations = async () => {
  try {
    const res = await authStore.api.get('/auth/role-relations')
    if (res.data.success) {
      roleRelations.value = (res.data.roles || []).map((r: any) => ({
        ...r,
        capabilities: [
          r.can_manage_users ? '用户管理' : null,
          r.can_manage_roles ? '角色管理' : null,
          r.can_manage_cinemas ? '影院管理' : null,
          r.can_manage_cameras ? '摄像头管理' : null,
          r.can_process_alarms ? '告警处置' : null
        ].filter(Boolean),
        scopeText: r.scope === 'cinema' ? '所属影院' : '全局'
      }))
    }
  } catch (e) {
    console.error(e)
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
  loadRoleRelations()
})
</script>

<style scoped>
.role-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.relation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-toolbar {
  display: flex;
  justify-content: flex-end;
}
</style>
