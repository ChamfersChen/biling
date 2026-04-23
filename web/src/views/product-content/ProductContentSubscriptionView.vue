<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Crown, Rocket, ShieldCheck } from 'lucide-vue-next'
import { useProductContentStore } from '@/stores/productContent'

const router = useRouter()
const productContentStore = useProductContentStore()

const tiers = [
  {
    key: 'free',
    name: 'Free',
    icon: Crown,
    color: '#64748b',
    daily: 5,
    monthly: 50,
    desc: '个人尝鲜'
  },
  {
    key: 'pro',
    name: 'Pro',
    icon: Rocket,
    color: '#2563eb',
    daily: 50,
    monthly: 1500,
    desc: '高频商用'
  },
  {
    key: 'enterprise',
    name: 'Enterprise',
    icon: ShieldCheck,
    color: '#0f766e',
    daily: null,
    monthly: null,
    desc: '企业无限'
  }
]

const currentTier = computed(() => productContentStore.subscription?.tier || productContentStore.currentQuota?.tier || 'free')
const quota = computed(() => productContentStore.currentQuota)

const getLimitText = (value) => (value === null || value === -1 ? '无限' : String(value))

onMounted(async () => {
  await Promise.all([productContentStore.fetchSubscription(), productContentStore.fetchQuota()])
})
</script>

<template>
  <div class="subscription-page">
    <div class="page-header">
      <div>
        <h2>订阅与配额</h2>
        <p>当前档位：{{ currentTier }}</p>
      </div>
      <a-space>
        <a-button @click="router.push('/product-content/generate')">去生成</a-button>
        <a-button @click="router.push('/product-content/history')">查看记录</a-button>
      </a-space>
    </div>

    <a-row :gutter="16" class="tier-row">
      <a-col :xs="24" :md="8" v-for="tier in tiers" :key="tier.key">
        <a-card :class="['tier-card', { active: currentTier === tier.key }]" :bordered="false">
          <div class="tier-title">
            <component :is="tier.icon" :size="18" :color="tier.color" />
            <span>{{ tier.name }}</span>
          </div>
          <p class="tier-desc">{{ tier.desc }}</p>
          <p>每日额度: {{ getLimitText(tier.daily) }}</p>
          <p>每月额度: {{ getLimitText(tier.monthly) }}</p>
          <a-tag v-if="currentTier === tier.key" color="blue">当前档位</a-tag>
        </a-card>
      </a-col>
    </a-row>

    <a-card title="当前使用情况" :bordered="false" class="usage-card">
      <a-descriptions :column="2" bordered size="small">
        <a-descriptions-item label="订阅档位">{{ quota?.tier || '-' }}</a-descriptions-item>
        <a-descriptions-item label="日额度">{{ getLimitText(quota?.daily_limit) }}</a-descriptions-item>
        <a-descriptions-item label="日已用">{{ quota?.daily_used ?? '-' }}</a-descriptions-item>
        <a-descriptions-item label="日剩余">{{ getLimitText(quota?.daily_remaining) }}</a-descriptions-item>
        <a-descriptions-item label="月额度">{{ getLimitText(quota?.monthly_limit) }}</a-descriptions-item>
        <a-descriptions-item label="月已用">{{ quota?.monthly_used ?? '-' }}</a-descriptions-item>
        <a-descriptions-item label="月剩余">{{ getLimitText(quota?.monthly_remaining) }}</a-descriptions-item>
        <a-descriptions-item label="订阅状态">{{ productContentStore.subscription?.status || '-' }}</a-descriptions-item>
      </a-descriptions>
    </a-card>
  </div>
</template>

<style scoped>
.subscription-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
}

.page-header p {
  margin: 4px 0 0;
  color: var(--gray-600);
}

.tier-row {
  margin-bottom: 16px;
}

.tier-card {
  min-height: 180px;
}

.tier-card.active {
  border: 1px solid #3b82f6;
}

.tier-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 6px;
}

.tier-desc {
  color: var(--gray-600);
  margin-bottom: 12px;
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>
