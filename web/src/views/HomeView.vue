<template>
  <div class="home-shell">
    <div v-if="isLoading" class="state-panel state-panel--center">
      <a-spin size="large" />
      <p>正在连接服务并加载品牌信息...</p>
    </div>

    <div v-else-if="error" class="state-panel state-panel--error">
      <a-result status="error" :title="error.title" :sub-title="error.message">
        <template #extra>
          <a-button type="primary" @click="retryLoad">重试</a-button>
        </template>
      </a-result>
    </div>

    <template v-else>
      <header class="site-header">
        <div class="brand-block">
          <img
            v-if="infoStore.organization.logo"
            :src="infoStore.organization.logo"
            :alt="infoStore.organization.name"
            class="brand-logo"
          />
          <div>
            <p class="brand-kicker">Prompt Workspace</p>
            <h1 class="brand-name">{{ infoStore.organization.name || infoStore.branding.name || 'Prompta' }}</h1>
          </div>
        </div>

        <nav class="top-nav">
          <button class="nav-link nav-link--button" type="button" @click="handleNav('/product-content/generate')">
            产品文案
          </button>
          <button class="nav-link nav-link--button" type="button" @click="handleNav('/community')">
            社区
          </button>
          <button class="nav-link nav-link--button" type="button" @click="handleNav('/extensions/prompts')">
            提示词管理
          </button>
        </nav>

        <div class="header-actions">
          <a href="https://github.com/ChamfersChen/biling" target="_blank" rel="noopener noreferrer" class="github-link">
            <Github :size="16" />
            <span>GitHub</span>
          </a>
          <UserInfoComponent :show-button="true" />
        </div>
      </header>

      <main class="home-main">
        <section class="hero-card">
          <div class="hero-copy">
            <p class="eyebrow">{{ infoStore.branding.name || 'Prompta' }}</p>
            <h2 class="hero-title">{{ infoStore.branding.subtitle || '高效内容生成与提示词管理' }}</h2>
            <p class="hero-subtitle">围绕产品文案生成、提示词管理与社区协作的核心能力，帮助团队快速产出高质量内容。</p>

            <div class="hero-actions">
              <button class="hero-btn hero-btn--primary" @click="handlePrimaryAction">
                {{ primaryActionLabel }}
              </button>
              <button v-if="userStore.isLoggedIn" class="hero-btn hero-btn--secondary" @click="router.push('/product-content/history')">
                查看生成记录
              </button>
            </div>
          </div>

          <div class="hero-stats">
            <div class="stats-card">
              <div class="stats-item">
                <span class="stats-num">3</span>
                <span class="stats-label">核心能力</span>
              </div>
              <div class="stats-divider" />
              <div class="stats-item">
                <span class="stats-num">3</span>
                <span class="stats-label">订阅档位</span>
              </div>
              <div class="stats-divider" />
              <div class="stats-item">
                <span class="stats-num">∞</span>
                <span class="stats-label">使用延展</span>
              </div>
            </div>
          </div>
        </section>

        <section class="entry-section">
          <h3 class="section-title">从这里开始</h3>
          <div class="entry-grid">
            <article class="entry-card" @click="handleNav('/product-content/generate')">
              <div class="entry-icon" style="background: linear-gradient(135deg, #fef3c7, #fde68a);">
                <FileText :size="22" color="#d97706" />
              </div>
              <div class="entry-body">
                <h4>产品文案</h4>
                <p>输入产品信息，选择风格与渠道，一键生成可用于发布的营销文案，并可直接生图。</p>
              </div>
              <span class="entry-arrow">
                <ArrowRight :size="16" />
              </span>
            </article>

            <article class="entry-card" @click="handleNav('/community')">
              <div class="entry-icon" style="background: linear-gradient(135deg, #dbeafe, #bfdbfe);">
                <Globe2 :size="22" color="#2563eb" />
              </div>
              <div class="entry-body">
                <h4>社区</h4>
                <p>浏览、发现和复用社区中的优质提示词与内容模板，参与交流与沉淀。</p>
              </div>
              <span class="entry-arrow">
                <ArrowRight :size="16" />
              </span>
            </article>

            <article class="entry-card" @click="handleNav('/extensions/prompts')">
              <div class="entry-icon" style="background: linear-gradient(135deg, #d1fae5, #a7f3d0);">
                <FolderTree :size="22" color="#059669" />
              </div>
              <div class="entry-body">
                <h4>提示词管理</h4>
                <p>管理员维护提示词资产，支持变量结构识别、测试与发布到社区。</p>
              </div>
              <span class="entry-arrow">
                <ArrowRight :size="16" />
              </span>
            </article>
          </div>
        </section>

        <section class="info-section" v-if="featureCards.length">
          <h3 class="section-title">系统说明</h3>
          <div class="info-grid">
            <article class="info-card" v-for="card in featureCards" :key="card.label">
              <div class="info-icon" v-if="card.icon">
                <component :is="card.icon" :size="18" />
              </div>
              <p class="info-value">{{ card.value || '--' }}</p>
              <p class="info-label">{{ card.label }}</p>
              <p class="info-desc">{{ card.description }}</p>
            </article>
          </div>
        </section>
      </main>

      <footer class="site-footer">
        <p>{{ infoStore.footer?.copyright || '© 2025 All rights reserved' }}</p>
      </footer>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useInfoStore } from '@/stores/info'
import { healthApi } from '@/apis/system_api'
import { Result, Button } from 'ant-design-vue'
import UserInfoComponent from '@/components/UserInfoComponent.vue'
import {
  ArrowRight,
  FileText,
  Globe2,
  FolderTree,
  Github,
  CheckCircle2,
  GitCommit,
  Star
} from 'lucide-vue-next'

const AResult = Result
const AButton = Button

const router = useRouter()
const userStore = useUserStore()
const infoStore = useInfoStore()

const isLoading = ref(true)
const error = ref(null)

const checkHealth = async () => {
  try {
    const response = await healthApi.checkHealth()
    if (response.status !== 'ok') {
      throw new Error('服务不可用')
    }
  } catch (e) {
    error.value = {
      title: '服务连接失败',
      message: '后端服务无法响应，请检查服务是否正常运行'
    }
    throw e
  }
}

const loadData = async () => {
  isLoading.value = true
  error.value = null
  try {
    await checkHealth()
    await infoStore.loadInfoConfig()
  } catch (e) {
    console.error('加载失败:', e)
  } finally {
    isLoading.value = false
  }
}

const retryLoad = () => {
  loadData()
}

const handleNav = (to) => {
  if (!userStore.isLoggedIn) {
    sessionStorage.setItem('redirect', to)
    router.push('/login')
    return
  }
  if (to === '/extensions/prompts' && !userStore.isAdmin) {
    router.push('/community')
    return
  }
  router.push(to)
}

const handlePrimaryAction = () => {
  if (!userStore.isLoggedIn) {
    sessionStorage.setItem('redirect', '/product-content/dashboard')
    router.push('/login')
    return
  }
  router.push('/product-content/dashboard')
}

const primaryActionLabel = computed(() => {
  return userStore.isLoggedIn ? '进入系统' : '登录并开始使用'
})

const iconKey = (value) => (typeof value === 'string' ? value.toLowerCase() : '')

const featureIconMap = {
  stars: Star,
  issues: CheckCircle2,
  resolved: CheckCircle2,
  commits: GitCommit,
  license: CheckCircle2,
  default: Star
}

const featureCards = computed(() => {
  const list = Array.isArray(infoStore.features) ? infoStore.features : []
  return list
    .map((item) => {
      if (typeof item === 'string') {
        return { label: item, value: '', description: '', icon: Star }
      }
      const key = iconKey(item.icon || item.type)
      return {
        label: item.label || item.name || '',
        value: item.value || '',
        description: item.description || '',
        icon: featureIconMap[key] || featureIconMap.default
      }
    })
    .filter((item) => item.label || item.value || item.description)
})

onMounted(() => {
  loadData()
})
</script>

<style lang="less" scoped>
.home-shell {
  min-height: 100vh;
  color: #172033;
  background:
    radial-gradient(circle at top left, rgba(245, 158, 11, 0.14), transparent 26%),
    radial-gradient(circle at 88% 10%, rgba(37, 99, 235, 0.12), transparent 22%),
    linear-gradient(180deg, #fff9f2, #eef6ff 42%, #f9fbff 100%);
}

.state-panel {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 16px;

  &--error {
    padding: 24px;
  }

  p {
    margin: 0;
    color: #60708a;
  }
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 28px;
  background: rgba(255, 255, 255, 0.44);
  border-bottom: 1px solid rgba(255, 255, 255, 0.56);
  backdrop-filter: blur(18px);
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-logo {
  width: 42px;
  height: 42px;
  object-fit: contain;
  border-radius: 12px;
}

.brand-kicker {
  margin: 0 0 2px;
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #60708a;
}

.brand-name {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #172033;
}

.top-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-link,
.github-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  color: #42526b;
  text-decoration: none;
  background: rgba(255, 255, 255, 0.46);
  border: 1px solid rgba(255, 255, 255, 0.56);
  transition: all 0.2s ease;
}

.nav-link--button {
  appearance: none;
  cursor: pointer;
}

.nav-link:hover,
.nav-link.router-link-active,
.github-link:hover {
  color: #2563eb;
  background: rgba(37, 99, 235, 0.1);
  border-color: rgba(37, 99, 235, 0.22);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.home-main {
  width: min(1100px, calc(100% - 32px));
  margin: 0 auto;
  padding: 32px 0 56px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-card,
.entry-section,
.info-section {
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.38);
  border: 1px solid rgba(255, 255, 255, 0.56);
  box-shadow: 0 24px 52px rgba(27, 52, 92, 0.1);
  backdrop-filter: blur(18px);
}

.hero-card {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.6fr);
  gap: 28px;
  padding: 36px;
  align-items: center;
}

.eyebrow {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #d97706;
}

.hero-title {
  margin: 0 0 16px;
  font-size: clamp(30px, 4vw, 48px);
  line-height: 1.1;
  letter-spacing: -0.03em;
  color: #172033;
}

.hero-subtitle {
  margin: 0 0 24px;
  max-width: 600px;
  font-size: 16px;
  line-height: 1.7;
  color: #4b5d79;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.hero-btn {
  min-height: 48px;
  padding: 0 24px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;

  &--primary {
    color: #fff;
    background: linear-gradient(135deg, #d97706, #2563eb);
    box-shadow: 0 16px 28px rgba(37, 99, 235, 0.18);
  }

  &--primary:hover {
    background: linear-gradient(135deg, #c26a05, #1f56c9);
  }

  &--secondary {
    color: #2563eb;
    background: rgba(255, 255, 255, 0.52);
    border-color: rgba(37, 99, 235, 0.18);
  }

  &--secondary:hover {
    background: rgba(37, 99, 235, 0.08);
  }
}

.stats-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.6), rgba(255, 255, 255, 0.3));
  border: 1px solid rgba(255, 255, 255, 0.8);
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stats-num {
  font-size: 32px;
  font-weight: 800;
  color: #172033;
}

.stats-label {
  font-size: 12px;
  color: #60708a;
}

.stats-divider {
  width: 1px;
  height: 40px;
  background: rgba(148, 163, 184, 0.24);
}

.entry-section,
.info-section {
  padding: 28px 32px;
}

.section-title {
  margin: 0 0 20px;
  font-size: 22px;
  font-weight: 800;
  color: #172033;
}

.entry-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.entry-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 22px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.entry-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 36px rgba(27, 52, 92, 0.14);
}

.entry-icon {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: grid;
  place-items: center;
}

.entry-body {
  flex: 1;
  min-width: 0;
}

.entry-body h4 {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 700;
  color: #172033;
}

.entry-body p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #60708a;
}

.entry-arrow {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.6);
  color: #60708a;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
}

.info-card {
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.34);
  border: 1px solid rgba(255, 255, 255, 0.52);
  backdrop-filter: blur(12px);
}

.info-icon {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(37, 99, 235, 0.08);
  color: #2563eb;
  margin-bottom: 12px;
}

.info-value {
  margin: 0 0 4px;
  font-size: 26px;
  font-weight: 800;
  color: #172033;
}

.info-label {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 700;
  color: #2d3d57;
}

.info-desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: #60708a;
}

.site-footer {
  padding: 0 24px 32px;
  text-align: center;
}

.site-footer p {
  margin: 0;
  color: #60708a;
}

@media (max-width: 1024px) {
  .hero-card {
    grid-template-columns: 1fr;
  }

  .stats-card {
    justify-content: center;
  }

  .entry-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .site-header {
    position: static;
    flex-direction: column;
    align-items: stretch;
    padding: 16px;
    gap: 12px;
  }

  .top-nav {
    flex-wrap: wrap;
    justify-content: center;
  }

  .header-actions {
    justify-content: center;
  }

  .home-main {
    padding: 16px 0 40px;
  }

  .hero-card,
  .entry-section,
  .info-section {
    padding: 20px;
    border-radius: 22px;
  }
}
</style>