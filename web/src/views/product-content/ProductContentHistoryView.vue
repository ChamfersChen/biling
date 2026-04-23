<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ReloadOutlined } from '@ant-design/icons-vue'
import { useProductContentStore } from '@/stores/productContent'

const router = useRouter()
const productContentStore = useProductContentStore()

const currentPage = ref(1)
const pageSize = ref(10)

const records = computed(() => productContentStore.generations)
const total = computed(() => productContentStore.generationsTotal)

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

onMounted(loadData)
</script>

<template>
  <div class="history-page">
    <div class="page-header">
      <div>
        <h2>文案生成记录</h2>
        <p>查看历史生成内容，支持回顾不同风格输出</p>
      </div>
      <a-space>
        <a-button @click="router.push('/product-content/generate')">去生成</a-button>
        <a-button @click="router.push('/product-content/subscription')">查看配额</a-button>
        <a-button :loading="productContentStore.loadingGenerations" @click="loadData">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
      </a-space>
    </div>

    <a-empty v-if="!productContentStore.loadingGenerations && records.length === 0" description="暂无记录" />

    <div v-else class="record-list">
      <a-card v-for="record in records" :key="record.id" class="record-item" :bordered="false">
        <div class="record-header">
          <div>
            <a-tag color="blue">{{ record.channel }}</a-tag>
            <a-tag color="geekblue">ID {{ record.id }}</a-tag>
            <a-tag>{{ record.tone_styles?.join(' / ') }}</a-tag>
          </div>
          <span class="record-time">{{ record.created_at }}</span>
        </div>

        <div class="items-wrap">
          <a-collapse>
            <a-collapse-panel
              v-for="(item, idx) in record.result_items || []"
              :key="`${record.id}-${idx}`"
              :header="`${idx + 1}. ${item.title || '未返回标题'} (${item.style || '-'})`"
            >
              <p class="item-content">{{ item.content || '未返回正文' }}</p>
              <div class="item-tags">
                <a-tag v-for="tag in item.hashtags || []" :key="tag">{{ tag }}</a-tag>
              </div>
              <p class="item-prompt">图片提示词: {{ item.image_prompt || '无' }}</p>
            </a-collapse-panel>
          </a-collapse>
        </div>
      </a-card>
    </div>

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

.record-list {
  display: grid;
  gap: 14px;
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.record-time {
  color: var(--gray-600);
  font-size: 12px;
}

.item-content {
  white-space: pre-wrap;
}

.item-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 8px 0;
}

.item-prompt {
  color: var(--gray-700);
  margin: 8px 0 0;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .record-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
