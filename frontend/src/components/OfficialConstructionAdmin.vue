<template>
  <section class="construction-admin" aria-label="校方施工公告管理">
    <div class="toolbar">
      <div class="filters">
        <label>
          搜尋公告
          <input v-model.trim="query" type="search" />
        </label>
        <label>
          顯示狀態
          <select v-model="filter">
            <option value="">全部公告</option>
            <option value="visible">顯示中</option>
            <option value="hidden">已隱藏</option>
          </select>
        </label>
      </div>
      <button
        class="reload-button"
        type="button"
        :disabled="loading"
        @click="load"
      >
        <AdminIcon name="refresh" />
        {{ loading ? "載入中…" : "重新載入" }}
      </button>
    </div>
    <p>隱藏後會移除地圖上的公告與施工標記。</p>
    <p v-if="latest">最近成功更新 {{ formatTime(latest) }}</p>
    <p v-if="message" role="status">{{ message }}</p>
    <p v-if="error" role="alert">{{ error }}</p>
    <p v-if="loading" role="status">載入校方公告中…</p>
    <p v-else-if="!filtered.length && !error">目前沒有符合條件的公告。</p>
    <ul v-else class="notices">
      <li v-for="notice in filtered" :key="notice.Id">
        <article>
          <div class="notice-top">
            <h2>{{ notice.NewsTitle }}</h2>
            <span class="status">{{
              notice.hidden ? "已隱藏" : "顯示中"
            }}</span>
          </div>
          <p>
            {{ notice.construction?.start_date || "起日待確認" }}
            ～ {{ notice.construction?.end_date || "迄日待確認" }}
          </p>
          <p v-if="notice.in_window">施工期間涵蓋今天或未來兩週。</p>
          <div class="actions">
            <a
              v-if="notice.source_url"
              :href="notice.source_url"
              target="_blank"
              rel="noopener noreferrer"
            >
              查看原公告
            </a>
            <button
              type="button"
              :disabled="busy"
              @click="setVisibility(notice)"
            >
              {{ notice.hidden ? "還原公告" : "隱藏公告" }}
            </button>
          </div>
        </article>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import AdminIcon from "./AdminIcon.vue";
import { campusRequest, formatTime } from "../services/campusTools.js";

const notices = ref([]);
const metadata = ref(null);
const filter = ref("");
const query = ref("");
const loading = ref(false);
const busy = ref(false);
const message = ref("");
const error = ref("");
const filtered = computed(() =>
  notices.value.filter(
    (notice) =>
      (!filter.value || (filter.value === "hidden") === notice.hidden) &&
      notice.NewsTitle?.toLowerCase().includes(query.value.toLowerCase())
  )
);
const latest = computed(() =>
  metadata.value?.sources
    .map((source) => source.updated_at)
    .filter(Boolean)
    .sort()
    .pop()
);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const result = await campusRequest("/admin/construction");
    notices.value = result.announcements;
    metadata.value = result.refresh;
  } catch (cause) {
    error.value = cause.message;
  } finally {
    loading.value = false;
  }
}

async function setVisibility(notice) {
  busy.value = true;
  error.value = "";
  message.value = "";
  try {
    const result = await campusRequest(
      "/admin/construction/visibility",
      "POST",
      {
        id: notice.Id,
        hidden: !notice.hidden,
        previous_hidden: notice.hidden,
      }
    );
    await load();
    message.value = result.message;
  } catch (cause) {
    error.value = cause.message;
  } finally {
    busy.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.construction-admin {
  line-height: 1.55;
}
.toolbar,
.filters,
.toolbar label,
.notice-top,
.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.toolbar {
  justify-content: space-between;
  margin: 20px 0;
}
.filters {
  min-width: 0;
}
.toolbar > button {
  margin-left: auto;
}
.toolbar label {
  min-width: 0;
}
.toolbar .reload-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 9px 11px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  color: var(--ink);
  font-size: 13px;
  font-weight: 600;
  transition: background 0.15s, border-color 0.15s;
}
.toolbar .reload-button:hover:not(:disabled) {
  background: #eef4ef;
  border-color: #8da69a;
}
.construction-admin button:not(.reload-button),
.construction-admin select,
.construction-admin input,
.actions a {
  min-height: 44px;
  max-width: 100%;
  padding: 6px 10px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #fff;
  color: #17252d;
}
.actions a {
  display: inline-flex;
  align-items: center;
}
.notices .actions button {
  margin-left: auto;
}
.construction-admin button:not(.reload-button):hover:not(:disabled),
.actions a:hover {
  border-color: #205b77;
}
.construction-admin button:disabled {
  opacity: 0.55;
  cursor: wait;
}
.notices {
  display: grid;
  gap: 12px;
  padding: 0;
  list-style: none;
}
.notices article {
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  overflow-wrap: anywhere;
}
.notices h2 {
  flex: 1;
  min-width: min(100%, 230px);
  margin: 0;
  font-size: 1.1rem;
}
.status {
  padding: 3px 8px;
  border-radius: 4px;
  background: var(--panel-soft);
  font-size: 0.875rem;
}
.notices p {
  margin: 8px 0;
}
</style>
