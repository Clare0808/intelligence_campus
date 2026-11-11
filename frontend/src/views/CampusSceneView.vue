<template>
  <main class="campus-page">
    <!-- <header class="header">
      <div class="identity">
        <span class="mark">中</span
        ><span
          ><strong>國立中央大學</strong
          ><small>NATIONAL CENTRAL UNIVERSITY</small></span
        >
      </div>
      <nav aria-label="頁面導覽">
        <span>3D OSM 建築輪廓地圖</span
        ><RouterLink to="/map">原有校園示意圖 ↗</RouterLink>
      </nav>
    </header> -->
    <div class="page-body">
      <section class="viewer" aria-label="中央大學 3D 地理地圖">
        <div class="map-area">
          <CampusMap
            :selected-id="selectedId"
            @loaded="onLoaded"
            @select="onSelect"
            @reset="selectedId = ''"
            @construction-loaded="onConstructionLoaded"
          />
        </div>
      </section>
      <aside
        id="building-sidebar"
        class="sidebar"
        :class="{ 'sidebar-closed': !sidebarOpen }"
        aria-label="校園地點分類側邊欄"
        :inert="!sidebarOpen"
      >
        <input
          id="building-search"
          v-model="query"
          type="search"
          placeholder="搜尋地點…"
        />
        <div class="list" aria-label="依類別排列的校園地點">
          <section
            v-for="group in groupedBuildings"
            :key="group.id"
            class="category-group"
          >
            <h2 class="category-heading">
              <button
                class="category-toggle"
                :style="{ '--category-color': group.color }"
                type="button"
                :aria-expanded="isGroupExpanded(group.id)"
                :aria-controls="`category-items-${group.id}`"
                @click="toggleGroup(group.id)"
              >
                <span>{{ group.label }}</span>
                <span class="category-actions">
                  <span class="category-chevron" aria-hidden="true">▼</span>
                </span>
              </button>
            </h2>
            <div
              :id="`category-items-${group.id}`"
              v-show="isGroupExpanded(group.id)"
            >
              <button
                v-for="building in group.features"
                :key="building.properties.id"
                class="building-row"
                :class="{ active: selectedId === building.properties.id }"
                type="button"
                @click="onSelect(building.properties.id)"
              >
                {{ building.properties.name }} <span aria-hidden="true"></span>
              </button>
            </div>
          </section>
          <p v-if="!groupedBuildings.length" class="empty">
            {{ buildings.length ? "找不到符合的地點" : "載入地點資料中…" }}
          </p>
        </div>
        <div v-if="selectedBuilding" class="details" aria-live="polite">
          <span class="eyebrow">{{ selectedCategory?.label ?? "建築" }}</span>
          <h2>{{ selectedBuilding.properties.name || "未命名建築" }}</h2>
          <section class="construction-details" aria-label="施工資訊">
            <h3>施工資訊</h3>
            <p v-if="!selectedAnnouncements.length">尚無施工資訊</p>
            <article
              v-for="(announcement, index) in selectedAnnouncements"
              :key="`${announcement.Id ?? 'announcement'}-${index}`"
              class="construction-announcement"
            >
              <h4>{{ announcement.NewsTitle || "施工公告" }}</h4>
              <p v-if="announcement.construction?.description">
                {{ announcement.construction.description }}
              </p>
              <p v-if="announcement.location?.raw_text">
                地點：{{ announcement.location.raw_text }}
              </p>
              <p
                v-if="announcement.construction?.start_date || announcement.construction?.end_date"
              >
                施工期間：{{ announcement.construction?.start_date || "未提供" }}
                ～ {{ announcement.construction?.end_date || "未提供" }}
              </p>
              <p v-if="announcement.needs_review" class="review-note">
                此公告資訊尚待確認
              </p>
            </article>
          </section>
        </div>
      </aside>
      <button
        class="sidebar-toggle"
        :class="{ 'sidebar-toggle-closed': !sidebarOpen }"
        type="button"
        :aria-label="sidebarOpen ? '收起建築搜尋側邊欄' : '展開建築搜尋側邊欄'"
        aria-controls="building-sidebar"
        :aria-expanded="sidebarOpen"
        @click="sidebarOpen = !sidebarOpen"
      >
        {{ sidebarOpen ? "◀" : "▶" }}
      </button>
    </div>
  </main>
</template>
<script setup>
import { computed, ref } from "vue";
import CampusMap from "../components/CampusMap.vue";
import { categories } from "../map/categories";
const buildings = ref([]);
const constructionAnnouncements = ref([]);
const selectedId = ref("");
const query = ref("");
const sidebarOpen = ref(true);
const collapsedGroups = ref(new Set());
function isGroupExpanded(id) {
  return !!query.value.trim() || !collapsedGroups.value.has(id);
}
function toggleGroup(id) {
  const next = new Set(collapsedGroups.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  collapsedGroups.value = next;
}
const groupedBuildings = computed(() => {
  const search = query.value.trim().toLowerCase();
  return categories
    .map((category) => ({
      ...category,
      features: buildings.value
        .filter(
          (feature) =>
            feature.properties.category === category.id &&
            feature.properties.name?.toLowerCase().includes(search)
        )
        .sort((a, b) =>
          a.properties.name.localeCompare(b.properties.name, "zh-Hant")
        ),
    }))
    .filter((category) => category.features.length);
});
const selectedBuilding = computed(() =>
  buildings.value.find((feature) => feature.properties.id === selectedId.value)
);
const selectedCategory = computed(() =>
  categories.find((category) => category.id === selectedBuilding.value?.properties.category)
);
const selectedAnnouncements = computed(() =>
  constructionAnnouncements.value.filter(
    (announcement) => announcement.location?.location_id === selectedId.value
  )
);
function onLoaded(features) {
  buildings.value = features.filter((feature) => feature.properties.name);
}
function onConstructionLoaded(announcements) {
  constructionAnnouncements.value = announcements;
}
function onSelect(id) {
  selectedId.value = id;
  sidebarOpen.value = true;
}
</script>
<style scoped>
.campus-page {
  --panel: rgba(9, 27, 49, 0.97);
  --panel-soft: rgba(12, 38, 66, 0.96);
  --line: #35678a;
  --glow: #58c8fa;
  --muted: #a2bfd2;
  height: 100vh;
  height: 100dvh;
  background: #071522;
  color: #e5f6ff;
}
.reference,
.details a {
  color: #72e7f5;
}
.page-body {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}
.page-body::after {
  position: absolute;
  z-index: 1;
  inset: 0;
  background: linear-gradient(90deg, rgba(5, 17, 37, 0.12), transparent 48%);
  content: "";
  pointer-events: none;
}
.sidebar {
  position: absolute;
  z-index: 2;
  top: 0;
  bottom: 0;
  left: 0;
  width: min(350px, calc(100% - 40px));
  overflow-y: auto;
  padding: 22px;
  border: 0;
  border-right: 1px solid #35678a66;
  border-radius: 0;
  background: linear-gradient(90deg, #091b31 0%, #091b31f2 55%, #091b31b3 82%, #091b3133 100%);
  transition: transform 0.25s ease, visibility 0.25s ease;
  scrollbar-color: #33778b #0a1b2b;
}
.sidebar-closed {
  visibility: hidden;
  transform: translateX(-100%);
}
.sidebar-toggle {
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--glow);
  cursor: pointer;
  position: absolute;
  z-index: 3;
  top: 50%;
  left: min(350px, 100% - 40px);
  width: 34px;
  height: 64px;
  transform: translateY(-50%);
  border-radius: 0 4px 4px 0;
  box-shadow: 5px 0 20px #06101d99;
  font-size: 18px;
  transition: left 0.25s ease, background 0.2s ease;
}
.sidebar-toggle:hover {
  background: #17416b;
}
.sidebar-toggle-closed {
  left: 0;
}
.sidebar h1 {
  font-size: clamp(32px, 3vw, 46px);
  line-height: 1.3;
  letter-spacing: -0.04em;
}
.sidebar h1 em {
  color: var(--glow);
  font-style: normal;
}
.sidebar > p {
  font-size: 13px;
  line-height: 1.9;
  color: var(--muted);
}
.eyebrow {
  font-size: 10px;
  letter-spacing: 0.12em;
  font-weight: 700;
  color: var(--glow);
}
.search-label {
  display: block;
  margin-top: 8px;
  margin-bottom: 10px;
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 0.14em;
  color: #a8d6e6;
}
input {
  width: 100%;
  border: 1px solid var(--line);
  padding: 12px 13px;
  border-radius: 3px;
  outline: none;
  background: #0b2946;
  color: #effbff;
  caret-color: var(--glow);
}
input::placeholder {
  color: #8daabb;
}
input:focus-visible {
  border-color: var(--glow);
  box-shadow: 0 0 0 2px #58c8fa33;
}
.list {
  overflow-y: auto;
  max-height: min(420px, 50vh);
  margin: 14px 0 16px;
  border: 1px solid var(--line);
  border-radius: 3px;
  background: #0c2540;
  scrollbar-color: #33778b #0a1b2b;
}
.category-heading {
  position: sticky;
  top: 0;
  z-index: 1;
  margin: 0;
  background: #102f50;
}
.category-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 11px 13px;
  background: #123759;
  border: 0;
  border-bottom: 1px solid var(--line);
  border-left: 3px solid var(--category-color);
  color: #e5f6ff;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-align: left;
  cursor: pointer;
}
.category-toggle:hover,
.category-toggle:focus-visible {
  background: #1a4b75;
}
.category-toggle:focus-visible,
.building-row:focus-visible,
.sidebar-toggle:focus-visible {
  outline: 2px solid var(--glow);
  outline-offset: -2px;
}
.category-actions {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 11px;
  color: #8edce9;
}
.category-chevron {
  display: inline-block;
  font-size: 14px;
  line-height: 1;
  transition: all 0.2s;
  transform: rotate(0deg);
}
.category-toggle[aria-expanded="false"] .category-chevron {
  transform: rotate(-90deg);
}
.building-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 10px 14px;
  border: 0;
  border-bottom: 1px solid #224866;
  background: #0c2540;
  color: #dceef6;
  text-align: left;
  cursor: pointer;
  transition: background 0.18s ease, box-shadow 0.18s ease;
}
.building-row span {
  color: #6bcbdc;
}
.building-row:hover,
.building-row.active {
  background: #194d73;
  box-shadow: inset 3px 0 0 var(--glow);
}
.empty {
  padding: 10px;
  font-size: 12px;
  color: var(--muted);
}
.details {
  padding: 17px;
  background: var(--panel-soft);
  border: 1px solid var(--line);
  border-radius: 3px;
  font-size: 12px;
  line-height: 1.7;
}
.details h2 {
  margin: 8px 0;
  font-size: 18px;
  color: #f3fcff;
}
.construction-details {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}
.construction-details h3 {
  margin: 0 0 10px;
  color: #ff4b48;
  font-size: 14px;
}
.construction-announcement + .construction-announcement {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}
.construction-announcement h4 {
  margin: 0 0 6px;
  font-size: 13px;
}
.construction-announcement p {
  margin: 4px 0;
  overflow-wrap: anywhere;
}
.review-note {
  color: #ffb3a5;
}
.details a {
  overflow-wrap: anywhere;
  text-decoration-color: #72e7f599;
}
.notice {
  padding: 12px;
  margin: 15px 0;
  background: #102e4d;
  border: 1px solid var(--line);
  border-radius: 3px;
  color: #b4d5e4;
  font-size: 11px;
  line-height: 1.8;
}
.reference {
  font-size: 12px;
}
.viewer {
  position: relative;
  width: 100%;
  height: 100%;
  background: #071522;
}
.viewer-top,
.viewer-bottom {
  position: absolute;
  z-index: 1;
  right: 16px;
  padding: 9px 12px;
  border: 1px solid var(--line);
  border-radius: 3px;
  background: var(--panel);
  color: var(--glow);
  font-size: 11px;
  font-weight: 700;
  pointer-events: none;
}
.viewer-top {
  top: 16px;
  right: 65px;
}
.viewer-bottom {
  bottom: 32px;
  color: var(--muted);
  font-size: 10px;
}
.map-area {
  width: 100%;
  height: 100%;
}
@media (max-width: 520px) {
  .sidebar {
    width: min(340px, calc(100% - 40px));
  }
  .sidebar-toggle {
    left: min(340px, 100% - 40px);
  }
  .sidebar-toggle-closed {
    left: 0;
  }
  .viewer-top,
  .viewer-bottom {
    display: none;
  }
  .list {
    max-height: 40vh;
  }
}
</style>
