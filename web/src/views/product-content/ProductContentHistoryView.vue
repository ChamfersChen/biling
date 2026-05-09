<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useProductContentStore } from '@/stores/productContent'

const router = useRouter()
const productContentStore = useProductContentStore()

const currentPage = ref(1)
const pageSize = ref(10)

const records = computed(() => productContentStore.generations)
const total = computed(() => productContentStore.generationsTotal)

const formatTime = (v) => {
  if (!v) return '未知'
  const d = new Date(v)
  return Number.isNaN(d.getTime()) ? v : d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadData = async () => {
  await productContentStore.fetchGenerations({ page: currentPage.value, page_size: pageSize.value })
}

const handlePageChange = async (page, size) => {
  currentPage.value = page
  pageSize.value = size
  await loadData()
}

const continueWithPrompt = (record) => {
  const query = {}
  if (record?.prompt_external_id) query.prompt_external_id = record.prompt_external_id
  if (record?.product_id) query.product_id = String(record.product_id)
  router.push({ path: '/product-content/generate', query })
}

onMounted(loadData)
</script>

<template>
  <div class="history-page">
    <div class="history-top">
      <div>
        <span class="top-kicker">History</span>
        <h1>生成记录</h1>
        <p>按批次回看文案结果，支持继续生成和对比不同风格组合。</p>
      </div>
      <div class="top-actions">
        <a-button type="primary" size="large" @click="router.push('/product-content/generate')">继续生成</a-button>
        <a-button size="large" @click="router.push('/product-content/dashboard')">查看看板</a-button>
        <a-button size="large" :loading="productContentStore.loadingGenerations" @click="loadData">刷新</a-button>
      </div>
    </div>

    <div class="history-summary">
      共 {{ total }} 条记录 · 当前第 {{ currentPage }} 页
    </div>

    <a-empty v-if="!productContentStore.loadingGenerations && !records.length" description="暂无生成记录" />

    <div v-else class="record-list">
      <div v-for="record in records" :key="record.id" class="record-card">
        <div class="record-head">
          <div class="record-tags">
            <span class="record-badge">批次 {{ record.id }}</span>
            <a-tag v-if="record.product_name" color="cyan">{{ record.product_name }}</a-tag>
            <a-tag color="blue">{{ record.channel }}</a-tag>
            <a-tag v-if="record.prompt_name" color="purple">{{ record.prompt_name }}</a-tag>
            <span class="record-time">{{ formatTime(record.created_at) }}</span>
          </div>
          <a-button size="small" type="primary" ghost @click="continueWithPrompt(record)">沿用</a-button>
        </div>
        <div class="record-tone">
          <span>风格：</span><a-tag v-for="t in record.tone_styles || []" :key="t">{{ t }}</a-tag>
          <span v-if="record.result_items?.length">{{ record.result_items.length }} 条文案</span>
        </div>
        <a-collapse ghost size="small">
          <a-collapse-panel v-for="(item, idx) in record.result_items || []" :key="idx" :header="`${idx + 1}. ${item.title} · ${item.style}`">
            <p class="item-text">{{ item.content }}</p>
            <div class="item-tags"><a-tag v-for="tag in item.hashtags || []" :key="tag">{{ tag }}</a-tag></div>
            <div class="item-prompt"><span>图片提示词</span><p>{{ item.image_prompt || '无' }}</p></div>
          </a-collapse-panel>
        </a-collapse>
      </div>
    </div>

    <div class="pagination" v-if="total > pageSize">
      <a-pagination v-model:current="currentPage" :page-size="pageSize" :total="total" show-size-changer @change="handlePageChange" @showSizeChange="handlePageChange" />
    </div>
  </div>
</template>

<style scoped>
.history-page {
  padding: 28px;
  min-height: 100%;
  background:
    radial-gradient(circle at 10% 0%, rgba(14, 165, 233, 0.1), transparent 24%),
    radial-gradient(circle at 90% 8%, rgba(251, 191, 36, 0.1), transparent 22%),
    linear-gradient(180deg, #f7fafc, #eef5ff);
}

.history-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 18px;
  max-width: 1200px;
  margin: 0 auto 18px;
}

.top-kicker {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.5);
  color: #0f766e;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.history-top h1 { margin: 10px 0 8px; font-size: 32px; font-weight: 800; color: #162132; }
.history-top p { margin: 0; color: #63748a; }
.top-actions { display: flex; gap: 10px; flex-wrap: wrap; }

.history-summary {
  max-width: 1200px;
  margin: 0 auto 16px;
  padding: 12px 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.5);
  color: #63748a;
  font-size: 13px;
}

.record-list {
  display: grid;
  gap: 14px;
  max-width: 1200px;
  margin: 0 auto;
}

.record-card {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(14px);
}

.record-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.record-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.record-badge {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(14, 165, 233, 0.08);
  color: #0369a1;
  font-size: 12px;
  font-weight: 700;
}

.record-time { color: #63748a; font-size: 12px; margin-left: auto; }

.record-tone {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 0 6px;
  color: #63748a;
  font-size: 13px;
  flex-wrap: wrap;
}

.item-text { white-space: pre-wrap; color: #334155; line-height: 1.7; }
.item-tags { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }

.item-prompt {
  padding: 10px;
  border-radius: 12px;
  background: rgba(241, 245, 249, 0.7);
}

.item-prompt span { display: block; font-size: 12px; color: #63748a; margin-bottom: 4px; }
.item-prompt p { margin: 0; color: #162132; }

.pagination {
  display: flex;
  justify-content: center;
  padding: 20px 0;
  max-width: 1200px;
  margin: 0 auto;
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #0f766e, #2563eb);
  border: none;
}

@media (max-width: 980px) {
  .history-page { padding: 16px; }
  .history-top { flex-direction: column; align-items: flex-start; }
  .record-head { flex-direction: column; align-items: flex-start; }
}
</style>
