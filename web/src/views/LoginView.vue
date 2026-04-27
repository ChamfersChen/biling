<template>
  <div class="auth-shell" :class="{ 'has-alert': serverStatus === 'error' }">
    <div v-if="serverStatus === 'error'" class="service-alert">
      <div class="service-alert__content">
        <AlertTriangle :size="18" />
        <div class="service-alert__copy">
          <strong>服务连接异常</strong>
          <span>{{ serverError }}</span>
        </div>
        <a-button type="link" size="small" :loading="healthChecking" @click="checkServerHealth">重试</a-button>
      </div>
    </div>

    <header class="auth-header">
      <button class="ghost-link" type="button" @click="goHome">
        <ArrowLeft :size="16" />
        <span>返回首页</span>
      </button>

      <div class="brand-lockup">
        <img
          v-if="infoStore.organization?.logo"
          :src="infoStore.organization.logo"
          :alt="brandName"
          class="brand-lockup__logo"
        />
        <div>
          <p class="brand-lockup__kicker">Prompt Workspace</p>
          <h1 class="brand-lockup__name">{{ brandName }}</h1>
        </div>
      </div>

      <button v-if="!isFirstRun" class="ghost-link" type="button" @click="goToRegister">
        <span>注册新账号</span>
        <ArrowRight :size="16" />
      </button>
      <div v-else class="ghost-link ghost-link--static">
        <ShieldCheck :size="16" />
        <span>初始化模式</span>
      </div>
    </header>

    <main class="auth-main">
      <section class="auth-hero">
        <div class="hero-badge">
          <Sparkles :size="16" />
          <span>{{ isFirstRun ? 'System Setup' : 'Unified AI Workspace' }}</span>
        </div>

        <h2 class="hero-title">
          {{ isFirstRun ? '先创建超级管理员，再开始管理提示词、社区内容和产品工作流。' : '登录后继续你的提示词资产、社区协作与产品文案生成流程。' }}
        </h2>

        <p class="hero-subtitle">
          {{ isFirstRun ? '系统检测到首次启动，当前需要完成管理员初始化。' : brandSubtitle }}
        </p>

        <div class="hero-panel hero-panel--story">
          <p class="panel-label">平台能力</p>
          <div class="feature-list">
            <article class="feature-item" v-for="item in featureList" :key="item.title">
              <component :is="item.icon" :size="18" class="feature-item__icon" />
              <div>
                <h3>{{ item.title }}</h3>
                <p>{{ item.description }}</p>
              </div>
            </article>
          </div>
        </div>

        <div class="hero-stats">
          <div class="stat-card" v-for="item in heroStats" :key="item.label">
            <p class="stat-card__value">{{ item.value }}</p>
            <p class="stat-card__label">{{ item.label }}</p>
            <p class="stat-card__note">{{ item.note }}</p>
          </div>
        </div>
      </section>

      <section class="auth-panel">
        <div class="auth-card">
          <div class="auth-card__top">
            <div>
              <p class="panel-label">{{ isFirstRun ? 'Initialize' : 'Welcome Back' }}</p>
              <h3 class="auth-card__title">{{ isFirstRun ? '创建首个管理员账户' : '登录到工作台' }}</h3>
              <p class="auth-card__desc">
                {{ isFirstRun ? '管理员将拥有提示词管理、组织配置与权限治理入口。' : brandDescription }}
              </p>
            </div>

            <div class="status-pill" :class="`status-pill--${serverStatus}`">
              <span class="status-dot"></span>
              <span>{{ serverStatusLabel }}</span>
            </div>
          </div>

          <div class="auth-card__meta">
            <div class="meta-chip">
              <Bot :size="16" />
              <span>产品文案 + 单条生图</span>
            </div>
            <div class="meta-chip">
              <FolderTree :size="16" />
              <span>提示词目录与社区发布</span>
            </div>
          </div>

          <div class="auth-card__body">
            <div v-if="isFirstRun" class="auth-form auth-form--init">
              <a-form :model="adminForm" @finish="handleInitialize" layout="vertical">
                <a-form-item
                  label="用户ID"
                  name="user_id"
                  :rules="[
                    { required: true, message: '请输入用户ID' },
                    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户ID只能包含字母、数字和下划线' },
                    { min: 3, max: 20, message: '用户ID长度必须在3-20个字符之间' }
                  ]"
                >
                  <a-input v-model:value="adminForm.user_id" placeholder="如 super_admin" :maxlength="20" />
                </a-form-item>

                <a-form-item
                  label="手机号（可选）"
                  name="phone_number"
                  :rules="[
                    {
                      validator: async (rule, value) => {
                        if (!value || value.trim() === '') {
                          return
                        }
                        const phoneRegex = /^1[3-9]\d{9}$/
                        if (!phoneRegex.test(value)) {
                          throw new Error('请输入正确的手机号格式')
                        }
                      }
                    }
                  ]"
                >
                  <a-input v-model:value="adminForm.phone_number" placeholder="可作为补充登录标识" :maxlength="11" />
                </a-form-item>

                <a-form-item label="密码" name="password" :rules="[{ required: true, message: '请输入密码' }]">
                  <a-input-password v-model:value="adminForm.password" />
                </a-form-item>

                <a-form-item
                  label="确认密码"
                  name="confirmPassword"
                  :rules="[
                    { required: true, message: '请确认密码' },
                    { validator: validateConfirmPassword }
                  ]"
                >
                  <a-input-password v-model:value="adminForm.confirmPassword" />
                </a-form-item>

                <a-form-item>
                  <a-button type="primary" html-type="submit" :loading="loading" class="primary-btn" block>
                    创建管理员账户
                  </a-button>
                </a-form-item>
              </a-form>
            </div>

            <div v-else class="auth-form">
              <a-form :model="loginForm" @finish="handleLogin" layout="vertical">
                <a-form-item
                  label="登录账号"
                  name="loginId"
                  :rules="[{ required: true, message: '请输入用户ID或手机号' }]"
                >
                  <a-input v-model:value="loginForm.loginId" placeholder="用户ID或手机号" />
                </a-form-item>

                <a-form-item
                  label="密码"
                  name="password"
                  :rules="[{ required: true, message: '请输入密码' }]"
                >
                  <a-input-password v-model:value="loginForm.password" />
                </a-form-item>

                <div class="form-row">
                  <a-checkbox v-model:checked="rememberMe">记住我</a-checkbox>
                  <span class="muted-tip">支持用户ID或手机号登录</span>
                </div>

                <a-form-item>
                  <a-button
                    type="primary"
                    html-type="submit"
                    :loading="loading"
                    :disabled="isLocked"
                    class="primary-btn"
                    block
                    size="large"
                  >
                    <span v-if="isLocked">账户已锁定 {{ formatTime(lockRemainingTime) }}</span>
                    <span v-else>登录并进入工作台</span>
                  </a-button>
                </a-form-item>

                <div class="switch-row">
                  <span>还没有账号？</span>
                  <button class="text-link" type="button" @click="goToRegister">立即注册</button>
                </div>
              </a-form>
            </div>

            <div v-if="errorMessage" class="feedback feedback--error">
              <AlertTriangle :size="16" />
              <span>{{ errorMessage }}</span>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useInfoStore } from '@/stores/info'
import { message } from 'ant-design-vue'
import { healthApi } from '@/apis/system_api'
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Bot,
  FolderTree,
  Globe2,
  ShieldCheck,
  Sparkles,
  Wand2
} from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()
const infoStore = useInfoStore()

const brandName = computed(() => {
  const orgName = infoStore.organization?.name?.trim() || ''
  const brandNameRaw = infoStore.branding?.name?.trim() || 'Prompta'
  if (orgName && brandNameRaw && orgName !== brandNameRaw) {
    return brandNameRaw
  }
  return orgName || brandNameRaw
})

const brandSubtitle = computed(() => {
  return infoStore.branding?.subtitle?.trim() || '面向运营、内容与业务团队的统一 AI 工作台。'
})

const brandDescription = computed(() => {
  return infoStore.branding?.description?.trim() || '连接提示词资产、社区协作和产品内容生成。'
})

const isFirstRun = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const rememberMe = ref(false)
const serverStatus = ref('loading')
const serverError = ref('')
const healthChecking = ref(false)
const isLocked = ref(false)
const lockRemainingTime = ref(0)
const lockCountdown = ref(null)

const loginForm = reactive({
  loginId: '',
  password: ''
})

const adminForm = reactive({
  user_id: '',
  password: '',
  confirmPassword: '',
  phone_number: ''
})

const serverStatusLabel = computed(() => {
  if (serverStatus.value === 'ok') return '服务正常'
  if (serverStatus.value === 'error') return '服务异常'
  return '检查中'
})

const featureList = computed(() => [
  { icon: FolderTree, title: '提示词资产管理', description: '维护目录树、变量、测试流程，并发布到社区。' },
  { icon: Globe2, title: '社区协作', description: '浏览分类、沉淀可共享内容并复用已发布提示词。' },
  { icon: Wand2, title: '产品文案生成', description: '支持已存产品复用、历史回看和单条结果生图。' }
])

const heroStats = computed(() => [
  { label: '核心能力', value: '3', note: '社区、提示词、产品文案' },
  { label: '订阅档位', value: '3', note: 'free / pro / enterprise' },
  { label: '生成链路', value: 'Closed Loop', note: '文案、图片提示词与图片结果串联' }
])

const goHome = () => {
  router.push('/')
}

const goToRegister = () => {
  router.push('/register')
}

const clearLockCountdown = () => {
  if (lockCountdown.value) {
    clearInterval(lockCountdown.value)
    lockCountdown.value = null
  }
}

const startLockCountdown = (remainingSeconds) => {
  clearLockCountdown()
  isLocked.value = true
  lockRemainingTime.value = remainingSeconds

  lockCountdown.value = setInterval(() => {
    lockRemainingTime.value--
    if (lockRemainingTime.value <= 0) {
      clearLockCountdown()
      isLocked.value = false
      errorMessage.value = ''
    }
  }, 1000)
}

const formatTime = (seconds) => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}分${remainingSeconds}秒`
  }
  if (seconds < 86400) {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}小时${minutes}分钟`
  }
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  return `${days}天${hours}小时`
}

const validateConfirmPassword = async (rule, value) => {
  if (value === '') {
    throw new Error('请确认密码')
  }
  if (value !== adminForm.password) {
    throw new Error('两次输入的密码不一致')
  }
}

const handleLogin = async () => {
  if (isLocked.value) {
    message.warning(`账户被锁定，请等待 ${formatTime(lockRemainingTime.value)}`)
    return
  }

  try {
    loading.value = true
    errorMessage.value = ''
    clearLockCountdown()

    await userStore.login({
      loginId: loginForm.loginId,
      password: loginForm.password,
      rememberMe: rememberMe.value
    })

    message.success('登录成功')
    const redirectPath = sessionStorage.getItem('redirect') || '/extensions/prompts'
    sessionStorage.removeItem('redirect')

    if (redirectPath === '/') {
      router.push('/extensions/prompts')
    } else {
      try {
      router.push(redirectPath)
      } catch (error) {
        console.error('跳转失败:', error)
        router.push('/extensions/prompts')
      }
    }
  } catch (error) {
    console.error('登录失败:', error)
    if (error.status === 423) {
      let remainingTime = 0
      if (error.headers && error.headers.get) {
        const lockRemainingHeader = error.headers.get('X-Lock-Remaining')
        if (lockRemainingHeader) {
          remainingTime = parseInt(lockRemainingHeader)
        }
      }
      if (remainingTime === 0) {
        const lockTimeMatch = error.message.match(/(\d+)\s*秒/)
        if (lockTimeMatch) {
          remainingTime = parseInt(lockTimeMatch[1])
        }
      }
      if (remainingTime > 0) {
        startLockCountdown(remainingTime)
        errorMessage.value = `由于多次登录失败，账户已被锁定 ${formatTime(remainingTime)}`
      } else {
        errorMessage.value = error.message || '账户被锁定，请稍后再试'
      }
    } else {
      errorMessage.value = error.message || '登录失败，请检查用户名和密码'
    }
  } finally {
    loading.value = false
  }
}

const handleInitialize = async () => {
  try {
    loading.value = true
    errorMessage.value = ''
    if (adminForm.password !== adminForm.confirmPassword) {
      errorMessage.value = '两次输入的密码不一致'
      return
    }
    await userStore.initialize({
      user_id: adminForm.user_id,
      password: adminForm.password,
      phone_number: adminForm.phone_number || null
    })
    message.success('管理员账户创建成功')
    router.push('/')
  } catch (error) {
    console.error('初始化失败:', error)
    errorMessage.value = error.message || '初始化失败，请重试'
  } finally {
    loading.value = false
  }
}

const checkFirstRunStatus = async () => {
  try {
    loading.value = true
    isFirstRun.value = await userStore.checkFirstRun()
  } catch (error) {
    console.error('检查首次运行状态失败:', error)
    errorMessage.value = '系统出错，请稍后重试'
  } finally {
    loading.value = false
  }
}

const checkServerHealth = async () => {
  try {
    healthChecking.value = true
    const response = await healthApi.checkHealth()
    if (response.status === 'ok') {
      serverStatus.value = 'ok'
      return
    }
    serverStatus.value = 'error'
    serverError.value = response.message || '服务端状态异常'
  } catch (error) {
    console.error('检查服务器健康状态失败:', error)
    serverStatus.value = 'error'
    serverError.value = error.message || '无法连接到服务端，请检查网络连接'
  } finally {
    healthChecking.value = false
  }
}

onMounted(async () => {
  rememberMe.value = !!localStorage.getItem('user_token')
  await infoStore.loadInfoConfig()

  if (userStore.isLoggedIn) {
    router.push('/')
    return
  }

  await checkServerHealth()
  await checkFirstRunStatus()
})

onUnmounted(() => {
  clearLockCountdown()
})
</script>

<style lang="less" scoped>
.auth-shell {
  min-height: 100vh;
  color: #172033;
  background:
    radial-gradient(circle at 10% 10%, rgba(245, 158, 11, 0.2), transparent 24%),
    radial-gradient(circle at 88% 16%, rgba(37, 99, 235, 0.18), transparent 26%),
    linear-gradient(180deg, #fff9f2, #eef6ff 45%, #f8fbff 100%);
}

.service-alert {
  padding: 12px 18px 0;
}

.service-alert__content {
  width: min(1280px, 100%);
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 18px;
  background: rgba(255, 244, 229, 0.8);
  border: 1px solid rgba(217, 119, 6, 0.22);
  color: #9a3412;
}

.service-alert__copy {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.auth-header {
  width: min(1280px, calc(100% - 28px));
  margin: 0 auto;
  padding: 22px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand-lockup {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-lockup__logo {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  object-fit: contain;
}

.brand-lockup__kicker,
.panel-label {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #d97706;
}

.brand-lockup__name {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
}

.ghost-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 42px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(37, 99, 235, 0.14);
  background: rgba(255, 255, 255, 0.44);
  color: #34506f;
  cursor: pointer;
}

.ghost-link--static {
  cursor: default;
}

.auth-main {
  width: min(1280px, calc(100% - 28px));
  margin: 0 auto;
  padding: 18px 0 36px;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(400px, 0.95fr);
  gap: 22px;
}

.auth-hero,
.auth-card {
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.38);
  border: 1px solid rgba(255, 255, 255, 0.56);
  box-shadow: 0 24px 52px rgba(27, 52, 92, 0.12);
  backdrop-filter: blur(18px);
}

.auth-hero {
  padding: 30px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-badge,
.status-pill,
.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.hero-badge {
  width: fit-content;
  color: #2563eb;
  background: rgba(37, 99, 235, 0.1);
}

.hero-title {
  margin: 0;
  font-size: clamp(34px, 4vw, 54px);
  line-height: 1.08;
  letter-spacing: -0.04em;
}

.hero-subtitle {
  margin: 0;
  max-width: 720px;
  font-size: 17px;
  line-height: 1.75;
  color: #52637d;
}

.hero-panel {
  padding: 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.48);
}

.feature-list {
  display: grid;
  gap: 12px;
}

.feature-item {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.28);
}

.feature-item__icon {
  color: #2563eb;
  margin-top: 2px;
}

.feature-item h3,
.auth-card__title {
  margin: 0 0 6px;
  color: #172033;
}

.feature-item p,
.auth-card__desc,
.stat-card__note,
.muted-tip {
  margin: 0;
  color: #60708a;
  line-height: 1.6;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.stat-card {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.32);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.stat-card__value {
  margin: 0 0 6px;
  font-size: 26px;
  font-weight: 800;
}

.stat-card__label {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 700;
}

.auth-panel {
  display: flex;
}

.auth-card {
  width: 100%;
  padding: 28px;
}

.auth-card__top,
.auth-card__meta,
.form-row,
.switch-row {
  display: flex;
  align-items: center;
}

.auth-card__top {
  justify-content: space-between;
  gap: 16px;
}

.auth-card__desc {
  max-width: 520px;
}

.status-pill {
  color: #52637d;
  background: rgba(255, 255, 255, 0.46);
  border: 1px solid rgba(37, 99, 235, 0.14);
}

.status-pill--ok {
  color: #166534;
  background: rgba(34, 197, 94, 0.12);
}

.status-pill--error {
  color: #b45309;
  background: rgba(245, 158, 11, 0.14);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
}

.auth-card__meta {
  gap: 10px;
  flex-wrap: wrap;
  margin: 20px 0 22px;
}

.meta-chip {
  color: #2563eb;
  background: rgba(37, 99, 235, 0.08);
}

.auth-card__body {
  padding: 22px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.28);
  border: 1px solid rgba(255, 255, 255, 0.48);
}

.form-row,
.switch-row {
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.switch-row {
  justify-content: center;
  margin-bottom: 0;
  color: #60708a;
}

.text-link {
  border: none;
  background: transparent;
  padding: 0;
  color: #2563eb;
  font-weight: 700;
  cursor: pointer;
}

.feedback {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 16px;
}

.feedback--error {
  color: #b45309;
  background: rgba(255, 244, 229, 0.72);
  border: 1px solid rgba(217, 119, 6, 0.2);
}

:deep(.primary-btn.ant-btn-primary) {
  min-height: 48px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #d97706, #2563eb);
  box-shadow: 0 16px 28px rgba(37, 99, 235, 0.18);
}

:deep(.primary-btn.ant-btn-primary:hover),
:deep(.primary-btn.ant-btn-primary:focus) {
  background: linear-gradient(135deg, #c26a05, #1f56c9);
}

:deep(.ant-input-affix-wrapper),
:deep(.ant-input),
:deep(.ant-input-password) {
  border-radius: 14px;
}

:deep(.ant-form-item-label > label) {
  color: #2d3d57;
  font-weight: 600;
}

@media (max-width: 1080px) {
  .auth-main,
  .hero-stats {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 820px) {
  .auth-header {
    flex-direction: column;
    align-items: stretch;
  }

  .brand-lockup {
    justify-content: center;
  }

  .hero-title {
    font-size: 34px;
  }

  .auth-hero,
  .auth-card {
    padding: 20px;
    border-radius: 24px;
  }

  .auth-card__top,
  .form-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
