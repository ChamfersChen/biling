<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'
import { Crown, Infinity, ReceiptText, Rocket, ShieldCheck, TicketPercent, WalletCards } from 'lucide-vue-next'
import { productContentApi } from '@/apis/product_content_api'
import { useProductContentStore } from '@/stores/productContent'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const productContentStore = useProductContentStore()

const redeemCode = ref('')
const redeeming = ref(false)
const creatingCheckout = ref('')
const openingPortal = ref(false)
const loadingCodes = ref(false)
const creatingCode = ref(false)
const codes = ref([])
const codeForm = ref({ tier: 'pro', quantity: 10, expires_at: '' })
const generatedCodesModalOpen = ref(false)
const latestGeneratedCodes = ref([])
const codeListExpanded = ref(false)

const subscription = computed(() => productContentStore.subscription || {})
const quota = computed(() => productContentStore.currentQuota || {})
const transactions = computed(() => productContentStore.transactions || [])
const plans = computed(() => subscription.value.plans || [])

const currentTier = computed(() => subscription.value.tier || quota.value.tier || 'free')
const canManageSubscription = computed(() => Boolean(subscription.value?.stripe_customer_id))
const isSuperAdmin = computed(() => userStore.isSuperAdmin)
const subscriptionCodes = computed(() => productContentStore.subscriptionCodes || [])
const unusedCodeCount = computed(() => subscriptionCodes.value.filter((item) => Number(item.used_count || 0) < 1).length)
const getLimitText = (v) => (v === null || v === undefined || v === -1 ? '无限' : String(v))
const getPriceText = (price) => (price ? `￥${(price / 100).toFixed(0)}/月` : '免费')

const usageCards = computed(() => [
  { label: '本月已用', value: `${quota.value.monthly_used ?? 0} / ${getLimitText(quota.value.monthly_limit)}`, icon: WalletCards },
  { label: '本月剩余', value: getLimitText(quota.value.monthly_remaining), icon: ReceiptText },
  { label: '当前档位', value: currentTier.value, icon: ShieldCheck },
  { label: '状态', value: subscription.value.status || 'active', icon: Crown }
])

const planIconMap = {
  free: Crown,
  pro: Rocket,
  max: Infinity
}

const loadData = async () => {
  await Promise.all([
    productContentStore.fetchSubscription(),
    productContentStore.fetchQuota(),
    productContentStore.fetchTransactions()
  ])
  if (isSuperAdmin.value) {
    await loadCodes()
  }
}

const loadCodes = async () => {
  loadingCodes.value = true
  try {
    const data = typeof productContentStore.fetchSubscriptionCodes === 'function'
      ? await productContentStore.fetchSubscriptionCodes()
      : await productContentApi.getSubscriptionCodes()
    codes.value = data?.list || []
  } catch (error) {
    message.error(error?.message || '加载兑换码失败')
  } finally {
    loadingCodes.value = false
  }
}

const handleCheckout = async (plan) => {
  creatingCheckout.value = plan.key
  try {
    const { checkout_url: checkoutUrl } = await productContentStore.createCheckoutSession({
      tier: plan.key,
      success_url: `${window.location.origin}/product-content/subscription?checkout=success`,
      cancel_url: `${window.location.origin}/product-content/subscription?checkout=cancel`
    })
    if (!checkoutUrl) throw new Error('支付链接创建失败')
    window.location.href = checkoutUrl
  } catch (error) {
    message.error(error?.message || '创建支付会话失败')
  } finally {
    creatingCheckout.value = ''
  }
}

const handleRedeem = async () => {
  if (!redeemCode.value.trim()) {
    message.warning('请输入兑换码')
    return
  }
  redeeming.value = true
  try {
    const result = await productContentStore.redeemCode({ code: redeemCode.value.trim() })
    message.success(`兑换成功，已升级到 ${result.tier}`)
    redeemCode.value = ''
    await productContentStore.fetchTransactions()
  } catch (error) {
    message.error(error?.message || '兑换失败')
  } finally {
    redeeming.value = false
  }
}

const handleOpenPortal = async () => {
  openingPortal.value = true
  try {
    const { portal_url: portalUrl } = await productContentStore.createCustomerPortal({
      return_url: `${window.location.origin}/product-content/subscription`
    })
    if (!portalUrl) throw new Error('订阅管理入口创建失败')
    window.location.href = portalUrl
  } catch (error) {
    message.error(error?.message || '打开订阅管理失败')
  } finally {
    openingPortal.value = false
  }
}

const handleCreateCode = async () => {
  if (!codeForm.value.quantity || codeForm.value.quantity < 1) {
    message.warning('请输入有效的生成数量')
    return
  }
  creatingCode.value = true
  try {
    const payload = {
      tier: codeForm.value.tier,
      quantity: codeForm.value.quantity,
      expires_at: codeForm.value.expires_at || undefined
    }
    const data = typeof productContentStore.createSubscriptionCode === 'function'
      ? await productContentStore.createSubscriptionCode(payload)
      : await productContentApi.createSubscriptionCode(payload)
    latestGeneratedCodes.value = data?.list || []
    generatedCodesModalOpen.value = latestGeneratedCodes.value.length > 0
    message.success(`已生成 ${data?.count || payload.quantity} 个兑换码`)
    codeForm.value = { tier: 'pro', quantity: 10, expires_at: '' }
    await loadCodes()
  } catch (error) {
    message.error(error?.message || '创建兑换码失败')
  } finally {
    creatingCode.value = false
  }
}

const copyCode = async (value) => {
  try {
    await navigator.clipboard.writeText(String(value || ''))
    message.success('已复制')
  } catch {
    message.error('复制失败')
  }
}

const copyAllCodes = async () => {
  const fullText = latestGeneratedCodes.value.map((item) => item.code).join('\n')
  await copyCode(fullText)
}

onMounted(async () => {
  await loadData()
  const checkoutState = route.query.checkout
  if (checkoutState === 'success') {
    message.success('支付已完成，订阅信息正在刷新')
    await loadData()
  } else if (checkoutState === 'cancel') {
    message.info('已取消支付')
  }
})
</script>

<template>
  <div class="sub-page">
    <div class="sub-top">
      <div>
        <span class="top-kicker">Subscription</span>
        <h1>订阅中心</h1>
        <p>按月升级配额，支持在线支付和兑换码充值，配额用尽时可快速升级。</p>
      </div>
      <div class="top-actions">
        <a-button size="large" @click="router.push('/product-content/dashboard')">查看看板</a-button>
        <a-button type="primary" size="large" @click="router.push('/product-content/generate')">去生成</a-button>
      </div>
    </div>

    <div class="usage-row">
      <div v-for="card in usageCards" :key="card.label" class="usage-card">
        <component :is="card.icon" :size="18" />
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
      </div>
    </div>

    <div class="content-grid">
      <section class="glass-panel plans-panel">
        <div class="section-head">
          <div>
            <span class="section-kicker">Plans</span>
            <h3>升级方案</h3>
          </div>
        </div>

        <div class="plan-row">
          <article v-for="plan in plans" :key="plan.key" :class="['plan-card', { active: currentTier === plan.key }]">
            <div class="plan-head">
              <component :is="planIconMap[plan.key] || Crown" :size="20" />
              <a-tag v-if="currentTier === plan.key" color="blue">当前</a-tag>
            </div>
            <h3>{{ plan.name }}</h3>
            <p class="plan-price">{{ getPriceText(plan.price) }}</p>
            <p class="plan-desc">{{ plan.description }}</p>
            <div class="plan-limits">
              <div><span>每月请求</span><strong>{{ getLimitText(plan.monthly_limit) }}</strong></div>
            </div>
            <a-button
              v-if="plan.key !== 'free'"
              type="primary"
              block
              :loading="creatingCheckout === plan.key"
              @click="handleCheckout(plan)"
            >
              {{ currentTier === plan.key ? '续费当前方案' : `升级到 ${plan.name}` }}
            </a-button>
          </article>
        </div>
      </section>

      <section class="glass-panel side-panel">
        <div class="section-head">
          <div>
            <span class="section-kicker">Redeem</span>
            <h3>兑换码充值</h3>
          </div>
          <TicketPercent :size="18" />
        </div>
        <p class="side-copy">输入兑换码后可直接提升档位，并自动刷新当前订阅和剩余额度。</p>
        <a-input v-model:value="redeemCode" size="large" placeholder="请输入兑换码" />
        <a-button type="primary" block :loading="redeeming" @click="handleRedeem">立即兑换</a-button>
        <a-button v-if="canManageSubscription" block :loading="openingPortal" @click="handleOpenPortal">管理订阅</a-button>

        <div class="transaction-head">
          <span class="section-kicker">History</span>
          <h3>最近交易</h3>
        </div>
        <div v-if="transactions.length" class="transaction-list">
          <div v-for="item in transactions" :key="item.id" class="transaction-item">
            <div>
              <strong>{{ item.tier }}</strong>
              <p>{{ item.source === 'redeem' ? '兑换码充值' : 'Stripe 支付' }}</p>
            </div>
            <div class="transaction-meta">
              <span>{{ item.amount ? `￥${(item.amount / 100).toFixed(0)}` : '￥0' }}</span>
              <small>{{ item.status }}</small>
            </div>
          </div>
        </div>
        <a-empty v-else description="暂无交易记录" />

        <template v-if="isSuperAdmin">
          <div class="transaction-head">
            <span class="section-kicker">Admin</span>
            <h3>兑换码管理</h3>
          </div>
          <p class="side-copy">选择档位和生成数量后，系统会自动批量生成多个 32 位兑换码。</p>
          <div class="admin-form">
            <div class="admin-form__row">
              <a-select v-model:value="codeForm.tier" :options="[{ label: 'Pro', value: 'pro' }, { label: 'Max', value: 'max' }]" />
              <a-input-number v-model:value="codeForm.quantity" :min="1" :max="200" style="width: 100%" placeholder="生成数量" />
            </div>
            <a-input v-model:value="codeForm.expires_at" placeholder="过期时间，可选：2026-12-31T23:59:59" />
            <a-button type="primary" block :loading="creatingCode" @click="handleCreateCode">创建兑换码</a-button>
          </div>
          <div class="code-summary" v-if="subscriptionCodes.length">
            <div class="code-summary__item">
              <span>兑换码总数</span>
              <strong>{{ subscriptionCodes.length }}</strong>
            </div>
            <div class="code-summary__item">
              <span>未使用</span>
              <strong>{{ unusedCodeCount }}</strong>
            </div>
            <a-button @click="codeListExpanded = !codeListExpanded">{{ codeListExpanded ? '收起兑换码' : '展开兑换码' }}</a-button>
          </div>
          <div v-if="subscriptionCodes.length && codeListExpanded" class="code-list-wrap">
            <div class="code-list">
              <div v-for="item in subscriptionCodes" :key="item.id" class="code-item">
                <div>
                  <strong>{{ item.code }}</strong>
                  <p>{{ item.tier }} · 单次兑换 · 已用 {{ item.used_count }} / 1</p>
                </div>
                <div class="code-item__actions">
                  <small>{{ item.expires_at || '永久有效' }}</small>
                  <a-button type="link" size="small" @click="copyCode(item.code)">复制</a-button>
                </div>
              </div>
            </div>
          </div>
          <a-empty v-else-if="!loadingCodes" description="暂无兑换码" />
        </template>
      </section>
    </div>

    <a-modal v-model:open="generatedCodesModalOpen" title="本次生成的兑换码" :footer="null" width="720">
      <div class="generated-codes-modal">
        <div class="generated-codes-modal__head">
          <p>本次共生成 {{ latestGeneratedCodes.length }} 个兑换码，可直接复制后分发。</p>
          <a-button type="primary" @click="copyAllCodes">复制全部</a-button>
        </div>
        <div class="generated-codes-list">
          <div v-for="item in latestGeneratedCodes" :key="item.id" class="generated-code-row">
            <div>
              <strong>{{ item.code }}</strong>
              <p>{{ item.tier }} · {{ item.expires_at || '永久有效' }}</p>
            </div>
            <a-button size="small" @click="copyCode(item.code)">复制</a-button>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<style scoped>
.sub-page {
  padding: 28px;
  min-height: 100%;
  background:
    radial-gradient(circle at left top, rgba(194, 65, 12, 0.1), transparent 24%),
    radial-gradient(circle at 85% 10%, rgba(16, 185, 129, 0.1), transparent 20%),
    linear-gradient(180deg, #faf7ff, #eef6ff 55%, #f8fbff);
}

.sub-top, .usage-row, .content-grid { max-width: 1240px; margin: 0 auto; }

.sub-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 18px;
  margin-bottom: 20px;
}

.top-kicker, .section-kicker {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.5);
  color: #c2410c;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.sub-top h1 { margin: 10px 0 8px; font-size: 32px; font-weight: 800; color: #172033; }
.sub-top p, .side-copy, .plan-desc, .transaction-item p { margin: 0; color: #60708a; }
.top-actions { display: flex; gap: 10px; flex-wrap: wrap; }

.usage-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}

.usage-card, .glass-panel {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(14px);
}

.usage-card span { display: block; margin-top: 10px; color: #64748b; font-size: 13px; }
.usage-card strong { display: block; margin-top: 6px; font-size: 24px; font-weight: 800; color: #172033; }

.content-grid {
  display: grid;
  grid-template-columns: 1.6fr 0.9fr;
  gap: 16px;
}

.section-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.section-head h3, .transaction-head h3 { margin: 8px 0 0; font-size: 22px; font-weight: 800; color: #172033; }

.plan-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.plan-card {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(15, 23, 42, 0.08);
}

.plan-card.active {
  box-shadow: 0 20px 40px rgba(37, 99, 235, 0.12);
}

.plan-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.plan-card h3 { margin: 0; font-size: 26px; font-weight: 800; color: #172033; }
.plan-price { margin: 8px 0 6px; font-size: 22px; font-weight: 800; color: #c2410c; }
.plan-limits { margin: 16px 0; }
.plan-limits div { padding: 12px; border-radius: 14px; background: rgba(248, 250, 252, 0.8); }
.plan-limits span { display: block; color: #64748b; font-size: 13px; }
.plan-limits strong { display: block; margin-top: 2px; font-size: 20px; color: #172033; }

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.transaction-head { margin-top: 8px; }

.transaction-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.admin-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.admin-form__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.code-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.82);
}

.code-summary__item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.code-summary__item span {
  color: #64748b;
  font-size: 12px;
}

.code-summary__item strong {
  color: #172033;
  font-size: 18px;
}

.code-list-wrap {
  max-height: 360px;
  overflow: auto;
}

.code-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.code-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.82);
}

.code-item strong { color: #172033; }
.code-item small { color: #64748b; }

.code-item__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.generated-codes-modal {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.generated-codes-modal__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.generated-codes-modal__head p {
  margin: 0;
  color: #60708a;
}

.generated-codes-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 420px;
  overflow: auto;
}

.generated-code-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.82);
}

.generated-code-row strong {
  color: #172033;
  word-break: break-all;
}

.generated-code-row p {
  margin: 4px 0 0;
  color: #64748b;
}

.transaction-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.82);
}

.transaction-item strong { color: #172033; text-transform: capitalize; }
.transaction-meta { text-align: right; }
.transaction-meta span { display: block; color: #172033; font-weight: 700; }
.transaction-meta small { color: #64748b; text-transform: capitalize; }

:deep(.ant-btn-primary) { background: linear-gradient(135deg, #c2410c, #2563eb); border: none; }

@media (max-width: 1080px) {
  .sub-page { padding: 16px; }
  .sub-top { flex-direction: column; align-items: flex-start; }
  .usage-row, .content-grid, .plan-row { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 720px) {
  .usage-row, .content-grid, .plan-row { grid-template-columns: 1fr; }
}
</style>
