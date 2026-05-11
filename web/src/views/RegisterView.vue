<template>
  <div class="auth-shell">
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
          <p class="brand-lockup__kicker">笔灵: AI让文案随心而生</p>
          <h1 class="brand-lockup__name">{{ brandName }}</h1>
        </div>
      </div>

      <button class="ghost-link" type="button" @click="goToLogin">
        <span>已有账号</span>
        <ArrowRight :size="16" />
      </button>
    </header>

    <main class="auth-main">
      <section class="auth-intro">
        <h2 class="intro-title">注册账号，进入统一工作台</h2>
        <p class="intro-subtitle">新用户注册后默认进入普通用户路径，可直接访问社区和产品文案模块。</p>

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
            <p class="panel-label">Create Account</p>
            <h3>创建你的账号</h3>
          </div>

          <div class="form-body">
            <a-form :model="registerForm" @finish="handleRegister" layout="vertical">
              <a-form-item label="用户名" name="username" :rules="[{ required: true, message: '请输入用户名' }, { min: 2, message: '用户名至少2个字符' }]">
                <a-input v-model:value="registerForm.username" placeholder="请输入用户名" size="large" />
              </a-form-item>
              <a-form-item label="密码" name="password" :rules="[{ required: true, message: '请输入密码' }, { min: 6, message: '密码至少6个字符' }]">
                <a-input-password v-model:value="registerForm.password" placeholder="请输入密码" size="large" />
              </a-form-item>
              <a-form-item label="确认密码" name="confirmPassword" :rules="[{ required: true, message: '请确认密码' }, { validator: validateConfirmPassword }]">
                <a-input-password v-model:value="registerForm.confirmPassword" placeholder="请再次输入密码" size="large" />
              </a-form-item>

              <div class="policy-tip">
                <ShieldCheck :size="15" />
                <span>注册成功后使用用户名和密码登录系统。</span>
              </div>

              <a-button type="primary" html-type="submit" :loading="loading" class="primary-btn" block size="large">
                创建账号
              </a-button>

              <div class="form-switch">
                <span>已经有账号？</span>
                <button class="text-link" type="button" @click="goToLogin">立即登录</button>
              </div>
            </a-form>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useInfoStore } from '@/stores/info'
import { message } from 'ant-design-vue'
import { apiPost } from '@/apis/base'
import {
  ArrowLeft,
  ArrowRight,
  FileText,
  Globe2,
  FolderTree,
  ShieldCheck
} from 'lucide-vue-next'

const router = useRouter()
const infoStore = useInfoStore()

const brandName = computed(() =>
  infoStore.organization?.name || infoStore.branding?.name || 'BiLing'
)

const loading = ref(false)
const registerForm = reactive({ username: '', password: '', confirmPassword: '' })

const capItems = computed(() => [
  { icon: FileText, label: '产品文案生成' },
  { icon: Globe2, label: '社区协作' },
  { icon: FolderTree, label: '提示词管理' }
])

const validateConfirmPassword = async (rule, value) => {
  if (!value) throw new Error('请确认密码')
  if (value !== registerForm.password) throw new Error('两次输入的密码不一致')
}

const goToLogin = () => router.push('/login')
const goHome = () => router.push('/')

const handleRegister = async () => {
  if (registerForm.password !== registerForm.confirmPassword) {
    message.error('两次输入的密码不一致')
    return
  }
  if (registerForm.password.length < 6) {
    message.error('密码长度不能少于6位')
    return
  }

  loading.value = true
  try {
    const result = await apiPost('/api/auth/register', {
      username: registerForm.username,
      password: registerForm.password,
      confirm_password: registerForm.confirmPassword
    }, {}, false)

    if (result.success) {
      message.success('注册成功，请登录')
      router.push('/login')
    } else {
      message.error(result.detail || '注册失败')
    }
  } catch (error) {
    message.error(error.message || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await infoStore.loadInfoConfig()
})
</script>

<style lang="less" scoped>
.auth-shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(245, 158, 11, 0.14), transparent 24%),
    radial-gradient(circle at 88% 10%, rgba(37, 99, 235, 0.12), transparent 22%),
    linear-gradient(180deg, #fff9f2, #eef6ff 42%, #f9fbff 100%);
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

.policy-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 14px;
  color: #34506f;
  background: rgba(255, 255, 255, 0.36);
  border: 1px solid rgba(37, 99, 235, 0.1);
  font-size: 13px;
  margin-bottom: 6px;
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