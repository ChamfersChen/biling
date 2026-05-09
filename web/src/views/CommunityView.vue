<template>
  <div class="community-view">
    <div class="community-top">
      <div class="community-top__main">
        <span class="top-kicker">Community</span>
        <h1>社区</h1>
        <p>浏览精选提示词与内容模板，发现可复用的优质资产。</p>
      </div>
      <a-input-search
        v-model:value="searchKeyword"
        placeholder="搜索提示词、描述或标签..."
        style="width: 300px"
        @search="handleSearch"
        allowClear
      />
    </div>

    <div class="community-tabs">
      <a-button :type="selectedTab[0] === 'prompts' ? 'primary' : 'default'" @click="switchTab('prompts')">
        <BookText :size="16" />
        提示词社区
      </a-button>
      <a-button :type="selectedTab[0] === 'favorites' ? 'primary' : 'default'" @click="switchTab('favorites')">
        <Heart :size="16" />
        我的收藏
      </a-button>
    </div>

    <div class="community-bar" v-if="selectedTab[0] !== 'favorites'">
      <a-radio-group v-model:value="sortBy" size="small" @change="handleSortChange">
        <a-radio-button value="popular">热门</a-radio-button>
        <a-radio-button value="latest">最新</a-radio-button>
        <a-radio-button value="rating">评分</a-radio-button>
      </a-radio-group>
      <div class="bar-categories">
        <a-tag v-for="cat in categories" :key="cat.key" :color="currentCategory === cat.key ? 'blue' : undefined" style="cursor:pointer" @click="handleCategoryChange(cat.key)">{{ cat.name }}</a-tag>
      </div>
      <span class="bar-count">共 {{ totalCount }} 个</span>
    </div>

    <div class="community-bar" v-if="selectedTab[0] === 'favorites'">
      <a-button size="small" type="dashed" @click="openCreateFolderModal">+ 新建收藏夹</a-button>
      <div class="favorite-folder-toolbar">
        <a-select
          v-model:value="favoriteFolder"
          class="favorite-folder-select"
          placeholder="选择收藏夹"
          allow-clear
          show-search
          :filter-option="filterFolderOption"
          :options="favoriteFolderSelectOptions"
        />
        <a-button size="small" @click="openFolderManagerModal">管理收藏夹</a-button>
      </div>
    </div>

    <div class="community-list" v-if="!loading && currentList.length > 0">
      <community-card
        v-for="item in currentList"
        :key="item.id"
        :template="item"
        :favorited="isFavorited(item.id)"
        :mode="selectedTab[0]"
        @click="handleTemplateClick(item)"
        @favorite="handleFavoriteClick(item)"
        @fork="handleFork(item)"
      />
    </div>

    <a-empty v-else-if="!loading" description="暂无内容" class="empty-state" />
    <div v-if="loading" class="loading-state"><a-spin size="large" /></div>

    <div class="community-pagination" v-if="totalCount > pageSize">
      <a-pagination v-model:current="currentPage" :total="totalCount" :pageSize="pageSize" @change="handlePageChange" showQuickJumper />
    </div>

    <a-modal v-model:open="showDetailModal" :title="selectedTemplate?.name || '提示词详情'" :width="920" :footer="null" class="detail-modal">
      <div v-if="detailLoading" class="detail-loading"><a-spin /></div>
      <div v-else class="detail-body">
        <div class="detail-meta-card">
          <div class="detail-meta-card__head">
            <div class="detail-meta-card__tags">
              <a-tag color="blue">提示词</a-tag>
              <a-tag :color="getCategoryColor(selectedTemplate?.category)">{{ getCategoryName(selectedTemplate?.category) }}</a-tag>
              <a-tag v-if="selectedTemplate?.is_official" color="gold">官方</a-tag>
            </div>
            <a-button type="primary" size="small" @click="copyTemplateContent" :disabled="!selectedTemplate?.content">
              <Copy :size="14" />
              复制文案
            </a-button>
          </div>

          <p class="detail-description">{{ selectedTemplate?.description || '暂无描述' }}</p>

          <div class="detail-facts">
            <div class="detail-fact">
              <span class="detail-fact__label">作者</span>
              <span class="detail-fact__value">{{ selectedTemplate?.author || '匿名' }}</span>
            </div>
            <div class="detail-fact">
              <span class="detail-fact__label">发布时间</span>
              <span class="detail-fact__value">{{ selectedTemplate?.created_at || '-' }}</span>
            </div>
            <div class="detail-fact" v-if="selectedTemplate?.department_name">
              <span class="detail-fact__label">来源部门</span>
              <span class="detail-fact__value">{{ selectedTemplate.department_name }}</span>
            </div>
            <div class="detail-fact">
              <span class="detail-fact__label">评分</span>
              <span class="detail-fact__value">{{ selectedTemplate?.rating?.toFixed?.(1) || '0.0' }}</span>
            </div>
          </div>

          <div v-if="selectedTemplate?.variables?.length" class="detail-section">
            <strong>变量</strong>
            <div class="detail-tags">
              <a-tag v-for="v in selectedTemplate.variables" :key="v.name" color="blue">{{ v.name }}{{ v.default ? `: ${v.default}` : '' }}</a-tag>
            </div>
          </div>

          <div v-if="selectedTemplate?.tags?.length" class="detail-section">
            <strong>标签</strong>
            <div class="detail-tags">
              <a-tag v-for="tag in selectedTemplate.tags" :key="tag">{{ tag }}</a-tag>
            </div>
          </div>
        </div>

        <div class="detail-preview">
          <div class="detail-preview__head">
            <h4>提示词文案</h4>
            <span class="detail-preview__hint">点击复制后可直接复用</span>
          </div>
          <pre v-if="selectedTemplate?.content">{{ selectedTemplate.content }}</pre>
          <div v-else class="detail-empty">暂无提示词文案</div>
        </div>
      </div>
    </a-modal>

    <a-modal v-model:open="showFavoriteModal" title="收藏" @ok="confirmFavorite" :confirm-loading="favoriting">
      <a-form layout="vertical">
        <a-form-item label="收藏夹">
          <a-auto-complete v-model:value="favoriteForm.folderPath" :options="favoriteFolderOptions" placeholder="选择或输入新收藏夹" allow-clear style="width:100%" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal v-model:open="showCreateFolderModal" :title="renameTarget ? '重命名收藏夹' : '新建收藏夹'" @ok="handleConfirmFolder" :confirm-loading="creatingFolder" @cancel="renameTarget = ''">
      <a-form layout="vertical">
        <a-form-item label="名称">
          <a-input v-model:value="newFolderName" :placeholder="renameTarget || '常用提示词'" @pressEnter="handleConfirmFolder" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal v-model:open="showFolderManagerModal" title="管理收藏夹" :footer="null" width="560">
      <div class="folder-manager">
        <a-input-search
          v-model:value="folderManagerKeyword"
          placeholder="搜索收藏夹"
          allow-clear
          class="folder-manager__search"
        />
        <div v-if="filteredFavoriteFolders.length" class="folder-manager__list">
          <div v-for="folder in filteredFavoriteFolders" :key="folder" class="folder-manager__item">
            <button class="folder-manager__name" type="button" @click="selectFavoriteFolder(folder)">
              <span>{{ folder }}</span>
              <span v-if="favoriteFolder === folder" class="folder-manager__active">当前使用</span>
            </button>
            <div class="folder-manager__actions">
              <a-button size="small" type="text" @click="openRenameFolderModal(folder)">重命名</a-button>
              <a-button size="small" type="text" danger @click="handleDeleteFolder(folder)">删除</a-button>
            </div>
          </div>
        </div>
        <a-empty v-else description="没有匹配的收藏夹" />
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { BookText, Heart, Copy, FileText, Code, BarChart, Globe, Briefcase, GraduationCap, Megaphone } from 'lucide-vue-next'
import CommunityCard from '@/components/CommunityCard.vue'
import { useCommunityStore } from '@/stores/communityStore'
import { useUserStore } from '@/stores/user'
import * as communityApi from '@/apis/community_api'

const store = useCommunityStore()
const userStore = useUserStore()

const selectedTab = ref(['prompts'])
const currentCategory = ref('all')
const searchKeyword = ref('')
const sortBy = ref('popular')
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)
const loading = ref(false)
const showDetailModal = ref(false)
const detailLoading = ref(false)
const showFavoriteModal = ref(false)
const selectedTemplate = ref(null)
const favoriting = ref(false)
const favoriteFolder = ref('')
const showCreateFolderModal = ref(false)
const creatingFolder = ref(false)
const newFolderName = ref('')
const renameTarget = ref('')
const showFolderManagerModal = ref(false)
const folderManagerKeyword = ref('')
const favoriteForm = ref({ folderPath: '' })

const availableFavoriteFolders = computed(() => Array.from(new Set((store.favoriteFolders || []).filter(Boolean))).sort((a, b) => a.localeCompare(b, 'zh-CN')))

const favoriteFolderOptions = computed(() => availableFavoriteFolders.value.map(f => ({ value: f })))
const favoriteFolderSelectOptions = computed(() => [{ label: '全部收藏', value: '' }, ...availableFavoriteFolders.value.map(folder => ({ label: folder, value: folder }))])
const filteredFavoriteFolders = computed(() => {
  const keyword = folderManagerKeyword.value.trim().toLowerCase()
  if (!keyword) return availableFavoriteFolders.value
  return availableFavoriteFolders.value.filter(folder => folder.toLowerCase().includes(keyword))
})

const categories = [
  { key: 'all', name: '全部', icon: FileText },
  { key: 'writing', name: '写作', icon: FileText },
  { key: 'programming', name: '编程', icon: Code },
  { key: 'analysis', name: '分析', icon: BarChart },
  { key: 'translation', name: '翻译', icon: Globe },
  { key: 'office', name: '办公', icon: Briefcase },
  { key: 'education', name: '教育', icon: GraduationCap },
  { key: 'marketing', name: '营销', icon: Megaphone }
]

const currentList = computed(() => {
  const tab = selectedTab.value[0]
  if (tab === 'prompts') return store.promptTemplates
  if (tab === 'favorites') {
    let items = store.favorites
    if (favoriteFolder.value) items = items.filter(t => t._favorite_folder === favoriteFolder.value)
    return items
  }
  return []
})

const switchTab = (tab) => { selectedTab.value = [tab]; favoriteFolder.value = '' }

onMounted(() => { loadData(); store.fetchFavoriteFolders('prompt') })
watch([selectedTab, currentCategory, sortBy], () => { currentPage.value = 1; loadData() })

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: currentPage.value, pageSize: pageSize.value, category: currentCategory.value === 'all' ? undefined : currentCategory.value, keyword: searchKeyword.value || undefined, sort: sortBy.value }
    if (selectedTab.value[0] === 'prompts') {
      await communityApi.getFavorites().then(data => { store.favorites = data.list || [] })
      const data = await communityApi.getPromptTemplates(params)
      store.promptTemplates = data.list || []
      totalCount.value = data.total || 0
    } else if (selectedTab.value[0] === 'favorites') {
      await store.fetchFavorites('prompt')
      totalCount.value = store.favorites.length
    }
  } catch { message.error('加载失败') }
  finally { loading.value = false }
}

const handleSearch = () => { currentPage.value = 1; loadData() }
const handleSortChange = () => { currentPage.value = 1; loadData() }
const handleCategoryChange = (cat) => { currentCategory.value = cat; currentPage.value = 1; loadData() }
const handlePageChange = (page) => { currentPage.value = page; loadData() }
const filterFolderOption = (input, option) => String(option?.label || '').toLowerCase().includes(String(input || '').toLowerCase())

const isFavorited = (id) => (store.favorites || []).some(t => String(t.id) === String(id))
const handleTemplateClick = async (item) => {
  selectedTemplate.value = item
  showDetailModal.value = true
  detailLoading.value = true
  try {
    const detail = await communityApi.getTemplateDetail(item.id)
    selectedTemplate.value = { ...item, ...detail }
  } catch {
    message.error('加载提示词详情失败')
  } finally {
    detailLoading.value = false
  }
}
const copyTemplateContent = async () => {
  if (selectedTemplate.value?.content) { await navigator.clipboard.writeText(selectedTemplate.value.content); message.success('已复制') }
}
const getCategoryName = (key) => categories.find(c => c.key === key)?.name || key
const getCategoryColor = (key) => {
  const m = { writing: 'gold', programming: 'blue', analysis: 'purple', translation: 'cyan', office: 'geekblue', education: 'green', marketing: 'volcano' }
  return m[key] || 'default'
}

const handleFavoriteClick = async (item) => {
  if (!userStore.isLoggedIn) { message.info('请先登录'); return }
  if (isFavorited(item.id)) {
    try {
      await communityApi.removeFavorite(item.id)
      await loadData()
      message.success('已取消收藏')
    }
    catch { message.error('操作失败') }
    return
  }
  selectedTemplate.value = item
  favoriteForm.value.folderPath = ''
  showFavoriteModal.value = true
}

const confirmFavorite = async () => {
  favoriting.value = true
  try {
    await communityApi.addFavorite({
      template_id: selectedTemplate.value?.id,
      item_type: 'prompt',
      folder_path: favoriteForm.value.folderPath || undefined
    })
    await loadData()
    message.success('收藏成功')
    showFavoriteModal.value = false
  }
  catch { message.error('收藏失败') }
  finally { favoriting.value = false }
}

const handleFork = async (item) => {
  try { await communityApi.forkTemplate(item.id, 'prompt'); message.success('已复制到提示词目录') }
  catch { message.error('复制失败') }
}

const openCreateFolderModal = () => { renameTarget.value = ''; newFolderName.value = ''; showCreateFolderModal.value = true }

const openRenameFolderModal = (folder) => {
  showFolderManagerModal.value = false
  renameTarget.value = folder
  newFolderName.value = folder
  showCreateFolderModal.value = true
}

const openFolderManagerModal = () => {
  folderManagerKeyword.value = ''
  showFolderManagerModal.value = true
}

const selectFavoriteFolder = (folder) => {
  favoriteFolder.value = folder
  showFolderManagerModal.value = false
}

const handleConfirmFolder = async () => {
  if (!newFolderName.value.trim()) { message.warning('请输入名称'); return }
  creatingFolder.value = true
  try {
    if (renameTarget.value) {
      await communityApi.renameFavoriteFolder({
        item_type: 'prompt',
        old_folder_path: renameTarget.value,
        new_folder_path: newFolderName.value.trim()
      })
      message.success('已重命名')
    } else {
      await communityApi.createFavoriteFolder({
        item_type: 'prompt',
        folder_name: newFolderName.value.trim()
      })
      message.success('已创建')
    }
    showCreateFolderModal.value = false
    renameTarget.value = ''
    await store.fetchFavoriteFolders('prompt')
    if (showFolderManagerModal.value) folderManagerKeyword.value = ''
  }
  catch { message.error(renameTarget.value ? '重命名失败' : '创建失败') }
  finally { creatingFolder.value = false }
}

const handleDeleteFolder = (folder) => {
  Modal.confirm({
    title: '删除收藏夹',
    content: `确定删除收藏夹「${folder}」？该收藏夹内的所有收藏项也会被一并删除。`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await communityApi.deleteFavoriteFolder(folder, 'prompt')
        message.success('已删除')
        if (favoriteFolder.value === folder) favoriteFolder.value = ''
        await store.fetchFavoriteFolders('prompt')
        if (!filteredFavoriteFolders.value.length) folderManagerKeyword.value = ''
        await loadData()
      }
      catch { message.error('删除失败') }
    }
  })
}
</script>

<style scoped>
.community-view {
  --cm-text: #172033;
  --cm-muted: #60708a;
  padding: 28px;
  min-height: 100%;
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.08), transparent 24%),
    radial-gradient(circle at 90% 10%, rgba(245, 158, 11, 0.06), transparent 20%),
    linear-gradient(180deg, #f8faff, #eef6ff 45%, #f9fbff);
}

.community-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 18px;
  max-width: 1340px;
  margin: 0 auto 20px;
}

.top-kicker {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.5);
  color: #2563eb;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.community-top h1 {
  margin: 10px 0 8px;
  font-size: 32px;
  font-weight: 800;
  color: var(--cm-text);
}

.community-top p {
  margin: 0;
  color: var(--cm-muted);
}

.community-tabs {
  display: flex;
  gap: 8px;
  max-width: 1340px;
  margin: 0 auto 16px;
}

.community-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  max-width: 1340px;
  margin: 0 auto 18px;
  flex-wrap: wrap;
}

.bar-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  flex: 1;
}

.favorite-folder-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 280px;
}

.favorite-folder-select {
  flex: 1;
  min-width: 220px;
}

.bar-count {
  color: var(--cm-muted);
  font-size: 13px;
  white-space: nowrap;
}

.community-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 1340px;
  margin: 0 auto;
}

.empty-state, .loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  max-width: 1340px;
  margin: 0 auto;
}

.community-pagination {
  display: flex;
  justify-content: center;
  padding: 24px 0;
  max-width: 1340px;
  margin: 0 auto;
}

.detail-body {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 20px;
  max-height: 600px;
  overflow: auto;
}

.detail-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 240px;
}

.detail-meta-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px);
}

.detail-meta-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.detail-meta-card__tags,
.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-description {
  margin: 0;
  color: var(--cm-muted);
  line-height: 1.75;
}

.detail-facts {
  display: grid;
  gap: 12px;
}

.detail-fact {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(241, 245, 249, 0.78);
}

.detail-fact__label {
  font-size: 12px;
  color: #7c8aa5;
}

.detail-fact__value {
  color: var(--cm-text);
  font-weight: 600;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-preview {
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 18px;
  padding: 18px;
  backdrop-filter: blur(16px);
}

.detail-preview__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.detail-preview__head h4 { margin: 0; }

.detail-preview__hint {
  color: #7c8aa5;
  font-size: 12px;
}

.detail-preview pre {
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.7;
  margin: 0;
  color: #334155;
  min-height: 280px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.88);
  overflow: auto;
}

.detail-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 280px;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.88);
  color: #94a3b8;
}

.folder-manager {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.folder-manager__search {
  width: 100%;
}

.folder-manager__list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 420px;
  overflow: auto;
}

.folder-manager__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.folder-manager__name {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--cm-text);
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}

.folder-manager__name span:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.folder-manager__active {
  flex-shrink: 0;
  font-size: 12px;
  color: #2563eb;
  background: rgba(37, 99, 235, 0.12);
  padding: 2px 8px;
  border-radius: 999px;
}

.folder-manager__actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

@media (max-width: 1024px) {
  .detail-body { grid-template-columns: 1fr; }
}

@media (max-width: 820px) {
  .community-view { padding: 16px; }
  .community-top { flex-direction: column; align-items: stretch; }
  .favorite-folder-toolbar {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }
  .detail-meta-card__head {
    flex-direction: column;
    align-items: stretch;
  }
  .folder-manager__item {
    flex-direction: column;
    align-items: stretch;
  }
  .folder-manager__actions {
    justify-content: flex-end;
  }
}
</style>
