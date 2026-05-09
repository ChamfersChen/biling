<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { BarChart3, ChartColumn, Clock3, Package, Sparkles, Wallet } from 'lucide-vue-next'
import { useProductContentStore } from '@/stores/productContent'

const router = useRouter()
const productContentStore = useProductContentStore()

const trendChartRef = ref(null)
const channelChartRef = ref(null)
let trendChart = null
let channelChart = null

const dashboard = computed(() => productContentStore.dashboard || {})
const quota = computed(() => dashboard.value.quota || {})
const subscription = computed(() => dashboard.value.subscription || {})
const accountSummary = computed(() => dashboard.value.account_summary || {})
const todaySummary = computed(() => dashboard.value.today_summary || {})
const usageSummary = computed(() => dashboard.value.usage_summary || {})
const dailyTrend = computed(() => dashboard.value.charts?.daily_trend || [])
const channelDistribution = computed(() => dashboard.value.charts?.channel_distribution || [])

const getLimitText = (value) => (value === null || value === undefined || value === -1 ? '无限' : String(value))

const overviewCards = computed(() => [
  { label: '今日余量', value: getLimitText(todaySummary.value.remaining), hint: `今日已用 ${quota.value.daily_used ?? 0} 次`, icon: Wallet },
  { label: '今日生成批次', value: todaySummary.value.generation_batches ?? 0, hint: `共生成 ${todaySummary.value.generated_items ?? 0} 条文案`, icon: Sparkles },
  { label: '历史总生成', value: accountSummary.value.total_generations ?? 0, hint: `累计 ${accountSummary.value.total_generated_items ?? 0} 条文案`, icon: ChartColumn },
  { label: '已存产品', value: accountSummary.value.total_products ?? 0, hint: `当前订阅 ${accountSummary.value.tier || subscription.value.tier || 'free'}`, icon: Package }
])

const todayStats = computed(() => [
  { label: '文案请求次数', value: todaySummary.value.text_requests ?? 0 },
  { label: '图片生成次数', value: todaySummary.value.image_requests ?? 0 },
  { label: '图片提示词次数', value: todaySummary.value.image_prompt_requests ?? 0 },
  { label: '今日产出文案', value: todaySummary.value.generated_items ?? 0 }
])

const usageStats = computed(() => [
  { label: '今日文案用量', value: `${usageSummary.value.daily_text_used ?? 0} / ${getLimitText(usageSummary.value.daily_text_limit)}` },
  { label: '本月文案用量', value: `${usageSummary.value.monthly_text_used ?? 0} / ${getLimitText(usageSummary.value.monthly_text_limit)}` },
  { label: '订阅状态', value: subscription.value.status || 'active' },
  { label: '当前档位', value: subscription.value.tier || quota.value.tier || 'free' }
])

const loadData = async () => {
  await productContentStore.fetchDashboard()
}

const initTrendChart = () => {
  if (!trendChartRef.value) return
  if (trendChart) {
    trendChart.dispose()
    trendChart = null
  }
  trendChart = echarts.init(trendChartRef.value)
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 20, right: 20, bottom: 10, top: 42, containLabel: true },
    xAxis: {
      type: 'category',
      data: dailyTrend.value.map((item) => item.label)
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '文案请求',
        type: 'line',
        smooth: true,
        data: dailyTrend.value.map((item) => item.text_generate_count),
        lineStyle: { width: 3, color: '#2563eb' },
        itemStyle: { color: '#2563eb' },
        areaStyle: { color: 'rgba(37, 99, 235, 0.12)' }
      },
      {
        name: '图片生成',
        type: 'bar',
        barMaxWidth: 18,
        data: dailyTrend.value.map((item) => item.image_generate_count),
        itemStyle: { color: '#f59e0b', borderRadius: [8, 8, 0, 0] }
      }
    ]
  })
}

const initChannelChart = () => {
  if (!channelChartRef.value) return
  if (channelChart) {
    channelChart.dispose()
    channelChart = null
  }
  channelChart = echarts.init(channelChartRef.value)
  channelChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        name: '渠道分布',
        type: 'pie',
        radius: ['48%', '74%'],
        center: ['50%', '44%'],
        label: { formatter: '{b}\n{c}' },
        data: channelDistribution.value.length
          ? channelDistribution.value.map((item) => ({ name: item.channel, value: item.count }))
          : [{ name: '暂无数据', value: 1, itemStyle: { color: '#cbd5e1' } }]
      }
    ]
  })
}

const renderCharts = () => {
  nextTick(() => {
    initTrendChart()
    initChannelChart()
  })
}

const handleResize = () => {
  if (trendChart) trendChart.resize()
  if (channelChart) channelChart.resize()
}

watch([dailyTrend, channelDistribution], renderCharts, { deep: true })

onMounted(async () => {
  await loadData()
  renderCharts()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (trendChart) trendChart.dispose()
  if (channelChart) channelChart.dispose()
})
</script>

<template>
  <div class="dashboard-page">
    <div class="dashboard-top">
      <div>
        <span class="top-kicker">Dashboard</span>
        <h1>数据看板</h1>
        <p>集中查看账户余量、历史用量、今日产出和近 7 天使用趋势。</p>
      </div>
      <div class="top-actions">
        <a-button type="primary" size="large" @click="router.push('/product-content/generate')">去生成</a-button>
        <a-button size="large" @click="router.push('/product-content/history')">查看记录</a-button>
        <a-button size="large" :loading="productContentStore.loadingDashboard" @click="loadData">刷新</a-button>
      </div>
    </div>

    <div class="overview-grid">
      <article v-for="card in overviewCards" :key="card.label" class="overview-card">
        <div class="overview-card__icon"><component :is="card.icon" :size="18" /></div>
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <p>{{ card.hint }}</p>
      </article>
    </div>

    <div class="dashboard-layout">
      <section class="glass-panel chart-panel chart-panel--wide">
        <div class="section-head">
          <div>
            <span class="section-kicker">Trend</span>
            <h3>近 7 天使用趋势</h3>
          </div>
          <span class="section-note">文案请求 + 图片生成</span>
        </div>
        <div ref="trendChartRef" class="chart-box"></div>
      </section>

      <section class="glass-panel chart-panel">
        <div class="section-head">
          <div>
            <span class="section-kicker">Channels</span>
            <h3>渠道分布</h3>
          </div>
          <span class="section-note">按生成批次统计</span>
        </div>
        <div ref="channelChartRef" class="chart-box chart-box--pie"></div>
      </section>
    </div>

    <div class="stats-grid">
      <section class="glass-panel stats-panel">
        <div class="section-head">
          <div>
            <span class="section-kicker">Today</span>
            <h3>当天统计</h3>
          </div>
          <Clock3 :size="18" />
        </div>
        <div class="mini-grid">
          <div v-for="item in todayStats" :key="item.label" class="mini-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </section>

      <section class="glass-panel stats-panel">
        <div class="section-head">
          <div>
            <span class="section-kicker">Usage</span>
            <h3>使用统计</h3>
          </div>
          <BarChart3 :size="18" />
        </div>
        <div class="mini-grid">
          <div v-for="item in usageStats" :key="item.label" class="mini-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </section>

      <section class="glass-panel stats-panel stats-panel--subscription">
        <div class="section-head">
          <div>
            <span class="section-kicker">Plan</span>
            <h3>订阅与配额</h3>
          </div>
          <a-tag color="blue">{{ subscription.tier || quota.tier || 'free' }}</a-tag>
        </div>
        <div class="subscription-list">
          <div class="subscription-row"><span>今日文案额度</span><strong>{{ quota.daily_used ?? 0 }} / {{ getLimitText(quota.daily_limit) }}</strong></div>
          <div class="subscription-row"><span>本月文案额度</span><strong>{{ quota.monthly_used ?? 0 }} / {{ getLimitText(quota.monthly_limit) }}</strong></div>
          <div class="subscription-row"><span>状态</span><strong>{{ subscription.status || 'active' }}</strong></div>
          <div class="subscription-row"><span>到期时间</span><strong>{{ subscription.expires_at || '长期有效' }}</strong></div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  padding: 28px;
  min-height: 100%;
  background:
    radial-gradient(circle at 12% 0%, rgba(37, 99, 235, 0.1), transparent 24%),
    radial-gradient(circle at 92% 10%, rgba(245, 158, 11, 0.12), transparent 22%),
    linear-gradient(180deg, #f8fbff, #eef6ff 55%, #f7fbff);
}

.dashboard-top,
.overview-grid,
.dashboard-layout,
.stats-grid {
  max-width: 1240px;
  margin: 0 auto;
}

.dashboard-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 18px;
  margin-bottom: 20px;
}

.top-kicker,
.section-kicker {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.52);
  color: #2563eb;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.dashboard-top h1,
.section-head h3 {
  margin: 10px 0 8px;
  color: #172033;
  font-weight: 800;
}

.dashboard-top h1 { font-size: 32px; }
.dashboard-top p,
.section-note,
.overview-card p,
.mini-card span,
.subscription-row span { color: #60708a; }

.top-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 18px;
}

.overview-card,
.glass-panel {
  border-radius: 22px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.76);
  backdrop-filter: blur(16px);
}

.overview-card {
  padding: 18px;
}

.overview-card__icon {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  margin-bottom: 12px;
  color: #2563eb;
  background: rgba(37, 99, 235, 0.1);
}

.overview-card span,
.mini-card span { display: block; font-size: 13px; }
.overview-card strong,
.mini-card strong { display: block; margin-top: 6px; font-size: 28px; font-weight: 800; color: #172033; }
.overview-card p { margin: 8px 0 0; font-size: 13px; }

.dashboard-layout {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.glass-panel {
  padding: 20px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-head h3 { font-size: 22px; }

.chart-box {
  width: 100%;
  height: 320px;
}

.chart-box--pie {
  height: 320px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.mini-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.mini-card {
  padding: 14px;
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.8);
}

.mini-card strong { font-size: 22px; }

.subscription-list {
  display: grid;
  gap: 12px;
}

.subscription-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.84);
}

.subscription-row strong {
  color: #172033;
  font-weight: 700;
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #2563eb, #f59e0b);
  border: none;
}

@media (max-width: 1080px) {
  .dashboard-page { padding: 16px; }
  .dashboard-top { flex-direction: column; align-items: flex-start; }
  .overview-grid,
  .stats-grid,
  .dashboard-layout {
    grid-template-columns: 1fr 1fr;
  }
  .chart-panel--wide,
  .stats-panel--subscription {
    grid-column: span 2;
  }
}

@media (max-width: 720px) {
  .overview-grid,
  .stats-grid,
  .dashboard-layout,
  .mini-grid {
    grid-template-columns: 1fr;
  }
  .chart-panel--wide,
  .stats-panel--subscription {
    grid-column: auto;
  }
}
</style>
