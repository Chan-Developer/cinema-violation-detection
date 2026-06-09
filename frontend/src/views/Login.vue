<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="bg-shape shape-1"></div>
      <div class="bg-shape shape-2"></div>
      <div class="bg-shape shape-3"></div>
    </div>

    <div class="login-container">
      <div class="login-brand">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 6H20V18H4V6Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M4 9H20" stroke="currentColor" stroke-width="1.5"/>
            <circle cx="6.5" cy="7.5" r="0.5" fill="currentColor"/>
            <circle cx="8.5" cy="7.5" r="0.5" fill="currentColor"/>
            <circle cx="10.5" cy="7.5" r="0.5" fill="currentColor"/>
            <path d="M9 13L11 15L15 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h1>智慧影院行为检测系统</h1>
        <p>Cinema Behavior Detection System</p>
      </div>

      <el-card class="login-card">
        <el-form :model="form" :rules="rules" ref="formRef" size="large">
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              prefix-icon="User"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              @click="handleLogin"
              class="login-btn"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>

        <el-divider>演示账号</el-divider>
        <div class="demo-accounts">
          <div class="account-item" v-for="acc in demoAccounts" :key="acc.user" @click="quickLogin(acc)">
            <el-tag :type="acc.type" effect="light" round>{{ acc.role }}</el-tag>
            <span class="account-text">{{ acc.user }} / {{ acc.pass }}</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({ username: '', password: '' })

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const demoAccounts = [
  { role: '管理员', user: 'admin', pass: 'admin123', type: 'danger' as const },
  { role: '影院经理', user: 'manager1', pass: '123456', type: 'success' as const },
  { role: '监控员', user: 'operator1', pass: '123456', type: 'warning' as const },
  { role: '运维', user: 'tech1', pass: '123456', type: 'info' as const },
]

const quickLogin = (acc: typeof demoAccounts[0]) => {
  form.username = acc.user
  form.password = acc.pass
}

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await authStore.login(form.username, form.password)
      ElMessage.success('登录成功')
      const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
      router.push(redirect)
    } catch (e: any) {
      ElMessage.error(e.message || '登录失败，请检查用户名和密码')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 40%, #16213e 70%, #0f3460 100%);
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.bg-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
}
.shape-1 {
  width: 500px; height: 500px;
  background: #667eea;
  top: -15%; left: -10%;
  animation: float 15s ease-in-out infinite;
}
.shape-2 {
  width: 400px; height: 400px;
  background: #764ba2;
  bottom: -10%; right: -5%;
  animation: float 20s ease-in-out infinite reverse;
}
.shape-3 {
  width: 300px; height: 300px;
  background: #f093fb;
  top: 50%; left: 60%;
  animation: float 12s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(30px, -30px); }
  66% { transform: translate(-20px, 20px); }
}

.login-container {
  position: relative;
  z-index: 1;
  width: 420px;
}

.login-brand {
  text-align: center;
  margin-bottom: 32px;
}
.brand-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.35);
}
.brand-icon svg {
  width: 32px; height: 32px;
}
.login-brand h1 {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 6px;
  letter-spacing: 1px;
}
.login-brand p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.45);
  letter-spacing: 0.5px;
}

.login-card {
  border-radius: 16px !important;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.05) !important;
  backdrop-filter: blur(20px);
}

.login-btn {
  width: 100%;
  height: 46px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  letter-spacing: 2px;
}
.login-btn:hover {
  background: linear-gradient(135deg, #5a6fd6 0%, #6a4293 100%);
}

.demo-accounts {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.account-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}
.account-item:hover {
  background: #f5f7fa;
}
.account-text {
  font-size: 13px;
  color: #666;
  font-family: 'SF Mono', 'Fira Code', monospace;
}
</style>
