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
          <button class="nav-link nav-link--button" type="button" @click="handleProtectedNav('/product-content/generate')">
            产品文案
          </button>
          <button class="nav-link nav-link--button" type="button" @click="handleProtectedNav('/extensions/prompts')">
            提示词管理
          </button>
          <button class="nav-link nav-link--button" type="button" @click="handleProtectedNav('/community')">
            社区
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
            <p class="eyebrow">统一管理提示词、社区分发与产品内容生成</p>
            <h2 class="hero-title">从提示词资产到社区分发，再到产品文案与生图，一套界面完成协作闭环。</h2>
            <p class="hero-subtitle">
              {{ infoStore.branding.subtitle || '面向运营、内容和业务团队的 AI 工作台' }}
            </p>

            <div class="hero-actions">
              <button class="hero-btn hero-btn--primary" @click="goToWorkspace">
                {{ primaryActionLabel }}
              </button>
            </div>

            <div class="hero-metrics">
              <div class="metric-tile" v-for="item in headlineMetrics" :key="item.label">
                <p class="metric-value">{{ item.value }}</p>
                <p class="metric-label">{{ item.label }}</p>
                <p class="metric-note">{{ item.note }}</p>
              </div>
            </div>
          </div>

          <div class="hero-side">
            <div class="workspace-preview">
              <div class="preview-header">
                <span class="preview-pill">当前系统能力</span>
                <span class="preview-status">在线工作台</span>
              </div>

              <div class="preview-stack">
                <div class="preview-module preview-module--highlight">
                  <div>
                    <p class="module-kicker">Content Studio</p>
                    <h3>产品文案生成</h3>
                    <p>支持已存产品复用、结果回看、单条生图、订阅配额。</p>
                  </div>
                  <Sparkles :size="18" />
                </div>

                <div class="preview-grid">
                  <div class="preview-module" v-for="module in previewModules" :key="module.title">
                    <component :is="module.icon" :size="18" class="module-icon" />
                    <p class="module-title">{{ module.title }}</p>
                    <p class="module-desc">{{ module.description }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="section-block capability-block">
          <div class="section-heading">
            <p class="section-kicker">Platform</p>
            <h3>围绕当前系统功能重新组织首页信息架构</h3>
            <p>不只是展示产品介绍，而是把今天已经可用的功能路径直接呈现出来。</p>
          </div>

          <div class="capability-grid">
            <article class="capability-card" v-for="item in capabilityCards" :key="item.title">
              <div class="capability-icon">
                <component :is="item.icon" :size="18" />
              </div>
              <h4>{{ item.title }}</h4>
              <p>{{ item.description }}</p>
              <span>{{ item.footnote }}</span>
            </article>
          </div>
        </section>

        <section class="section-block route-block">
          <div class="section-heading">
            <p class="section-kicker">Entry Points</p>
            <h3>按角色进入最合适的工作入口</h3>
            <p>管理员管理资产与结构，普通用户直接进入内容消费和生产流程。</p>
          </div>

          <div class="route-grid">
            <article class="route-card" v-for="item in entryRoutes" :key="item.title">
              <div class="route-top">
                <component :is="item.icon" :size="18" />
                <span>{{ item.tag }}</span>
              </div>
              <h4>{{ item.title }}</h4>
              <p>{{ item.description }}</p>
              <button class="route-link" @click="navigateTo(item.to)">{{ item.action }}</button>
            </article>
          </div>
        </section>

        <section class="section-block insight-block" v-if="featureCards.length">
          <div class="section-heading">
            <p class="section-kicker">Signals</p>
            <h3>来自品牌配置的附加信息</h3>
            <p>保留系统配置中的业务指标、亮点和说明信息。</p>
          </div>

          <div class="insight-grid">
            <article class="insight-card" v-for="card in featureCards" :key="card.label">
              <div class="insight-icon" v-if="card.icon">
                <component :is="card.icon" :size="18" />
              </div>
              <p class="insight-value">{{ card.value || '--' }}</p>
              <p class="insight-label">{{ card.label }}</p>
              <p class="insight-desc">{{ card.description || '来自系统配置的补充说明' }}</p>
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
import { Result, Button, message } from 'ant-design-vue'
import UserInfoComponent from '@/components/UserInfoComponent.vue'
import {
  Sparkles,
  Bot,
  FolderTree,
  Globe2,
  Image,
  FileText,
  ShieldCheck,
  BadgeDollarSign,
  Wand2,
  Compass,
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

const goToWorkspace = () => {
  if (!userStore.isLoggedIn) {
    sessionStorage.setItem('redirect', '/product-content/generate')
    router.push('/login')
    return
  }

  router.push('/product-content/generate')
}

const handleProtectedNav = (to) => {
  if (!userStore.isLoggedIn) {
    sessionStorage.setItem('redirect', to)
    router.push('/login')
    return
  }

  if (to === '/extensions/prompts' && !userStore.isAdmin) {
    message.info('提示词管理仅管理员可用，已为你打开社区')
    router.push('/community')
    return
  }

  router.push(to)
}

const navigateTo = (to) => {
  if (!userStore.isLoggedIn) {
    sessionStorage.setItem('redirect', to)
    router.push('/login')
    return
  }
  router.push(to)
}

const primaryActionLabel = computed(() => {
  if (!userStore.isLoggedIn) {
    return '登录并开始使用'
  }
  if (userStore.isAdmin) {
    return '进入系统'
  }
  return '进入产品文案工作台'
})

const headlineMetrics = computed(() => [
  { label: '核心模块', value: '3', note: '提示词管理、社区、产品文案' },
  { label: '内容链路', value: 'End-to-End', note: '从资产维护到生成、分发与复用' },
  { label: '订阅档位', value: '3', note: 'free / pro / enterprise 配额体系' }
])

const previewModules = computed(() => [
  { icon: FolderTree, title: '提示词管理', description: '目录树、变量识别、测试与发布到社区' },
  { icon: Globe2, title: '社区协作', description: '分类浏览、收藏互动、内容传播与沉淀' },
  { icon: Image, title: '图片生成', description: '基于文案结果逐条触发生图流程' }
])

const capabilityCards = computed(() => [
  {
    icon: Wand2,
    title: '通用产品文案工作台',
    description: '支持产品资料保存、风格组合、渠道适配、历史批次回看和最近结果复用。',
    footnote: '覆盖 generate / history / subscription'
  },
  {
    icon: FolderTree,
    title: '提示词资产管理',
    description: '通过目录树维护提示词文件、变量结构、测试结果，并可直接发布到社区。',
    footnote: '适合管理员与运营维护知识资产'
  },
  {
    icon: Globe2,
    title: '社区分发与复用',
    description: '社区页承担浏览、发现、筛选和内容复用能力。',
    footnote: '把内部资产变成可共享的内容单元'
  },
  {
    icon: BadgeDollarSign,
    title: '订阅与配额治理',
    description: '按套餐控制每日和每月使用量，支持面向业务侧的清晰容量展示。',
    footnote: 'free / pro / enterprise'
  },
  {
    icon: ShieldCheck,
    title: '多租户与权限体系',
    description: '复用现有 user_id、department_id 和鉴权体系，管理员与普通用户路径分离。',
    footnote: '保持现有后端组织结构与安全边界'
  },
  {
    icon: Bot,
    title: 'AI 生成闭环',
    description: '从 Prompt 构建、结构化结果解析，到图片生成与对象存储上传已经串联。',
    footnote: '内容与视觉资产可连续生产'
  }
])

const entryRoutes = computed(() => [
  {
    icon: FileText,
    tag: 'Generate',
    title: '产品文案',
    description: '进入产品文案生成台，创建新产品、复用已存产品、查看最近结果并逐条生图。',
    action: '打开工作台',
    to: '/product-content/generate'
  },
  {
    icon: Compass,
    tag: 'Discover',
    title: '社区',
    description: '浏览社区内容、分类和文件夹视角，查看详情并参与交流。',
    action: '浏览社区',
    to: '/community'
  },
  {
    icon: FolderTree,
    tag: 'Admin',
    title: '提示词管理',
    description: '管理员可维护提示词目录、测试变量与发布状态，持续经营提示词资产。',
    action: '管理提示词',
    to: '/extensions/prompts'
  }
])

const iconKey = (value) => (typeof value === 'string' ? value.toLowerCase() : '')

const featureIconMap = {
  stars: Star,
  issues: CheckCircle2,
  resolved: CheckCircle2,
  commits: GitCommit,
  license: ShieldCheck,
  default: Star
}

const featureCards = computed(() => {
  const list = Array.isArray(infoStore.features) ? infoStore.features : []
  return list
    .map((item) => {
      if (typeof item === 'string') {
        return {
          label: item,
          value: '',
          description: '',
          icon: featureIconMap.default
        }
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
    radial-gradient(circle at top left, rgba(245, 158, 11, 0.18), transparent 28%),
    radial-gradient(circle at 88% 12%, rgba(37, 99, 235, 0.14), transparent 24%),
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
  background: rgba(255, 255, 255, 0.42);
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
  letter-spacing: 0.16em;
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
  flex-wrap: wrap;
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
  border: 1px solid rgba(37, 99, 235, 0.12);
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
  width: min(1280px, calc(100% - 32px));
  margin: 0 auto;
  padding: 28px 0 48px;
}

.hero-card,
.section-block,
.overview-panel {
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.38);
  border: 1px solid rgba(255, 255, 255, 0.56);
  box-shadow: 0 24px 52px rgba(27, 52, 92, 0.12);
  backdrop-filter: blur(18px);
}

.hero-card {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(360px, 0.8fr);
  gap: 28px;
  padding: 34px;
}

.eyebrow,
.section-kicker,
.module-kicker {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #d97706;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-title {
  margin: 0;
  font-size: clamp(36px, 5vw, 62px);
  line-height: 1.05;
  letter-spacing: -0.04em;
  color: #172033;
}

.hero-subtitle {
  margin: 0;
  max-width: 760px;
  font-size: 18px;
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
  padding: 0 20px;
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

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 8px;
}

.metric-tile,
.preview-module,
.capability-card,
.route-card,
.insight-card {
  background: rgba(255, 255, 255, 0.34);
  border: 1px solid rgba(255, 255, 255, 0.52);
  backdrop-filter: blur(12px);
}

.metric-tile {
  padding: 18px;
  border-radius: 22px;
}

.metric-value {
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 800;
  color: #172033;
}

.metric-label {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 700;
  color: #2d3d57;
}

.metric-note {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: #60708a;
}

.hero-side,
.workspace-preview,
.preview-stack {
  display: flex;
  flex-direction: column;
}

.workspace-preview {
  height: 100%;
  padding: 22px;
  border-radius: 26px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.46), rgba(255, 255, 255, 0.24));
  border: 1px solid rgba(255, 255, 255, 0.58);
}

.preview-header,
.route-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.preview-pill,
.preview-status,
.route-top span {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.preview-pill {
  color: #2563eb;
  background: rgba(37, 99, 235, 0.08);
}

.preview-status,
.route-top span {
  color: #b45309;
  background: rgba(217, 119, 6, 0.1);
}

.preview-stack {
  gap: 12px;
  margin-top: 18px;
}

.preview-module {
  padding: 16px;
  border-radius: 20px;
}

.preview-module--highlight {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  background: linear-gradient(135deg, rgba(217, 119, 6, 0.12), rgba(37, 99, 235, 0.12));
}

.preview-module h3,
.module-title,
.capability-card h4,
.route-card h4 {
  margin: 6px 0 8px;
  color: #172033;
}

.preview-module p,
.module-desc,
.capability-card p,
.route-card p,
.insight-desc,
.section-heading p {
  margin: 0;
  color: #60708a;
  line-height: 1.65;
}

.preview-grid,
.capability-grid,
.route-grid,
.insight-grid {
  display: grid;
  gap: 14px;
}

.preview-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.module-icon,
.capability-icon {
  color: #2563eb;
}

.module-title {
  font-size: 14px;
  font-weight: 700;
}

.module-desc {
  font-size: 13px;
}

.section-block,
.overview-panel {
  margin-top: 18px;
  padding: 28px;
}

.section-heading {
  max-width: 720px;
  margin-bottom: 18px;
}

.section-heading h3 {
  margin: 8px 0 10px;
  font-size: 28px;
  color: #172033;
}

.capability-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.capability-card,
.route-card,
.insight-card {
  padding: 20px;
  border-radius: 24px;
}

.capability-card span {
  display: inline-block;
  margin-top: 12px;
  font-size: 12px;
  font-weight: 700;
  color: #2563eb;
}

.route-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.route-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.route-link {
  align-self: flex-start;
  border: none;
  background: transparent;
  padding: 0;
  color: #2563eb;
  font-weight: 700;
  cursor: pointer;
}

.insight-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.insight-icon {
  width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(37, 99, 235, 0.08);
  color: #2563eb;
}

.insight-value {
  margin: 12px 0 6px;
  font-size: 28px;
  font-weight: 800;
  color: #172033;
}

.insight-label {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 700;
  color: #2d3d57;
}

.site-footer {
  padding: 0 24px 32px;
  text-align: center;
}

.site-footer p {
  margin: 0;
  color: #60708a;
}

@media (max-width: 1120px) {
  .hero-card,
  .capability-grid,
  .route-grid {
    grid-template-columns: 1fr;
  }

  .hero-metrics,
  .preview-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .site-header {
    position: static;
    flex-direction: column;
    align-items: stretch;
    padding: 16px;
  }

  .top-nav,
  .header-actions {
    justify-content: center;
  }

  .home-main {
    width: calc(100% - 20px);
    padding: 10px 0 24px;
  }

  .hero-card,
  .section-block,
  .overview-panel {
    padding: 18px;
    border-radius: 24px;
  }

  .hero-title {
    font-size: 34px;
  }
}
</style>
