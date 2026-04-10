<template>
  <div class="app-layout">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 6H20V18H4V6Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M4 9H20" stroke="currentColor" stroke-width="1.5"/>
            <circle cx="6.5" cy="7.5" r="0.5" fill="currentColor"/>
            <circle cx="8.5" cy="7.5" r="0.5" fill="currentColor"/>
            <circle cx="10.5" cy="7.5" r="0.5" fill="currentColor"/>
            <path d="M9 13L11 15L15 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <transition name="fade">
          <div v-if="!sidebarCollapsed" class="logo-text">
            <h1>智慧影院</h1>
            <p>行为检测系统</p>
          </div>
        </transition>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in visibleMenuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActiveRoute(item.path) }"
        >
          <el-icon :size="20"><component :is="item.icon" /></el-icon>
          <transition name="fade">
            <span v-if="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
          </transition>
          <transition name="fade">
            <el-badge
              v-if="!sidebarCollapsed && item.badge && item.badge() > 0"
              :value="item.badge()"
              :max="99"
              class="nav-badge"
            />
          </transition>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <el-icon :size="18">
            <DArrowLeft v-if="!sidebarCollapsed" />
            <DArrowRight v-else />
          </el-icon>
        </div>
      </div>
    </aside>

    <div class="main-area">
      <header class="topbar">
        <div class="topbar-left">
          <h2 class="page-title">{{ currentPageTitle }}</h2>
        </div>
        <div class="topbar-right">
          <div class="topbar-actions">
            <el-tooltip content="报警通知" placement="bottom">
              <div class="action-btn" @click="$router.push('/alarms')">
                <el-badge :value="pendingCount" :max="99" :hidden="pendingCount === 0">
                  <el-icon :size="20"><Bell /></el-icon>
                </el-badge>
              </div>
            </el-tooltip>
          </div>

          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-block">
              <div class="user-avatar">{{ avatarText }}</div>
              <div class="user-meta" v-if="!sidebarCollapsed">
                <span class="user-name">{{ authStore.username }}</span>
                <el-tag :type="roleTagType" size="small" effect="plain" round>{{ roleName }}</el-tag>
              </div>
              <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon> 系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="page-content">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'
import {
  ROLE_ADMIN,
  ROLE_MANAGER,
  roleLabel,
  roleTag
} from '../constants/roles'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const sidebarCollapsed = ref(false)
const pendingCount = computed(() => authStore.pendingAlarmCount)

const menuItems = [
  { path: '/', label: '仪表盘', icon: 'DataAnalysis', roles: null },
  { path: '/monitor', label: '视频识别', icon: 'Monitor', roles: null },
  { path: '/alarms', label: '报警管理', icon: 'Bell', roles: null, badge: () => authStore.pendingAlarmCount },
  { path: '/cinemas', label: '影院管理', icon: 'OfficeBuilding', roles: [ROLE_ADMIN] },
  { path: '/users', label: '用户管理', icon: 'User', roles: [ROLE_ADMIN, ROLE_MANAGER] },
  { path: '/roles', label: '角色管理', icon: 'Setting', roles: [ROLE_ADMIN] },
  { path: '/settings', label: '系统设置', icon: 'Setting', roles: null },
]

const visibleMenuItems = computed(() =>
  menuItems.filter(item =>
    !item.roles || item.roles.includes(authStore.userRole)
  )
)

const currentPageTitle = computed(() => {
  const item = menuItems.find(m => m.path === route.path)
  return item?.label || '页面'
})

const isActiveRoute = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const avatarText = computed(() => {
  const name = authStore.user?.real_name || authStore.username
  return name ? name.charAt(0).toUpperCase() : 'U'
})

const roleName = computed(() => {
  return roleLabel(authStore.userRole)
})

const roleTagType = computed(() => {
  return roleTag(authStore.userRole)
})

const handleCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } else if (command === 'settings') {
    router.push('/settings')
  }
}
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background: #faf9fc;
}

/* ===== Sidebar ===== */
.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #f8f0ff 0%, #faf5ff 50%, #f5f0ff 100%);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
  overflow: hidden;
  border-right: 1px solid #ede5f5;
}
.sidebar.collapsed {
  width: 72px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px;
  border-bottom: 1px solid #ede5f5;
}
.logo-icon {
  width: 40px;
  height: 40px;
  min-width: 40px;
  background: linear-gradient(135deg, #d084d0 0%, #a78bdb 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}
.logo-icon svg {
  width: 22px;
  height: 22px;
}
.logo-text h1 {
  font-size: 16px;
  font-weight: 700;
  color: #7c3aed;
  white-space: nowrap;
  line-height: 1.3;
}
.logo-text p {
  font-size: 11px;
  color: #a78bdb;
  white-space: nowrap;
}

/* ===== Navigation ===== */
.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  color: #9380c5;
  text-decoration: none;
  transition: all 0.2s ease;
  position: relative;
  font-size: 14px;
  white-space: nowrap;
}
.nav-item:hover {
  color: #7c3aed;
  background: rgba(208, 132, 208, 0.08);
}
.nav-item.active {
  color: #7c3aed;
  background: linear-gradient(135deg, rgba(208, 132, 208, 0.15) 0%, rgba(167, 139, 219, 0.1) 100%);
  box-shadow: 0 2px 8px rgba(208, 132, 208, 0.15);
}
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: #d084d0;
  border-radius: 0 3px 3px 0;
}

.nav-badge {
  margin-left: auto;
}

/* ===== Sidebar Footer ===== */
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid #ede5f5;
}
.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 36px;
  border-radius: 8px;
  color: #a78bdb;
  cursor: pointer;
  transition: all 0.2s;
}
.collapse-btn:hover {
  color: #7c3aed;
  background: rgba(208, 132, 208, 0.08);
}

/* ===== Main Area ===== */
.main-area {
  --sidebar-w: 240px;
  flex: 1;
  margin-left: var(--sidebar-w);
  width: calc(100vw - var(--sidebar-w));
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-width: 0;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.sidebar.collapsed ~ .main-area {
  --sidebar-w: 72px;
}

/* ===== Top Bar ===== */
.topbar {
  height: 64px;
  background: linear-gradient(90deg, #fff 0%, #faf5ff 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  box-shadow: 0 1px 4px rgba(208, 132, 208, 0.08);
  position: sticky;
  top: 0;
  z-index: 50;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #7c3aed;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.action-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}
.action-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.user-block {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
}
.user-block:hover {
  background: #f5f5f5;
}

.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, #d084d0 0%, #a78bdb 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.user-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.user-name {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  line-height: 1.2;
}

.dropdown-arrow {
  color: #999;
  font-size: 12px;
}

/* ===== Page Content ===== */
.page-content {
  flex: 1;
  padding: 24px;
  min-width: 0;
  overflow-x: auto;
}

/* ===== Transitions ===== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.page-enter-active,
.page-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
