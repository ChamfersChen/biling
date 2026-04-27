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
          <p class="brand-lockup__kicker">Prompt Workspace</p>
          <h1 class="brand-lockup__name">{{ brandName }}</h1>
        </div>
      </div>

      <button class="ghost-link" type="button" @click="goToLogin">
        <span>已有账号</span>
        <ArrowRight :size="16" />
      </button>
    </header>

    <main class="auth-main">
      <section class="auth-hero">
        <div class="hero-badge">
          <Sparkles :size="16" />
          <span>Workspace Onboarding</span>
        </div>

        <h2 class="hero-title">创建账号后，直接进入社区与产品文案生成的统一工作台。</h2>
        <p class="hero-subtitle">{{ brandSubtitle }}</p>

        <div class="hero-panel">
          <p class="panel-label">适合谁使用</p>
          <div class="persona-list">
            <article class="persona-item" v-for="item in personaList" :key="item.title">
              <component :is="item.icon" :size="18" class="persona-item__icon" />
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
              <p class="panel-label">Create Account</p>
              <h3 class="auth-card__title">注册你的工作台账号</h3>
              <p class="auth-card__desc">新用户注册后默认进入普通用户路径，可直接访问社区与产品文案模块。</p>
            </div>
            <div class="status-chip">
              <ShieldCheck :size="16" />
              <span>默认用户角色</span>
            </div>
          </div>

          <div class="auth-card__meta">
            <div class="meta-chip">
              <Globe2 :size="16" />
              <span>社区内容可直接访问</span>
            </div>
            <div class="meta-chip">
              <Wand2 :size="16" />
              <span>可进入产品文案生成与历史查看</span>
            </div>
          </div>

          <div class="auth-card__body">
            <a-form :model="registerForm" @finish="handleRegister" layout="vertical">
              <a-form-item
                label="用户名"
                name="username"
                :rules="[
                  { required: true, message: '请输入用户名' },
                  { min: 2, message: '用户名至少2个字符' }
                ]"
              >
                <a-input v-model:value="registerForm.username" placeholder="请输入用户名" />
              </a-form-item>

              <a-form-item
                label="密码"
                name="password"
                :rules="[
                  { required: true, message: '请输入密码' },
                  { min: 6, message: '密码至少6个字符' }
                ]"
              >
                <a-input-password v-model:value="registerForm.password" placeholder="请输入密码" />
              </a-form-item>

              <a-form-item
                label="确认密码"
                name="confirmPassword"
                :rules="[
                  { required: true, message: '请确认密码' },
                  { validator: validateConfirmPassword }
                ]"
              >
                <a-input-password v-model:value="registerForm.confirmPassword" placeholder="请再次输入密码" />
              </a-form-item>

              <div class="policy-tip">
                <BadgeCheck :size="16" />
                <span>注册成功后请使用刚创建的用户名和密码登录系统。</span>
              </div>

              <a-form-item>
                <a-button type="primary" html-type="submit" :loading="loading" class="primary-btn" block size="large">
                  创建账号
                </a-button>
              </a-form-item>

              <div class="switch-row">
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
  BadgeCheck,
  Globe2,
  LibraryBig,
  ShieldCheck,
  Sparkles,
  Users,
  Wand2
} from 'lucide-vue-next'

const router = useRouter()
const infoStore = useInfoStore()

const brandName = computed(() => infoStore.organization?.name || infoStore.branding?.name || 'Prompta')
const brandSubtitle = computed(() => infoStore.branding?.subtitle?.trim() || '让团队成员更快进入内容生产与提示词协作流程。')

const loading = ref(false)
const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const personaList = computed(() => [
  { icon: Users, title: '运营与内容团队', description: '直接使用产品文案与社区内容，加快内容交付。' },
  { icon: LibraryBig, title: '知识与提示词维护者', description: '在社区与提示词管理中沉淀可复用的内容资产。' },
  { icon: Wand2, title: '业务使用者', description: '按产品资料生成文案、回看历史结果并继续生图。' }
])

const heroStats = computed(() => [
  { label: '默认入口', value: '2', note: '社区、产品文案' },
  { label: '注册结果', value: 'Instant', note: '创建成功后即可登录' },
  { label: '角色路径', value: 'User', note: '普通用户默认不进入管理员模块' }
])

const validateConfirmPassword = async () => {
  if (registerForm.confirmPassword !== registerForm.password) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

const goToLogin = () => {
  router.push('/login')
}

const goHome = () => {
  router.push('/')
}

const handleRegister = async () => {
  if (!registerForm.username || !registerForm.password || !registerForm.confirmPassword) {
    message.error('请填写完整信息')
    return
  }
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
    const result = await apiPost(
      '/api/auth/register',
      {
        username: registerForm.username,
        password: registerForm.password,
        confirm_password: registerForm.confirmPassword
      },
      {},
      false
    )

    if (result.success) {
      message.success('注册成功，请登录')
      router.push('/login')
    } else {
      message.error(result.detail || '注册失败')
    }
  } catch (error) {
    console.error('注册失败:', error)
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
  color: #172033;
  background:
    radial-gradient(circle at 12% 10%, rgba(245, 158, 11, 0.18), transparent 22%),
    radial-gradient(circle at 86% 14%, rgba(37, 99, 235, 0.18), transparent 24%),
    linear-gradient(180deg, #fff9f2, #eef6ff 46%, #f8fbff 100%);
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

.auth-main {
  width: min(1280px, calc(100% - 28px));
  margin: 0 auto;
  padding: 18px 0 36px;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(420px, 0.95fr);
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
.status-chip,
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

.hero-subtitle,
.auth-card__desc,
.persona-item p,
.stat-card__note {
  margin: 0;
  color: #60708a;
  line-height: 1.72;
}

.hero-panel {
  padding: 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.48);
}

.persona-list {
  display: grid;
  gap: 12px;
}

.persona-item {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.28);
}

.persona-item__icon {
  color: #2563eb;
  margin-top: 2px;
}

.persona-item h3,
.auth-card__title {
  margin: 0 0 6px;
  color: #172033;
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

.auth-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.status-chip {
  color: #166534;
  background: rgba(34, 197, 94, 0.12);
}

.auth-card__meta {
  display: flex;
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

.policy-tip,
.switch-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.policy-tip {
  margin-bottom: 18px;
  padding: 12px 14px;
  border-radius: 16px;
  color: #34506f;
  background: rgba(255, 255, 255, 0.36);
  border: 1px solid rgba(37, 99, 235, 0.1);
}

.switch-row {
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

  .auth-card__top {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
