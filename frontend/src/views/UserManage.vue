<template>
  <div class="user-page">
    <div class="page-toolbar">
      <el-button type="primary" round @click="openAdd">
        <el-icon><Plus /></el-icon> 添加用户
      </el-button>
    </div>

    <el-card>
      <el-table :data="users" stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="姓名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机" width="130" />
        <el-table-column prop="role" label="角色" width="110">
          <template #default="{ row }">
            <el-tag :type="getRoleTag(row.role)" size="small" effect="light" round>
              {{ getRoleName(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="cinema_name" label="所属影院" width="120" />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'danger'" size="small" round>
              {{ row.status ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="175" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editUser(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="deleteUser(row)" :disabled="row.username === 'admin'">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-footer">
        <el-pagination
          v-model:current-page="pagination.page"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="loadUsers"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editingUser ? '编辑用户' : '添加用户'" width="520px" top="8vh">
      <el-form :model="userForm" :rules="formRules" ref="formRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" :disabled="!!editingUser" placeholder="登录用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!editingUser">
          <el-input v-model="userForm.password" type="password" show-password placeholder="设置密码" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="userForm.real_name" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="userForm.email" placeholder="邮箱地址" />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="userForm.phone" placeholder="手机号码" />
        </el-form-item>
        <el-form-item label="角色" prop="role_id">
          <el-select v-model="userForm.role_id" style="width: 100%">
            <el-option v-for="r in roles" :key="r.id" :label="r.description" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="影院" v-if="userForm.role_id === 2">
          <el-select v-model="userForm.cinema_id" placeholder="选择影院" style="width: 100%">
            <el-option v-for="c in cinemas" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="userForm.status" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { getApiErrorMessage } from '../utils/error'

const authStore = useAuthStore()

const loading = ref(false)
const users = ref<any[]>([])
const roles = ref<any[]>([])
const cinemas = ref<any[]>([])
const showDialog = ref(false)
const editingUser = ref<any>(null)
const formRef = ref<FormInstance>()

const userForm = reactive({
  username: '', password: '', real_name: '', email: '', phone: '',
  role_id: null as number | null, cinema_id: null as number | null, status: 1
})
const formRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{
    validator: (_rule, value, callback) => {
      if (!editingUser.value && !value) {
        callback(new Error('请输入密码'))
        return
      }
      callback()
    },
    trigger: 'blur'
  }],
  role_id: [{ required: true, message: '请选择角色', trigger: 'change' }],
}
const pagination = reactive({ page: 1, total: 0 })

const loadUsers = async () => {
  loading.value = true
  try {
    const res = await authStore.api.get(`/auth/users?page=${pagination.page}&per_page=20`)
    if (res.data.success) { users.value = res.data.users; pagination.total = res.data.total }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const loadRoles = async () => {
  try {
    const res = await authStore.api.get('/auth/roles')
    if (res.data.success) roles.value = res.data.roles
  } catch (e) { console.error(e) }
}

const loadCinemas = async () => {
  try {
    const res = await authStore.api.get('/cinemas?per_page=100')
    if (res.data.success) cinemas.value = res.data.cinemas
  } catch (e) { console.error(e) }
}

const getRoleName = (role: string) =>
  ({ admin: '管理员', manager: '影院经理', operator: '监控员', maintenance: '运维' } as Record<string, string>)[role] || role

const getRoleTag = (role: string) =>
  ({ admin: 'danger', manager: 'success', operator: 'warning', maintenance: 'info' } as Record<string, string>)[role] || 'info'

const openAdd = () => {
  editingUser.value = null
  Object.assign(userForm, { username: '', password: '', real_name: '', email: '', phone: '', role_id: null, cinema_id: null, status: 1 })
  showDialog.value = true
}

const editUser = (u: any) => {
  editingUser.value = u
  Object.assign(userForm, {
    username: u.username, password: '', real_name: u.real_name,
    email: u.email, phone: u.phone, role_id: u.role_id,
    cinema_id: u.cinema_id, status: u.status
  })
  showDialog.value = true
}

const saveUser = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  try {
    const payload = { ...userForm }
    if (editingUser.value) {
      await authStore.api.put(`/auth/users/${editingUser.value.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await authStore.api.post('/auth/users', payload)
      ElMessage.success('添加成功')
    }
    showDialog.value = false
    loadUsers()
  } catch (e: any) {
    console.error('saveUser failed:', e)
    ElMessage.error(getApiErrorMessage(e, '操作失败'))
  }
}

const deleteUser = async (u: any) => {
  await ElMessageBox.confirm(`确定删除用户「${u.real_name || u.username}」？`, '提示', { type: 'warning' })
  try {
    await authStore.api.delete(`/auth/users/${u.id}`)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (e: any) {
    console.error('deleteUser failed:', e)
    ElMessage.error(getApiErrorMessage(e, '删除失败'))
  }
}

onMounted(() => { loadUsers(); loadRoles(); loadCinemas() })
</script>

<style scoped>
.user-page {
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
