import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue')
      },
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue')
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: () => import('../views/Monitor.vue')
      },
      {
        path: 'alarms',
        name: 'AlarmList',
        component: () => import('../views/AlarmList.vue')
      },
      {
        path: 'cinemas',
        name: 'CinemaManage',
        component: () => import('../views/CinemaManage.vue'),
        meta: { roles: ['admin', 'manager'] }
      },
      {
        path: 'cameras',
        name: 'CameraManage',
        component: () => import('../views/CameraManage.vue')
      },
      {
        path: 'users',
        name: 'UserManage',
        component: () => import('../views/UserManage.vue'),
        meta: { roles: ['admin'] }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue')
      },
      {
        path: 'detection',
        name: 'Detection',
        component: () => import('../views/Detection.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else if (to.meta.roles && userStr) {
    const user = JSON.parse(userStr)
    if (!(to.meta.roles as string[]).includes(user.role)) {
      next('/')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
