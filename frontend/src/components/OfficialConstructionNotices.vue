<template>
  <details v-if="refresh" class="official-notices">
    <summary>校方施工公告 · 近期 {{ upcoming.length }} 筆</summary>
    <p v-if="latest">最近成功取得 {{ formatTime(latest) }}</p>
    <p>每 {{ refresh.interval_minutes }} 分鐘查詢校方公告。</p>
    <p v-if="unavailable.length" role="status">
      {{ unavailable.join("、") }} 暫時無法更新，保留先前公告。
    </p>
    <p v-if="!upcoming.length">目前沒有確認落在兩週內的施工公告。</p>
    <p v-if="!recent.length">尚無可顯示的公告。</p>
    <ul v-else>
      <li v-for="notice in recent" :key="notice.Id">
        <a
          v-if="notice.source_url"
          :href="notice.source_url"
          target="_blank"
          rel="noopener noreferrer"
        >
          {{ notice.NewsTitle }}
        </a>
        <strong v-else>{{ notice.NewsTitle }}</strong>
        <p v-if="notice.source_name">{{ notice.source_name }}</p>
        <p>
          {{ notice.construction?.start_date || "起日待確認" }}
          ～ {{ notice.construction?.end_date || "迄日待確認" }}
        </p>
        <p v-if="notice.in_window && !notice.location?.location_id">
          公告位置尚無可確認的地圖建物。
        </p>
      </li>
    </ul>
  </details>
</template>

<script setup>
import { computed } from "vue";
import { formatTime } from "../services/campusTools.js";

/* global defineProps */
const props = defineProps({
  announcements: { type: Array, required: true },
  refresh: { type: Object, default: null },
});
const upcoming = computed(() =>
  props.announcements.filter((notice) => notice.in_window)
);
const recent = computed(() =>
  [...props.announcements]
    .sort(
      (a, b) =>
        Number(b.in_window) - Number(a.in_window) ||
        (b.PublishDate || "").localeCompare(a.PublishDate || "")
    )
    .slice(0, Math.max(6, upcoming.value.length))
);
const latest = computed(() =>
  props.refresh.sources
    .map((source) => source.updated_at)
    .filter(Boolean)
    .sort()
    .pop()
);
const unavailable = computed(() =>
  props.refresh.sources
    .filter((source) => source.status === "error")
    .map((source) => source.name)
);
</script>

<style scoped>
.official-notices {
  margin: 0 0 14px;
  padding: 0 10px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: var(--panel);
  font-size: 0.875rem;
  overflow-wrap: anywhere;
}
.official-notices summary {
  min-height: 44px;
  align-content: center;
  cursor: pointer;
}
.official-notices p {
  margin: 4px 0;
  color: var(--muted);
}
.official-notices ul {
  list-style: none;
  padding: 0;
  margin: 10px 0;
}
.official-notices li {
  padding: 8px 0;
  border-top: 1px solid var(--line);
}
.official-notices a {
  color: var(--glow);
}
</style>
