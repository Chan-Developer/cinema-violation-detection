<template>
  <div class="settings-page">
    <section class="hero-card">
      <div class="hero-main">
        <div class="hero-title">系统设置</div>
        <div class="hero-subtitle">统一管理账号信息、报警提醒与系统运行参数</div>
      </div>
      <div class="hero-tags">
        <el-tag :type="roleTagType" effect="dark" round>{{ roleName }}</el-tag>
        <el-tag type="info" round>v1.0.0</el-tag>
      </div>
    </section>

    <el-row :gutter="isMobile ? 12 : 20" class="settings-layout">
      <el-col :xs="24" :sm="24" :md="15" :lg="15">
        <el-card class="panel-card mb-card">
          <template #header>
            <div class="card-head">
              <el-icon :size="18"><User /></el-icon>
              <span>个人信息</span>
            </div>
          </template>
          <div class="profile-wrap">
            <el-avatar :size="56" class="profile-avatar">{{ userInitial }}</el-avatar>
            <div class="profile-meta">
              <div class="profile-name">{{ user?.real_name || user?.username || '-' }}</div>
              <div class="profile-sub">{{ user?.username || '-' }}</div>
            </div>
          </div>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">邮箱</span>
              <span class="value">{{ user?.email || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">手机</span>
              <span class="value">{{ user?.phone || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">角色</span>
              <span class="value"><el-tag :type="roleTagType" size="small" round>{{ roleName }}</el-tag></span>
            </div>
            <div class="info-item">
              <span class="label">所属影院</span>
              <span class="value">{{ user?.cinema_name || '-' }}</span>
            </div>
          </div>
        </el-card>

        <el-card class="panel-card">
          <template #header>
            <div class="card-head">
              <el-icon :size="18"><Bell /></el-icon>
              <span>报警推送设置</span>
            </div>
          </template>
          <div class="notify-list">
            <div class="notify-item">
              <div class="notify-text">
                <div class="notify-title">WebSocket 推送</div>
                <div class="notify-desc">实时接收报警状态变化和新告警</div>
              </div>
              <el-switch v-model="settings.wsEnabled" />
            </div>
            <div class="notify-item">
              <div class="notify-text">
                <div class="notify-title">声音提醒</div>
                <div class="notify-desc">有新告警时播放声音，避免遗漏</div>
              </div>
              <el-switch v-model="settings.soundEnabled" />
            </div>
            <div class="notify-item">
              <div class="notify-text">
                <div class="notify-title">桌面通知</div>
                <div class="notify-desc">在浏览器层面展示系统消息通知</div>
              </div>
              <el-switch v-model="settings.desktopNotify" />
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="9" :lg="9">
        <el-card class="panel-card mb-card">
          <template #header>
            <div class="card-head">
              <el-icon :size="18"><Operation /></el-icon>
              <span>快捷操作</span>
            </div>
          </template>
          <div class="actions-list">
            <el-button type="primary" class="action-btn" @click="initData">
              <el-icon><Refresh /></el-icon>
              <span>初始化演示数据</span>
            </el-button>
            <el-button type="warning" plain class="action-btn" @click="testNotification">
              <el-icon><Bell /></el-icon>
              <span>测试通知</span>
            </el-button>
            <el-button plain class="action-btn" @click="showAbout">
              <el-icon><InfoFilled /></el-icon>
              <span>关于系统</span>
            </el-button>
          </div>
        </el-card>

        <el-card class="panel-card">
          <template #header>
            <div class="card-head">
              <el-icon :size="18"><Monitor /></el-icon>
              <span>系统信息</span>
            </div>
          </template>
          <div class="sys-list">
            <div class="sys-item">
              <span class="k">系统版本</span>
              <span class="v"><el-tag size="small" round>v1.0.0</el-tag></span>
            </div>
            <div class="sys-item">
              <span class="k">前端框架</span>
              <span class="v">Vue 3 + Element Plus</span>
            </div>
            <div class="sys-item">
              <span class="k">后端框架</span>
              <span class="v">Flask + SQLAlchemy</span>
            </div>
            <div class="sys-item">
              <span class="k">数据库</span>
              <span class="v">SQLite</span>
            </div>
            <div class="sys-item">
              <span class="k">实时通信</span>
              <span class="v">Flask-SocketIO</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, ref, onMounted, onUnmounted } from 'vue'
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
const userInitial = computed(() => (user.value?.real_name || user.value?.username || 'U').slice(0, 1).toUpperCase())
const isMobile = ref(false)

const settings = reactive({ wsEnabled: true, soundEnabled: true, desktopNotify: true })

const handleResize = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

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
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
}

.hero-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  margin-bottom: 16px;
  border-radius: 14px;
  border: 1px solid #e4e8f2;
  background: linear-gradient(135deg, #f8fbff 0%, #f3f5ff 100%);
}

.hero-title {
  font-size: 22px;
  line-height: 1.2;
  font-weight: 700;
  color: #1f2937;
}

.hero-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: #667085;
}

.hero-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}

.settings-layout {
  align-items: stretch;
}

.panel-card {
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.mb-card {
  margin-bottom: 16px;
}

.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #334155;
}

.profile-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.profile-avatar {
  background: linear-gradient(135deg, #5b8ff9 0%, #6f5ef9 100%);
  color: #fff;
  font-weight: 700;
}

.profile-name {
  font-size: 16px;
  font-weight: 700;
  color: #111827;
}

.profile-sub {
  margin-top: 2px;
  font-size: 12px;
  color: #6b7280;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.info-item {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #eceff5;
  background: #fafbff;
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.info-item .label {
  color: #64748b;
  font-size: 12px;
}

.info-item .value {
  color: #1f2937;
  font-size: 13px;
  font-weight: 500;
  text-align: right;
}

.notify-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notify-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid #edf1f6;
  background: #fbfcff;
}

.notify-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.notify-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #6b7280;
}

.actions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.actions-list .action-btn {
  width: 100%;
  justify-content: flex-start;
  height: 40px;
  border-radius: 10px;
}

.sys-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sys-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #eef2f6;
}

.sys-item .k {
  color: #64748b;
  font-size: 12px;
}

.sys-item .v {
  color: #1f2937;
  font-size: 13px;
  font-weight: 500;
  text-align: right;
}

@media (max-width: 768px) {
  .hero-card {
    flex-direction: column;
    align-items: flex-start;
    padding: 14px;
    margin-bottom: 12px;
  }

  .hero-title {
    font-size: 18px;
  }

  .hero-subtitle {
    font-size: 12px;
  }

  .settings-page {
    max-width: 100%;
  }

  .mb-card {
    margin-bottom: 12px;
  }

  .profile-wrap {
    margin-bottom: 10px;
  }

  .info-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .card-head {
    font-size: 14px;
  }

  .notify-item {
    align-items: flex-start;
  }

  .actions-list .action-btn {
    justify-content: center;
  }
}
</style>
