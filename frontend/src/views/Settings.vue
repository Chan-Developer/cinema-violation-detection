<template>
  <div class="settings-page">
    <el-row :gutter="24">
      <el-col :span="16">
        <!-- 个人信息 -->
        <el-card class="mb-card">
          <template #header>
            <div class="card-head">
              <el-icon :size="18"><User /></el-icon>
              <span>个人信息</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="用户名">{{ user?.username }}</el-descriptions-item>
            <el-descriptions-item label="姓名">{{ user?.real_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ user?.email || '-' }}</el-descriptions-item>
            <el-descriptions-item label="手机">{{ user?.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="角色">
              <el-tag :type="roleTagType" size="small" round>{{ roleName }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="所属影院">{{ user?.cinema_name || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 通知设置 -->
        <el-card>
          <template #header>
            <div class="card-head">
              <el-icon :size="18"><Bell /></el-icon>
              <span>报警推送设置</span>
            </div>
          </template>
          <el-form label-width="120px">
            <el-form-item label="WebSocket推送">
              <el-switch v-model="settings.wsEnabled" />
              <span class="setting-hint">实时接收报警推送</span>
            </el-form-item>
            <el-form-item label="声音提醒">
              <el-switch v-model="settings.soundEnabled" />
              <span class="setting-hint">新报警时播放提示音</span>
            </el-form-item>
            <el-form-item label="桌面通知">
              <el-switch v-model="settings.desktopNotify" />
              <span class="setting-hint">浏览器桌面通知</span>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="8">
        <!-- 快捷操作 -->
        <el-card class="mb-card">
          <template #header>
            <div class="card-head">
              <el-icon :size="18"><Operation /></el-icon>
              <span>快捷操作</span>
            </div>
          </template>
          <div class="actions-list">
            <el-button type="primary" plain round class="action-btn" @click="initData">
              <el-icon><Refresh /></el-icon> 初始化演示数据
            </el-button>
            <el-button type="warning" plain round class="action-btn" @click="testNotification">
              <el-icon><Bell /></el-icon> 测试通知
            </el-button>
            <el-button type="info" plain round class="action-btn" @click="showAbout">
              <el-icon><InfoFilled /></el-icon> 关于系统
            </el-button>
          </div>
        </el-card>

        <!-- 系统信息 -->
        <el-card>
          <template #header>
            <div class="card-head">
              <el-icon :size="18"><Monitor /></el-icon>
              <span>系统信息</span>
            </div>
          </template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="系统版本">
              <el-tag size="small" round>v1.0.0</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="前端框架">Vue 3 + Element Plus</el-descriptions-item>
            <el-descriptions-item label="后端框架">Flask + SQLAlchemy</el-descriptions-item>
            <el-descriptions-item label="数据库">SQLite</el-descriptions-item>
            <el-descriptions-item label="实时通信">Flask-SocketIO</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()

const user = computed(() => authStore.user)
const roleName = computed(() =>
  ({ admin: '管理员', manager: '影院经理', operator: '监控员', maintenance: '运维' } as Record<string, string>)[user.value?.role || ''] || user.value?.role || ''
)
const roleTagType = computed(() =>
  ({ admin: 'danger', manager: 'success', operator: 'warning', maintenance: 'info' } as Record<string, string>)[user.value?.role || ''] || 'info'
)

const settings = reactive({ wsEnabled: true, soundEnabled: true, desktopNotify: true })

const initData = async () => {
  await ElMessageBox.confirm('初始化数据会重置部分数据，确定继续?', '提示', { type: 'warning' })
  try {
    await authStore.api.post('/init')
    ElMessage.success('初始化成功')
  } catch (_e) { ElMessage.error('初始化失败') }
}

const testNotification = () => {
  ElMessage.success('测试通知: 系统运行正常')
}

const showAbout = () => {
  ElMessageBox.alert(
    '智慧影院行为检测系统 v1.0.0\n\n基于 Flask + Vue 3 开发\n支持盗摄、吸烟、拥堵、走动等行为检测',
    '关于系统',
    { confirmButtonText: '确定' }
  )
}
</script>

<style scoped>
.settings-page {
  max-width: 1200px;
}

.mb-card {
  margin-bottom: 24px;
}

.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
}

.setting-hint {
  margin-left: 12px;
  font-size: 12px;
  color: #bbb;
}

.actions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.actions-list .action-btn {
  width: 100%;
  justify-content: center;
}
</style>
