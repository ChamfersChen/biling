<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CalendarClock, Files, RefreshCw, WandSparkles } from 'lucide-vue-next'
import { useProductContentStore } from '@/stores/productContent'

const router = useRouter()
const productContentStore = useProductContentStore()

const currentPage = ref(1)
const pageSize = ref(10)

const records = computed(() => productContentStore.generations)
const total = computed(() => productContentStore.generationsTotal)
const recordCount = computed(() => records.value.length)
const itemCount = computed(() =>
  records.value.reduce((sum, record) => sum + ((record.result_items && record.result_items.length) || 0), 0)
)

const formatTimestamp = (value) => {
  if (!value) {
    return '时间未知'
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return parsed.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadData = async () => {
  await productContentStore.fetchGenerations({
    page: currentPage.value,
    page_size: pageSize.value
  })
}

const handlePageChange = async (page, size) => {
  currentPage.value = page
  pageSize.value = size
  await loadData()
}

const continueWithPrompt = (record) => {
  const query = {}
  if (record?.prompt_external_id) {
    query.prompt_external_id = record.prompt_external_id
  }
  if (record?.product_id) {
    query.product_id = String(record.product_id)
  }
  router.push({ path: '/product-content/generate', query })
}

onMounted(loadData)
</script>

<template>
  <div class="history-page">
    <section class="history-hero">
      <div>
        <span class="eyebrow">History Board</span>
        <h1>把每次生成都整理成可追溯、可复盘的内容档案</h1>
        <p>这里不是简单列表，而是按批次回看输出质量，便于挑选可复用结果、对比不同风格组合。</p>
      </div>
      <div class="hero-actions">
        <a-button type="primary" size="large" @click="router.push('/product-content/generate')">继续生成</a-button>
        <a-button size="large" @click="router.push('/product-content/subscription')">查看配额</a-button>
        <a-button size="large" :loading="productContentStore.loadingGenerations" @click="loadData">
          <template #icon><RefreshCw :size="16" /></template>
          刷新
        </a-button>
      </div>
    </section>

    <section class="stats-row">
      <div class="stat-card">
        <Files :size="18" />
        <div>
          <span>当前页批次</span>
          <strong>{{ recordCount }}</strong>
        </div>
      </div>
      <div class="stat-card">
        <WandSparkles :size="18" />
        <div>
          <span>当前页结果数</span>
          <strong>{{ itemCount }}</strong>
        </div>
      </div>
      <div class="stat-card">
        <CalendarClock :size="18" />
        <div>
          <span>总记录数</span>
          <strong>{{ total }}</strong>
        </div>
      </div>
    </section>

    <a-empty v-if="!productContentStore.loadingGenerations && records.length === 0" description="暂无生成记录" class="empty-box" />

    <section v-else class="timeline-list">
      <article v-for="record in records" :key="record.id" class="timeline-card">
        <div class="timeline-top">
          <div class="top-left">
            <span class="batch-badge">批次 {{ record.id }}</span>
            <a-tag v-if="record.product_name" color="cyan">{{ record.product_name }}</a-tag>
            <a-tag color="blue">{{ record.channel }}</a-tag>
            <a-tag color="gold">{{ record.result_items?.length || 0 }} 条文案</a-tag>
            <a-tag v-if="record.prompt_name" color="purple">{{ record.prompt_name }}</a-tag>
          </div>
          <div class="record-actions">
            <span class="record-time">{{ formatTimestamp(record.created_at) }}</span>
            <a-button size="small" type="primary" @click="continueWithPrompt(record)">沿用提示词继续生成</a-button>
          </div>
        </div>

        <p v-if="record.product_category" class="record-subtitle">{{ record.product_category }} · 便于回看该产品在不同风格与渠道下的表现</p>

        <div v-if="record.prompt_name || record.prompt_external_id" class="prompt-row">
          <span class="tone-label">提示词来源</span>
          <div class="prompt-meta">
            <span class="prompt-name">{{ record.prompt_name || '系统内置提示词' }}</span>
            <span v-if="record.prompt_external_id" class="prompt-external-id">external_id：{{ record.prompt_external_id }}</span>
            <span v-else class="prompt-external-id">系统内置提示词</span>
          </div>
        </div>

        <div class="tone-row">
          <span class="tone-label">风格组合</span>
          <div class="tone-tags">
            <span v-for="tone in record.tone_styles || []" :key="tone" class="tone-pill">{{ tone }}</span>
          </div>
        </div>

        <a-collapse ghost class="history-collapse">
          <a-collapse-panel
            v-for="(item, idx) in record.result_items || []"
            :key="`${record.id}-${idx}`"
            :header="`${idx + 1}. ${item.title || '未返回标题'} · ${item.style || '-'}`"
          >
            <div class="collapse-body">
              <p class="item-content">{{ item.content || '未返回正文' }}</p>
              <div class="item-tags">
                <a-tag v-for="tag in item.hashtags || []" :key="tag" class="hash-tag">{{ tag }}</a-tag>
              </div>
              <div class="prompt-box">
                <span>图片提示词</span>
                <p>{{ item.image_prompt || '无' }}</p>
              </div>
            </div>
          </a-collapse-panel>
        </a-collapse>
      </article>
    </section>

    <div class="pagination-wrap" v-if="total > pageSize">
      <a-pagination
        v-model:current="currentPage"
        :page-size="pageSize"
        :total="total"
        show-size-changer
        @change="handlePageChange"
        @showSizeChange="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.history-page {
  --history-bg: linear-gradient(180deg, #f7fafc, #eef5ff);
  --history-text: #162132;
  --history-muted: #63748a;
  --history-card: rgba(255, 255, 255, 0.78);
  --history-border: rgba(15, 23, 42, 0.08);
  padding: 28px;
  min-height: 100%;
  background:
    radial-gradient(circle at 10% 0%, rgba(14, 165, 233, 0.12), transparent 28%),
    radial-gradient(circle at 90% 8%, rgba(251, 191, 36, 0.14), transparent 26%),
    var(--history-bg);
}

.history-hero,
.stats-row,
.timeline-list,
.pagination-wrap,
.empty-box {
  max-width: 1220px;
  margin-left: auto;
  margin-right: auto;
}

.history-hero {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 18px;
  margin-bottom: 18px;
}

.eyebrow {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.68);
  color: #0f766e;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.history-hero h1 {
  margin: 12px 0 10px;
  font-size: 36px;
  line-height: 1.14;
  font-weight: 800;
  color: var(--history-text);
  max-width: 760px;
}

.history-hero p {
  max-width: 680px;
  color: var(--history-muted);
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.stat-card,
.timeline-card {
  backdrop-filter: blur(14px);
  background: var(--history-card);
  border: 1px solid var(--history-border);
  box-shadow: 0 24px 50px rgba(52, 77, 114, 0.1);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px;
  border-radius: 22px;
  color: var(--history-text);
}

.stat-card span {
  display: block;
  color: var(--history-muted);
  font-size: 13px;
}

.stat-card strong {
  display: block;
  margin-top: 2px;
  font-size: 28px;
  font-weight: 800;
}

.timeline-list {
  display: grid;
  gap: 16px;
}

.timeline-card {
  border-radius: 26px;
  padding: 18px;
}

.timeline-top,
.top-left,
.tone-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.top-left {
  justify-content: flex-start;
  flex-wrap: wrap;
}

.batch-badge,
.tone-pill {
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.record-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.batch-badge {
  background: rgba(14, 165, 233, 0.1);
  color: #0369a1;
}

.record-time {
  color: var(--history-muted);
  font-size: 13px;
}

.record-subtitle {
  margin: 12px 0 0;
  color: var(--history-muted);
  font-size: 13px;
  line-height: 1.6;
}

.tone-row {
  margin: 16px 0 10px;
  align-items: start;
}

.tone-label {
  min-width: 72px;
  color: var(--history-muted);
  font-size: 13px;
}

.tone-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.prompt-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin: 14px 0 4px;
}

.prompt-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.prompt-name {
  color: var(--history-text);
  font-size: 13px;
  font-weight: 700;
}

.prompt-external-id {
  color: var(--history-muted);
  font-size: 12px;
}

.tone-pill {
  background: rgba(245, 158, 11, 0.1);
  color: #a16207;
}

.history-collapse {
  margin-top: 8px;
}

.history-page :deep(.ant-collapse-item) {
  margin-bottom: 10px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 18px !important;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.62);
}

.history-page :deep(.ant-collapse-header) {
  align-items: center !important;
  font-weight: 700;
  color: var(--history-text) !important;
}

.collapse-body {
  display: grid;
  gap: 12px;
}

.item-content {
  white-space: pre-wrap;
  color: #334155;
  line-height: 1.78;
}

.item-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hash-tag {
  border-radius: 999px;
}

.prompt-box {
  padding: 14px;
  border-radius: 18px;
  background: rgba(241, 245, 249, 0.78);
}

.prompt-box span {
  display: block;
  color: var(--history-muted);
  font-size: 12px;
  margin-bottom: 6px;
}

.prompt-box p {
  color: var(--history-text);
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.history-page :deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #0f766e, #2563eb);
  border: none;
}

@media (max-width: 980px) {
  .history-page {
    padding: 16px;
  }

  .history-hero,
  .timeline-top,
  .tone-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .hero-actions {
    width: 100%;
  }

  .hero-actions :deep(.ant-btn) {
    flex: 1 1 auto;
  }
}
</style>
