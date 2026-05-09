<template>
  <div class="auth-shell" :class="{ 'has-alert': serverStatus === 'error' }">
    <div v-if="serverStatus === 'error'" class="service-alert">
      <div class="service-alert__content">
        <AlertTriangle :size="16" />
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
      <section class="auth-intro">
        <h2 class="intro-title">
          {{ isFirstRun ? '完成初始化，开始使用工作台' : '登录后直接进入产品文案与社区协作' }}
        </h2>
        <p class="intro-subtitle">
          {{ isFirstRun ? '系统检测到首次运行，需要先创建管理员账户。' : brandSubtitle }}
        </p>

        <div class="intro-capabilities">
          <div class="cap-item" v-for="item in capItems" :key="item.label">
            <component :is="item.icon" :size="18" />
            <span>{{ item.label }}</span>
          </div>
        </div>
      </section>

      <section class="auth-form-panel">
        <div class="form-card">
          <div class="form-card__header">
            <p class="panel-label">{{ isFirstRun ? 'Initialize' : 'Sign In' }}</p>
            <h3>{{ isFirstRun ? '创建管理员账户' : '登录到工作台' }}</h3>
          </div>

          <div v-if="isFirstRun" class="form-body">
            <a-form :model="adminForm" @finish="handleInitialize" layout="vertical">
              <a-form-item label="用户ID" name="user_id" :rules="[{ required: true, message: '请输入用户ID' }, { pattern: /^[a-zA-Z0-9_]+$/, message: '用户ID只能包含字母、数字和下划线' }, { min: 3, max: 20, message: '长度3-20个字符' }]">
                <a-input v-model:value="adminForm.user_id" placeholder="如 super_admin" :maxlength="20" />
              </a-form-item>
              <a-form-item label="手机号（可选）" name="phone_number" :rules="[{ validator: async (rule, value) => { if (!value || !value.trim()) return; if (!/^1[3-9]\d{9}$/.test(value)) throw new Error('格式不正确'); } }]">
                <a-input v-model:value="adminForm.phone_number" placeholder="选填" :maxlength="11" />
              </a-form-item>
              <a-form-item label="密码" name="password" :rules="[{ required: true, message: '请输入密码' }]">
                <a-input-password v-model:value="adminForm.password" />
              </a-form-item>
              <a-form-item label="确认密码" name="confirmPassword" :rules="[{ required: true, message: '请确认密码' }, { validator: validateConfirmPassword }]">
                <a-input-password v-model:value="adminForm.confirmPassword" />
              </a-form-item>
              <a-button type="primary" html-type="submit" :loading="loading" class="primary-btn" block size="large">
                创建管理员账户
              </a-button>
            </a-form>
          </div>

          <div v-else class="form-body">
            <a-form :model="loginForm" @finish="handleLogin" layout="vertical">
              <a-form-item label="登录账号" name="loginId" :rules="[{ required: true, message: '请输入用户ID或手机号' }]">
                <a-input v-model:value="loginForm.loginId" placeholder="用户ID或手机号" size="large" />
              </a-form-item>
              <a-form-item label="密码" name="password" :rules="[{ required: true, message: '请输入密码' }]">
                <a-input-password v-model:value="loginForm.password" size="large" />
              </a-form-item>
              <div class="form-row">
                <a-checkbox v-model:checked="rememberMe">记住我</a-checkbox>
              </div>
              <a-button
                type="primary"
                html-type="submit"
                :loading="loading"
                :disabled="isLocked"
                class="primary-btn"
                block
                size="large"
              >
                {{ isLocked ? `账户已锁定 ${formatTime(lockRemainingTime)}` : '登录并进入工作台' }}
              </a-button>
              <div class="form-switch">
                <span>还没有账号？</span>
                <button class="text-link" type="button" @click="goToRegister">立即注册</button>
              </div>
            </a-form>
          </div>

          <div v-if="errorMessage" class="feedback feedback--error">
            <AlertTriangle :size="15" />
            <span>{{ errorMessage }}</span>
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
  FileText,
  FolderTree,
  Globe2,
  ShieldCheck,
  Sparkles
} from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()
const infoStore = useInfoStore()

const brandName = computed(() => {
  const org = infoStore.organization?.name?.trim() || ''
  const brand = infoStore.branding?.name?.trim() || 'Prompta'
  return org || brand
})

const brandSubtitle = computed(() =>
  infoStore.branding?.subtitle?.trim() || '围绕产品文案生成、提示词管理和社区协作的统一工作台。'
)

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

const loginForm = reactive({ loginId: '', password: '' })
const adminForm = reactive({ user_id: '', password: '', confirmPassword: '', phone_number: '' })

const capItems = computed(() => [
  { icon: FileText, label: '产品文案生成' },
  { icon: Globe2, label: '社区协作' },
  { icon: FolderTree, label: '提示词管理' }
])

const goHome = () => router.push('/')
const goToRegister = () => router.push('/register')

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
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分钟`
  return `${Math.floor(seconds / 86400)}天${Math.floor((seconds % 86400) / 3600)}小时`
}

const validateConfirmPassword = async (rule, value) => {
  if (!value) throw new Error('请确认密码')
  if (value !== adminForm.password) throw new Error('两次输入的密码不一致')
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
    await userStore.login({ loginId: loginForm.loginId, password: loginForm.password, rememberMe: rememberMe.value })
    message.success('登录成功')
    const redirectPath = sessionStorage.getItem('redirect') || '/product-content/generate'
    sessionStorage.removeItem('redirect')
    if (redirectPath === '/') {
      router.push('/product-content/generate')
    } else {
      try {
        router.push(redirectPath)
      } catch {
        router.push('/product-content/generate')
      }
    }
  } catch (error) {
    if (error.status === 423) {
      let remainingTime = 0
      const lockHeader = error.headers?.get?.('X-Lock-Remaining')
      if (lockHeader) remainingTime = parseInt(lockHeader)
      if (!remainingTime) {
        const match = error.message.match(/(\d+)\s*秒/)
        if (match) remainingTime = parseInt(match[1])
      }
      if (remainingTime > 0) {
        startLockCountdown(remainingTime)
        errorMessage.value = `账户已被锁定 ${formatTime(remainingTime)}`
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
    await userStore.initialize({ user_id: adminForm.user_id, password: adminForm.password, phone_number: adminForm.phone_number || null })
    message.success('管理员账户创建成功')
    router.push('/')
  } catch (error) {
    errorMessage.value = error.message || '初始化失败，请重试'
  } finally {
    loading.value = false
  }
}

const checkServerHealth = async () => {
  try {
    healthChecking.value = true
    const response = await healthApi.checkHealth()
    serverStatus.value = response.status === 'ok' ? 'ok' : 'error'
    if (serverStatus.value === 'error') serverError.value = response.message || '服务端状态异常'
  } catch (error) {
    serverStatus.value = 'error'
    serverError.value = error.message || '无法连接到服务端'
  } finally {
    healthChecking.value = false
  }
}

onMounted(async () => {
  rememberMe.value = !!localStorage.getItem('user_token')
  await infoStore.loadInfoConfig()
  if (userStore.isLoggedIn) { router.push('/'); return }
  await checkServerHealth()
  await checkFirstRunStatus()
})

const checkFirstRunStatus = async () => {
  try { isFirstRun.value = await userStore.checkFirstRun() } catch { isFirstRun.value = false }
}

onUnmounted(() => clearLockCountdown())
</script>

<style lang="less" scoped>
.auth-shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(245, 158, 11, 0.14), transparent 24%),
    radial-gradient(circle at 88% 10%, rgba(37, 99, 235, 0.12), transparent 22%),
    linear-gradient(180deg, #fff9f2, #eef6ff 42%, #f9fbff 100%);
}

.service-alert {
  padding: 12px 18px 0;
}

.service-alert__content {
  width: min(1200px, 100%);
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
  font-size: 13px;
}

.auth-header {
  width: min(1200px, calc(100% - 28px));
  margin: 0 auto;
  padding: 20px 0;
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
  width: 42px;
  height: 42px;
  border-radius: 12px;
  object-fit: contain;
}

.brand-lockup__kicker {
  margin: 0 0 2px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #60708a;
}

.brand-lockup__name {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #172033;
}

.ghost-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(37, 99, 235, 0.14);
  background: rgba(255, 255, 255, 0.44);
  color: #34506f;
  cursor: pointer;
}

.ghost-link--static { cursor: default; }

.auth-main {
  width: min(1200px, calc(100% - 28px));
  margin: 0 auto;
  padding: 12px 0 48px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(380px, 480px);
  gap: 20px;
  align-items: start;
}

.auth-intro,
.form-card {
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.38);
  border: 1px solid rgba(255, 255, 255, 0.56);
  box-shadow: 0 24px 52px rgba(27, 52, 92, 0.1);
  backdrop-filter: blur(18px);
}

.auth-intro {
  padding: 36px 34px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.intro-title {
  margin: 0;
  font-size: clamp(28px, 4vw, 42px);
  line-height: 1.12;
  letter-spacing: -0.03em;
  color: #172033;
}

.intro-subtitle {
  margin: 0;
  font-size: 16px;
  line-height: 1.7;
  color: #52637d;
  max-width: 560px;
}

.intro-capabilities {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
}

.cap-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  color: #2563eb;
  font-size: 13px;
  font-weight: 700;
}

.form-card {
  padding: 28px;
}

.form-card__header {
  margin-bottom: 20px;
}

.panel-label {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #d97706;
}

.form-card__header h3 {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  color: #172033;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.form-switch {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 6px;
  color: #60708a;
  font-size: 14px;
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
  margin-top: 14px;
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
  font-size: 13px;
}

:deep(.primary-btn.ant-btn-primary) {
  min-height: 48px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #d97706, #2563eb);
  box-shadow: 0 16px 28px rgba(37, 99, 235, 0.18);
  font-size: 15px;
  font-weight: 700;
}

:deep(.primary-btn.ant-btn-primary:hover) {
  background: linear-gradient(135deg, #c26a05, #1f56c9);
}

:deep(.ant-input),
:deep(.ant-input-affix-wrapper),
:deep(.ant-input-password) {
  border-radius: 14px;
}

:deep(.ant-form-item-label > label) {
  color: #2d3d57;
  font-weight: 600;
}

@media (max-width: 1024px) {
  .auth-main {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 820px) {
  .auth-header {
    flex-direction: column;
    align-items: stretch;
    padding: 16px 0;
  }

  .brand-lockup {
    justify-content: center;
  }

  .intro-title {
    font-size: 28px;
  }

  .auth-intro,
  .form-card {
    padding: 22px 20px;
    border-radius: 22px;
  }
}
</style>