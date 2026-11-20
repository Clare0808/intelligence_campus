<template>
  <main
    class="campus-page"
    :class="{ 'theme-light': theme === 'light' }"
    @keydown.esc="cancelPick"
  >
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
    <div class="page-body" :inert="refreshState !== 'idle'">
      <section class="viewer" aria-label="中央大學 3D 地理地圖">
        <div class="map-area">
          <CampusMap
            :selected-id="selectedId"
            :sidebar-open="sidebarOpen"
            :theme="theme"
            :tool-layers="toolLayers"
            :tool-focus="toolFocus"
            :picking-location="pickingLocation"
            @loaded="onLoaded"
            @select="onSelect"
            @reset="resetMap"
            @clear-route="clearRouteCount += 1"
            @construction-loaded="onConstructionLoaded"
            @theme-change="setTheme"
            @tool-point="onToolPoint"
            @tool-marker="onToolMarker"
          />
          <div v-if="pickingLocation" class="pick-location" role="status">
            <span>點擊地圖選擇回報位置。</span>
            <button type="button" @click="cancelPick">取消</button>
          </div>
        </div>
      </section>
      <aside
        id="building-sidebar"
        class="sidebar"
        :class="{ 'sidebar-closed': !sidebarOpen }"
        aria-label="校園地點分類側邊欄"
        :inert="!sidebarOpen"
      >
        <nav class="campus-navigation" aria-label="校園頁面導覽">
          <RouterLink v-if="isAdmin" :to="{ name: 'campus-admin' }"
            >管理後台</RouterLink
          >
          <button
            type="button"
            :aria-expanded="activePanel === 'report'"
            :aria-controls="
              activePanel === 'report' ? 'campus-tool-panel' : undefined
            "
            @click="activePanel = activePanel === 'report' ? '' : 'report'"
          >
            登入與回報
          </button>
        </nav>
        <CampusTools
          :buildings="buildings"
          v-model:panel="activePanel"
          :map-point="toolPoint"
          :map-marker="toolMarker"
          :reset-count="resetTools"
          :clear-route-count="clearRouteCount"
          @layers="toolLayers = $event"
          @focus="toolFocus = { point: $event }"
          @route-focus="toolFocus = { route: $event }"
          @pick-location="startPick"
          @show-map="sidebarOpen = false"
        />
        <div
          v-if="activePanel === 'construction'"
          id="construction-panel"
          class="construction-panel"
        >
          <div v-if="canRefreshConstruction" class="construction-refresh">
            <button
              class="refresh-button"
              type="button"
              :disabled="refreshState !== 'idle'"
              @click="refreshConstruction"
            >
              {{
                refreshState === "idle" ? "更新施工公告" : "正在更新施工公告…"
              }}
            </button>
            <p v-if="refreshError" role="alert">
              {{ refreshError }}
            </p>
          </div>
          <OfficialConstructionNotices
            :announcements="constructionAnnouncements"
            :refresh="constructionRefresh"
          />
          <input
            id="building-search"
            v-model="query"
            type="search"
            placeholder="搜尋地點…"
            aria-label="搜尋地點"
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
                  :aria-pressed="selectedId === building.properties.id"
                  type="button"
                  @click="onSelect(building.properties.id)"
                >
                  {{ building.properties.name }}
                  <span aria-hidden="true"></span>
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
                  v-if="
                    announcement.construction?.start_date ||
                    announcement.construction?.end_date
                  "
                >
                  施工期間：{{
                    announcement.construction?.start_date || "未提供"
                  }}
                  ～ {{ announcement.construction?.end_date || "未提供" }}
                </p>
              </article>
            </section>
          </div>
        </div>
      </aside>
      <button
        class="sidebar-toggle"
        :class="{ 'sidebar-toggle-closed': !sidebarOpen }"
        type="button"
        :aria-label="sidebarOpen ? '收起功能側邊欄' : '展開功能側邊欄'"
        aria-controls="building-sidebar"
        :aria-expanded="sidebarOpen"
        @click="sidebarOpen = !sidebarOpen"
      >
        <span aria-hidden="true">{{ sidebarOpen ? "◀" : "▶" }}</span>
      </button>
    </div>
    <div
      v-if="refreshState !== 'idle'"
      ref="refreshOverlay"
      class="refresh-overlay"
      role="alertdialog"
      aria-modal="true"
      aria-label="施工公告更新狀態"
      aria-describedby="refresh-overlay-message"
      tabindex="-1"
      @keydown.tab.prevent
    >
      <div class="refresh-overlay-content" aria-live="polite">
        <span
          v-if="refreshState === 'loading'"
          class="refresh-spinner"
          aria-hidden="true"
        ></span>
        <p v-if="refreshState === 'loading'" id="refresh-overlay-message">
          正在抓取並整理施工公告，請稍候…
        </p>
        <p v-else id="refresh-overlay-message" class="refresh-success-message">
          <span class="refresh-success-title">資料更新成功!</span>
          <span>正在重新整理...</span>
        </p>
      </div>
    </div>
  </main>
</template>
<script setup>
import CampusTools from "../components/CampusTools.vue";
import OfficialConstructionNotices from "../components/OfficialConstructionNotices.vue";
import { computed, nextTick, onBeforeUnmount, ref } from "vue";
import CampusMap from "../components/CampusMap.vue";
import { useRoute } from "vue-router";
import { categories } from "../map/categories";
import { refreshConstructionData } from "../map/layers";
import { useCampusAccount } from "../services/campusTools.js";
const canRefreshConstruction = import.meta.env.DEV;
const buildings = ref([]);
const { session } = useCampusAccount();
const isAdmin = computed(() => session.value?.account?.admin === true);
const route = useRoute();
const activePanel = ref(route.query.login ? "report" : "");
const constructionAnnouncements = ref([]);
const constructionRefresh = ref(null);
const selectedId = ref("");
const query = ref("");
const sidebarOpen = ref(true);
const toolLayers = ref(null);
const toolFocus = ref(null);
const toolPoint = ref(null);
const toolMarker = ref(null);
const resetTools = ref(0);
const clearRouteCount = ref(0);
const pickingLocation = ref(false);

function resetMap() {
  selectedId.value = "";
  resetTools.value += 1;
}

function startPick() {
  pickingLocation.value = true;
  sidebarOpen.value = false;
}

function cancelPick() {
  if (!pickingLocation.value) return;
  pickingLocation.value = false;
  sidebarOpen.value = true;
}

function onToolPoint(point) {
  toolPoint.value = point;
  cancelPick();
}

function onToolMarker(marker) {
  toolMarker.value = marker;
  sidebarOpen.value = true;
}
const theme = ref(
  localStorage.getItem("campus-theme") === "light" ? "light" : "dark"
);
function setTheme(value) {
  theme.value = value;
  localStorage.setItem("campus-theme", value);
}
const collapsedGroups = ref(new Set());
const refreshState = ref("idle");
const refreshError = ref("");
const refreshOverlay = ref(null);
let reloadTimer;
async function refreshConstruction() {
  if (refreshState.value !== "idle") return;
  refreshState.value = "loading";
  refreshError.value = "";
  await nextTick();
  refreshOverlay.value?.focus();
  try {
    await refreshConstructionData();
    refreshState.value = "success";
    reloadTimer = window.setTimeout(() => window.location.reload(), 1500);
  } catch (error) {
    refreshError.value = error.message || "施工公告更新失敗，請稍後再試。";
    refreshState.value = "idle";
  }
}
onBeforeUnmount(() => window.clearTimeout(reloadTimer));
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
  categories.find(
    (category) => category.id === selectedBuilding.value?.properties.category
  )
);
const selectedAnnouncements = computed(() =>
  constructionAnnouncements.value.filter(
    (announcement) => announcement.location?.location_id === selectedId.value
  )
);
function onLoaded(features) {
  buildings.value = features.filter((feature) => feature.properties.name);
}
function onConstructionLoaded(announcements, refresh) {
  constructionAnnouncements.value = announcements;
  constructionRefresh.value = refresh ?? null;
}
function onSelect(id) {
  selectedId.value = selectedId.value === id ? "" : id;
  // Narrow screens need the map area to show both the building and its label.
  if (window.innerWidth < 600 && selectedId.value) sidebarOpen.value = false;
}
</script>
<style scoped>
.campus-navigation {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
  gap: 6px;
  margin-bottom: 12px;
}
.campus-navigation a,
.campus-navigation button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 44px;
  padding: 6px 8px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: var(--panel);
  color: var(--glow);
  text-decoration: none;
  font: inherit;
  font-size: 0.875rem;
  cursor: pointer;
}
.campus-navigation a:hover,
.campus-navigation button:hover,
.campus-navigation button[aria-expanded="true"] {
  border-color: var(--glow);
}
.construction-panel {
  margin-top: 8px;
  margin-bottom: 14px;
  padding: 13px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
}
.pick-location {
  position: absolute;
  z-index: 2;
  top: 92px;
  left: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: calc(100% - 65px);
  padding: 6px 10px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: var(--panel);
  font-size: 0.875rem;
}
.pick-location button {
  min-height: 44px;
  padding: 4px 8px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--panel-soft);
  color: inherit;
}
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
.campus-page.theme-light {
  --panel: rgba(255, 255, 255, 0.96);
  --panel-soft: rgba(255, 255, 255, 0.94);
  --line: #b5c4cc;
  --glow: #205b77;
  --muted: #536774;
  background: #f5f6f1;
  color: #17252d;
  color-scheme: light;
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
  background: linear-gradient(
    90deg,
    #091b31 0%,
    #091b31f2 55%,
    #091b31b3 82%,
    #091b3133 100%
  );
  transition: transform 0.25s ease, visibility 0.25s ease;
  scrollbar-color: #33778b #0a1b2b;
}
.sidebar-closed {
  visibility: hidden;
  transform: translateX(-100%);
}
.refresh-button {
  width: 100%;
  padding: 11px 13px;
  border: 1px solid var(--glow);
  border-radius: 3px;
  background: #17416b;
  color: #effbff;
  font-weight: 700;
}
.refresh-button:hover:not(:disabled) {
  background: #1a5a84;
}
.refresh-button:disabled {
  opacity: 0.65;
  cursor: wait;
}
.construction-refresh p {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}
.refresh-overlay {
  position: fixed;
  z-index: 1000;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(4, 16, 30, 0.82);
  backdrop-filter: blur(6px);
}
.refresh-overlay-content {
  display: grid;
  justify-items: center;
  gap: 22px;
  width: min(100%, 420px);
  padding: 36px 24px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--panel);
  box-shadow: 0 18px 60px #020b18aa;
  color: #effbff;
  text-align: center;
}
.refresh-overlay-content p {
  margin: 0;
  font-size: 16px;
  line-height: 1.6;
}
.refresh-success-message {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.refresh-success-title {
  font-size: 24px;
  font-weight: 700;
}
.refresh-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #35678a;
  border-top-color: var(--glow);
  border-radius: 50%;
  animation: refresh-spin 0.8s linear infinite;
}
@keyframes refresh-spin {
  to {
    transform: rotate(360deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .refresh-spinner {
    animation-duration: 2s;
  }
}
.sidebar-toggle {
  border: 1px solid var(--line);
  background: #0c2642;
  color: #e5f6ff;
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
  transition: left 0.25s ease;
}
.sidebar-toggle:hover {
  background: #1a4b75;
  border-color: var(--glow);
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
.theme-light .page-body::after {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.12),
    transparent 48%
  );
}
.theme-light .viewer {
  background: #f5f6f1;
}
.theme-light .sidebar {
  border-right-color: #b5c4cc80;
  background: linear-gradient(
    90deg,
    #ffffff 0%,
    #fffffff2 55%,
    #ffffffb3 82%,
    #ffffff33 100%
  );
  scrollbar-color: #a3b8c4 #eef2f4;
}
.theme-light .sidebar-toggle {
  background: #fff;
  border-color: var(--line);
  color: #17252d;
  box-shadow: 5px 0 20px #364b5b30;
}
.theme-light .sidebar-toggle:hover {
  background: #deebf0;
  border-color: var(--glow);
}
.theme-light .refresh-button {
  background: #fff;
  color: #17252d;
}
.theme-light input,
.theme-light .list,
.theme-light .category-heading,
.theme-light .category-toggle,
.theme-light .building-row {
  background: #fff;
  color: #17252d;
}
.theme-light input::placeholder {
  color: #536774;
}
.theme-light .list {
  scrollbar-color: #a3b8c4 #eef2f4;
}
.theme-light .category-toggle {
  border-bottom-color: var(--line);
}
.theme-light .building-row {
  border-bottom-color: #dce5ea;
}
.theme-light .refresh-button:hover:not(:disabled),
.theme-light .category-toggle:hover,
.theme-light .category-toggle:focus-visible,
.theme-light .building-row:hover,
.theme-light .building-row.active {
  background: #deebf0;
}
.theme-light .category-actions,
.theme-light .building-row span {
  color: var(--glow);
}
.theme-light .details h2,
.theme-light .refresh-overlay-content {
  color: #17252d;
}
.theme-light .review-note {
  color: #a13c2f;
}
.theme-light .refresh-overlay {
  background: rgba(220, 231, 237, 0.78);
}
.theme-light .refresh-overlay-content {
  box-shadow: 0 18px 60px #364b5b30;
}
.theme-light .refresh-spinner {
  border-color: #c6d6de;
  border-top-color: var(--glow);
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
