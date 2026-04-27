<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Crown, Rocket, ShieldCheck, Sparkles } from 'lucide-vue-next'
import { useProductContentStore } from '@/stores/productContent'

const router = useRouter()
const productContentStore = useProductContentStore()

const tiers = [
  {
    key: 'free',
    name: 'Free',
    icon: Crown,
    color: '#c2410c',
    daily: 5,
    monthly: 50,
    desc: '适合个人体验和小批量试跑',
    accent: 'amber'
  },
  {
    key: 'pro',
    name: 'Pro',
    icon: Rocket,
    color: '#2563eb',
    daily: 50,
    monthly: 1500,
    desc: '适合高频生成和持续内容运营',
    accent: 'blue'
  },
  {
    key: 'enterprise',
    name: 'Enterprise',
    icon: ShieldCheck,
    color: '#0f766e',
    daily: null,
    monthly: null,
    desc: '适合团队协同和规模化生产',
    accent: 'green'
  }
]

const currentTier = computed(() => productContentStore.subscription?.tier || productContentStore.currentQuota?.tier || 'free')
const quota = computed(() => productContentStore.currentQuota)

const getLimitText = (value) => (value === null || value === -1 ? '无限' : String(value))

const usageHealth = computed(() => {
  const dailyRemaining = quota.value?.daily_remaining
  if (dailyRemaining === undefined || dailyRemaining === null) {
    return {
      tone: 'neutral',
      text: '正在同步配额状态'
    }
  }
  if (dailyRemaining === -1) {
    return {
      tone: 'healthy',
      text: '当前档位不受日额度限制'
    }
  }
  if (dailyRemaining <= 0) {
    return {
      tone: 'warning',
      text: '今日文案生成额度已用尽'
    }
  }
  if (dailyRemaining <= 2) {
    return {
      tone: 'warning',
      text: '今日额度接近上限，建议集中处理高优先级产品'
    }
  }
  return {
    tone: 'healthy',
    text: '当前额度充足，可继续批量生成'
  }
})

const usageCards = computed(() => [
  {
    label: '今日已用',
    value: quota.value?.daily_used ?? '-',
    helper: `总额度 ${getLimitText(quota.value?.daily_limit)}`
  },
  {
    label: '今日剩余',
    value: getLimitText(quota.value?.daily_remaining),
    helper: '按日维度控制生成频率'
  },
  {
    label: '本月已用',
    value: quota.value?.monthly_used ?? '-',
    helper: `月额度 ${getLimitText(quota.value?.monthly_limit)}`
  },
  {
    label: '订阅状态',
    value: productContentStore.subscription?.status || '-',
    helper: `当前档位 ${currentTier.value}`
  }
])

onMounted(async () => {
  await Promise.all([productContentStore.fetchSubscription(), productContentStore.fetchQuota()])
})
</script>

<template>
  <div class="subscription-page">
    <section class="subscription-hero">
      <div>
        <span class="eyebrow">Plan Overview</span>
        <h1>把配额展示做成清晰的运营面板，而不是一张冰冷的表</h1>
        <p>现在可以更直观看到当前档位、日月使用进度，以及不同订阅层级的容量差异。</p>
      </div>
      <div class="hero-actions">
        <a-button type="primary" size="large" @click="router.push('/product-content/generate')">去生成</a-button>
        <a-button size="large" @click="router.push('/product-content/history')">查看记录</a-button>
      </div>
    </section>

    <section class="usage-grid">
      <div v-for="card in usageCards" :key="card.label" class="usage-stat-card">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <p>{{ card.helper }}</p>
      </div>
    </section>

    <section :class="['health-banner', usageHealth.tone]">
      <div>
        <span class="panel-kicker">Capacity Signal</span>
        <h3>{{ usageHealth.text }}</h3>
        <p>发布前建议把高频生成账号升级到更合适的档位，避免运营高峰时被配额打断。</p>
      </div>
      <a-button type="primary" @click="router.push('/product-content/generate')">继续处理产品内容</a-button>
    </section>

    <section class="plan-grid">
      <article v-for="tier in tiers" :key="tier.key" :class="['plan-card', tier.accent, { active: currentTier === tier.key }]">
        <div class="plan-top">
          <div class="plan-icon">
            <component :is="tier.icon" :size="18" :color="tier.color" />
          </div>
          <a-tag v-if="currentTier === tier.key" color="blue">当前方案</a-tag>
        </div>
        <h3>{{ tier.name }}</h3>
        <p class="plan-desc">{{ tier.desc }}</p>
        <div class="plan-limits">
          <div>
            <span>每日额度</span>
            <strong>{{ getLimitText(tier.daily) }}</strong>
          </div>
          <div>
            <span>每月额度</span>
            <strong>{{ getLimitText(tier.monthly) }}</strong>
          </div>
        </div>
        <div class="plan-footer">
          <Sparkles :size="15" />
          <span v-if="tier.key === 'free'">用于试用与低频场景</span>
          <span v-else-if="tier.key === 'pro'">适合持续内容投放与团队运营</span>
          <span v-else>适合高并发、长期使用与企业业务</span>
        </div>
      </article>
    </section>

    <section class="details-panel">
      <div class="panel-header">
        <div>
          <span class="panel-kicker">Usage Snapshot</span>
          <h3>当前使用明细</h3>
        </div>
      </div>
      <a-descriptions :column="2" bordered size="middle">
        <a-descriptions-item label="订阅档位">{{ quota?.tier || '-' }}</a-descriptions-item>
        <a-descriptions-item label="订阅状态">{{ productContentStore.subscription?.status || '-' }}</a-descriptions-item>
        <a-descriptions-item label="日额度">{{ getLimitText(quota?.daily_limit) }}</a-descriptions-item>
        <a-descriptions-item label="日已用">{{ quota?.daily_used ?? '-' }}</a-descriptions-item>
        <a-descriptions-item label="日剩余">{{ getLimitText(quota?.daily_remaining) }}</a-descriptions-item>
        <a-descriptions-item label="月额度">{{ getLimitText(quota?.monthly_limit) }}</a-descriptions-item>
        <a-descriptions-item label="月已用">{{ quota?.monthly_used ?? '-' }}</a-descriptions-item>
        <a-descriptions-item label="月剩余">{{ getLimitText(quota?.monthly_remaining) }}</a-descriptions-item>
      </a-descriptions>
    </section>
  </div>
</template>

<style scoped>
.subscription-page {
  --sub-text: #172033;
  --sub-muted: #64748b;
  padding: 28px;
  min-height: 100%;
  background:
    radial-gradient(circle at left top, rgba(194, 65, 12, 0.12), transparent 26%),
    radial-gradient(circle at 85% 10%, rgba(16, 185, 129, 0.12), transparent 22%),
    linear-gradient(180deg, #faf7ff, #eef6ff 55%, #f8fbff);
}

.subscription-hero,
.usage-grid,
.plan-grid,
.details-panel,
.health-banner {
  max-width: 1220px;
  margin-left: auto;
  margin-right: auto;
}

.subscription-hero {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 18px;
  margin-bottom: 18px;
}

.eyebrow,
.panel-kicker {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.74);
  color: #c2410c;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.subscription-hero h1 {
  margin: 12px 0 10px;
  max-width: 760px;
  font-size: 36px;
  line-height: 1.15;
  font-weight: 800;
  color: var(--sub-text);
}

.subscription-hero p {
  max-width: 680px;
  color: var(--sub-muted);
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.usage-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.usage-stat-card,
.plan-card,
.details-panel {
  backdrop-filter: blur(14px);
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 24px 52px rgba(58, 77, 114, 0.1);
}

.usage-stat-card {
  padding: 18px;
  border-radius: 22px;
}

.usage-stat-card span {
  display: block;
  color: var(--sub-muted);
  font-size: 13px;
}

.usage-stat-card strong {
  display: block;
  margin: 8px 0 6px;
  font-size: 28px;
  font-weight: 800;
  color: var(--sub-text);
}

.usage-stat-card p {
  color: var(--sub-muted);
  font-size: 13px;
}

.plan-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.health-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
  padding: 22px;
  border-radius: 28px;
  backdrop-filter: blur(14px);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 24px 52px rgba(58, 77, 114, 0.1);
}

.health-banner.healthy {
  background: linear-gradient(135deg, rgba(236, 253, 245, 0.92), rgba(239, 246, 255, 0.88));
}

.health-banner.warning {
  background: linear-gradient(135deg, rgba(255, 247, 237, 0.94), rgba(255, 251, 235, 0.9));
}

.health-banner.neutral {
  background: rgba(255, 255, 255, 0.82);
}

.health-banner h3 {
  margin: 10px 0 8px;
  font-size: 24px;
  font-weight: 800;
  color: var(--sub-text);
}

.health-banner p {
  color: var(--sub-muted);
}

.plan-card {
  border-radius: 26px;
  padding: 20px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.plan-card.active {
  transform: translateY(-4px);
}

.plan-card.amber.active {
  box-shadow: 0 30px 60px rgba(194, 65, 12, 0.16);
}

.plan-card.blue.active {
  box-shadow: 0 30px 60px rgba(37, 99, 235, 0.16);
}

.plan-card.green.active {
  box-shadow: 0 30px 60px rgba(15, 118, 110, 0.16);
}

.plan-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.plan-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.78);
}

.plan-card h3 {
  font-size: 28px;
  font-weight: 800;
  color: var(--sub-text);
}

.plan-desc {
  margin-top: 8px;
  color: var(--sub-muted);
  min-height: 42px;
}

.plan-limits {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 20px;
}

.plan-limits div {
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.6);
}

.plan-limits span {
  display: block;
  color: var(--sub-muted);
  font-size: 13px;
}

.plan-limits strong {
  display: block;
  margin-top: 4px;
  font-size: 24px;
  font-weight: 800;
  color: var(--sub-text);
}

.plan-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 18px;
  color: var(--sub-muted);
}

.plan-card.amber {
  background: linear-gradient(180deg, rgba(255, 244, 230, 0.95), rgba(255, 255, 255, 0.82));
}

.plan-card.blue {
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.95), rgba(255, 255, 255, 0.82));
}

.plan-card.green {
  background: linear-gradient(180deg, rgba(236, 253, 245, 0.95), rgba(255, 255, 255, 0.82));
}

.details-panel {
  border-radius: 28px;
  padding: 22px;
}

.panel-header {
  margin-bottom: 16px;
}

.panel-header h3 {
  margin-top: 10px;
  font-size: 24px;
  font-weight: 800;
  color: var(--sub-text);
}

.subscription-page :deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #c2410c, #2563eb);
  border: none;
}

.subscription-page :deep(.ant-descriptions) {
  border-radius: 20px;
  overflow: hidden;
}

@media (max-width: 980px) {
  .subscription-page {
    padding: 16px;
  }

  .subscription-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .usage-grid,
  .plan-grid {
    grid-template-columns: 1fr;
  }

  .health-banner {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
