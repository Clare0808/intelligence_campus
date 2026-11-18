<template>
  <section class="tools" aria-label="校園地圖工具">
    <div class="tool-nav">
      <button
        v-for="[id, name] in tools"
        :key="id"
        type="button"
        :aria-expanded="panel === id"
        :aria-controls="panel ? 'campus-tool-panel' : undefined"
        @click="panel = panel === id ? '' : id"
      >
        {{ name }}
      </button>
    </div>
    <div v-if="panel" id="campus-tool-panel" class="tool-panel">
      <template v-if="panel === 'route'">
        <h2>路線規劃</h2>
        <p v-if="datasetError" role="alert">{{ datasetError }}</p>
        <form class="fields" @submit.prevent="planRoute">
          <label>
            起點
            <select v-model="start" required>
              <option value="" disabled>選擇起點</option>
              <option v-for="place in places" :key="place.id" :value="place.id">
                {{ place.name }}
              </option>
            </select>
          </label>
          <label>
            終點
            <select v-model="end" required>
              <option value="" disabled>選擇終點</option>
              <option v-for="place in places" :key="place.id" :value="place.id">
                {{ place.name }}
              </option>
            </select>
          </label>
          <label>
            路線偏好
            <select v-model="mode">
              <option value="walking">步行</option>
              <option value="wheelchair">輪椅／推行李 · 避開階梯</option>
              <option value="night">夜間 · 優先使用有照明紀錄的路段</option>
            </select>
          </label>
          <button
            class="primary"
            :disabled="planning || !planner"
            type="submit"
          >
            {{ planning ? "規劃中…" : "規劃路線" }}
          </button>
        </form>
        <p v-if="routeError" role="alert">{{ routeError }}</p>
        <div v-if="planned" class="result" aria-live="polite">
          <strong>約 {{ Math.round(planned.distance) }} 公尺</strong>
          <p>
            起終點採建物附近的實際 OSM 道路。起點距建物參考點約
            {{ Math.round(planned.startOffset) }} 公尺， 終點距建物參考點約
            {{ Math.round(planned.endOffset) }} 公尺。
          </p>
          <p class="muted">
            地圖道路與路線使用同一份 OSM 資料，建物入口連接仍需現場確認。
          </p>
          <p v-if="mode === 'wheelchair'">
            無障礙可信度：{{
              percent(planned.wheelchair) === 100 ? "路段皆有標記" : "有限"
            }}。 {{ percent(planned.wheelchair) }}%
            路段有輪椅可通行標記；出入口與坡度仍需確認。
          </p>
          <p v-if="mode === 'night'">
            照明可信度：{{
              percent(planned.lightingKnown) === 100 ? "路段皆有紀錄" : "有限"
            }}。 已標有照明 {{ percent(planned.lit) }}%，照明未知
            {{ 100 - percent(planned.lightingKnown) }}%。
          </p>
          <p v-if="reportsError" role="status">
            道路封閉回報暫不可用，路線只使用 OSM 路網。
          </p>
          <p class="muted">
            路況可信度：依地圖標記及已審核回報。OSM 取得日
            {{ network.retrieved }}。
            <a :href="network.licence" target="_blank" rel="noopener noreferrer"
              >© OpenStreetMap contributors</a
            >
          </p>
          <div class="action-row">
            <button type="button" @click="emit('show-map')">查看地圖</button>
            <button type="button" @click="clearRoute">清除路線</button>
          </div>
        </div>
      </template>

      <template v-else-if="panel === 'markers'">
        <h2>地圖標記</h2>
        <fieldset>
          <legend>顯示圖層</legend>
          <label class="check">
            <input v-model="showAccessibility" type="checkbox" />
            <span class="key access-key" aria-hidden="true">A</span>
            無障礙設施
          </label>
          <label class="check">
            <input v-model="showIdle" type="checkbox" />
            <span class="key idle-key" aria-hidden="true">I</span>
            閒置設施
          </label>
          <label class="check">
            <input v-model="showOtherReports" type="checkbox" />
            其他校園回報（施工、毀壞）
          </label>
        </fieldset>
        <p v-if="datasetError" role="alert">{{ datasetError }}</p>
        <p v-if="reportsError" role="alert">{{ reportsError }}</p>
        <p
          v-if="showIdle && !idleReports.length && !reportsError"
          class="muted"
        >
          目前沒有審核公開的閒置設施回報。
        </p>
        <label v-if="markerOptions.length" class="fields">
          查看標記
          <select
            :value="activeMarker"
            @change="chooseMarker($event.target.value)"
          >
            <option value="">選擇地點或點擊地圖標記</option>
            <option
              v-for="point in markerOptions"
              :key="point.id"
              :value="point.id"
            >
              {{ point.name }}
            </option>
          </select>
        </label>
        <div v-if="selectedPlace" class="result" aria-live="polite">
          <strong>{{ selectedPlace.name }}</strong>
          <ul>
            <li v-for="facility in selectedPlace.facilities" :key="facility">
              {{ facilities[facility] }}
            </li>
          </ul>
          <p class="muted">
            標記為校方地圖上的建物位置。資料取得日
            {{ accessibility.retrieved }}。
          </p>
          <a
            :href="accessibility.source"
            target="_blank"
            rel="noopener noreferrer"
            >國立中央大學無障礙地圖</a
          >
        </div>
        <div v-if="selectedReport" class="result" aria-live="polite">
          <strong
            >{{ kinds[selectedReport.kind] }} ·
            {{ selectedReport.title }}</strong
          >
          <p>{{ selectedReport.details }}</p>
          <p v-if="selectedReport.road_closed">回報指出該處有道路封閉。</p>
          <p class="muted">
            來源：使用者回報（經管理員審核）。回報
            {{ formatTime(selectedReport.created_at) }}， 更新
            {{ formatTime(selectedReport.reviewed_at) }}。
          </p>
        </div>
        <button v-if="activeMarker" type="button" @click="emit('show-map')">
          查看地圖
        </button>
        <button type="button" @click="loadReports">重新載入回報標記</button>
      </template>

      <template v-else>
        <h2>登入與回報</h2>
        <CampusAccount />
        <template v-if="account">
          <RouterLink
            v-if="account.admin"
            class="admin-link"
            :to="{ name: 'campus-admin' }"
          >
            開啟回報管理
          </RouterLink>
          <form class="fields report-form" @submit.prevent="submitReport">
            <label>
              回報類別
              <select v-model="kind">
                <option v-for="(name, id) in kinds" :key="id" :value="id">
                  {{ name }}
                </option>
              </select>
            </label>
            <label>
              標題
              <input v-model.trim="title" required maxlength="80" />
            </label>
            <label>
              情況說明
              <textarea
                v-model.trim="details"
                required
                maxlength="1000"
                rows="3"
              />
            </label>
            <label>
              建物參考點
              <select
                :value="reportPlace"
                @change="chooseReportPlace($event.target.value)"
              >
                <option value="">選擇建物，或在地圖上選點</option>
                <option
                  v-for="place in places"
                  :key="place.id"
                  :value="place.id"
                >
                  {{ place.name }}
                </option>
              </select>
            </label>
            <button type="button" @click="emit('pick-location')">
              在地圖上選點
            </button>
            <p v-if="location" class="muted">
              選定位置 {{ location[1].toFixed(5) }},
              {{ location[0].toFixed(5) }}
            </p>
            <label v-if="kind === 'construction'" class="check">
              <input v-model="roadClosed" type="checkbox" />
              回報該處道路封閉
            </label>
            <p v-if="kind === 'construction' && roadClosed" class="muted">
              請在封閉路段上選點。審核公開後，路線會避開該處對應的 OSM 路段。
            </p>
            <p class="muted">
              標題、說明與位置經審核後可在地圖公開，請避免填寫個人資料。
            </p>
            <button class="primary" type="submit" :disabled="submitting">
              {{ submitting ? "送出中…" : "送出回報" }}
            </button>
          </form>
          <p v-if="reportError" role="alert">{{ reportError }}</p>
          <p v-if="submission" role="status">
            回報 #{{ submission }} 已送出，等待管理員審核。
          </p>
        </template>
        <p v-else class="muted">登入後可回報施工、毀壞與閒置設施。</p>
      </template>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, shallowRef, watch } from "vue";
import { useRoute } from "vue-router";
import CampusAccount from "./CampusAccount.vue";
import { createRoutePlanner } from "../map/walkingRoutes.js";
import {
  campusRequest,
  formatTime,
  kinds,
  loadCampusFile,
  useCampusAccount,
} from "../services/campusTools.js";

/* global defineProps, defineEmits */
const props = defineProps({
  mapPoint: { type: Array, default: null },
  mapMarker: { type: Object, default: null },
  resetCount: { type: Number, default: 0 },
  clearRouteCount: { type: Number, default: 0 },
});
const emit = defineEmits([
  "layers",
  "focus",
  "route-focus",
  "pick-location",
  "show-map",
]);
const route = useRoute();
const { session } = useCampusAccount();
const account = computed(() => session.value?.account);
const tools = [
  ["route", "路線規劃"],
  ["markers", "地圖標記"],
  ["report", "登入與回報"],
];
const panel = ref(route.query.login ? "report" : "");
const accessibility = shallowRef(null);
const network = shallowRef(null);
const planner = shallowRef(null);
const datasetError = ref("");
const reportsError = ref("");
const reports = ref([]);
const places = computed(() => accessibility.value?.places ?? []);

const start = ref("");
const end = ref("");
const mode = ref("walking");
const planned = shallowRef(null);
const planning = ref(false);
const routeError = ref("");
let routeRequest = 0;

const facilities = {
  elevator: "無障礙電梯",
  ramp: "無障礙坡道",
  toilet: "無障礙廁所",
  parking: "無障礙停車格",
};
const showAccessibility = ref(false);
const showIdle = ref(false);
const showOtherReports = ref(false);
const activeMarker = ref("");
const idleReports = computed(() =>
  reports.value.filter((report) => report.kind === "idle")
);
const accessibilityMarkers = computed(() =>
  showAccessibility.value
    ? places.value
        .filter((place) => place.facilities.length)
        .map((place) => ({
          id: "access:" + place.id,
          name: place.name,
          coordinates: place.coordinates,
          kind: "accessibility",
          label: "A",
        }))
    : []
);
const reportMarkers = computed(() =>
  reports.value
    .filter((report) =>
      report.kind === "idle" ? showIdle.value : showOtherReports.value
    )
    .map((report) => ({
      id: "report:" + report.id,
      name: kinds[report.kind] + " · " + report.title,
      coordinates: [report.longitude, report.latitude],
      kind: report.kind,
      label: { idle: "I", construction: "C", damage: "D" }[report.kind],
    }))
);
const markerOptions = computed(() => [
  ...accessibilityMarkers.value,
  ...reportMarkers.value,
]);
const selectedPlace = computed(() =>
  activeMarker.value.startsWith("access:")
    ? places.value.find((place) => place.id === activeMarker.value.slice(7))
    : null
);
const selectedReport = computed(() =>
  activeMarker.value.startsWith("report:")
    ? reports.value.find(
        (report) => String(report.id) === activeMarker.value.slice(7)
      )
    : null
);

const location = ref(null);
const reportPlace = ref("");
const kind = ref("construction");
const title = ref("");
const details = ref("");
const roadClosed = ref(false);
const reportError = ref("");
const submission = ref(null);
const submitting = ref(false);

watch(
  () => props.mapPoint,
  (point) => {
    if (!point) return;
    location.value = point;
    reportPlace.value = "";
    panel.value = "report";
  }
);
watch(
  () => props.mapMarker,
  (marker) => {
    if (!marker) return;
    activeMarker.value = marker.id;
    panel.value = "markers";
  }
);
watch(markerOptions, (markers) => {
  if (!markers.some((marker) => marker.id === activeMarker.value))
    activeMarker.value = "";
});
function clearRoute() {
  routeRequest += 1;
  planned.value = null;
  routeError.value = "";
  planning.value = false;
}
watch(
  [start, end, mode, () => props.resetCount, () => props.clearRouteCount],
  clearRoute
);
watch(panel, (value) => {
  if (value === "markers") loadReports();
});

const layers = computed(() => {
  const coordinates = planned.value?.coordinates ?? [];
  const points = [...markerOptions.value];
  if (coordinates.length) {
    points.push(
      {
        id: "start",
        kind: "route",
        label: "起點",
        coordinates: coordinates[0],
      },
      {
        id: "end",
        kind: "route",
        label: "終點",
        coordinates: coordinates[coordinates.length - 1],
      }
    );
  }
  if (location.value && account.value && panel.value === "report") {
    points.push({
      id: "draft",
      kind: "draft",
      label: "+",
      coordinates: location.value,
    });
  }
  return { route: coordinates, points };
});
watch(layers, (value) => emit("layers", value), { immediate: true });

async function loadReports() {
  try {
    reports.value = (await campusRequest("/reports/map")).reports;
    reportsError.value = "";
  } catch (error) {
    reportsError.value = error.message;
  }
}

async function planRoute() {
  planned.value = null;
  routeError.value = "";
  if (start.value === end.value) {
    routeError.value = "請選擇不同的起點及終點。";
    return;
  }
  const requestId = ++routeRequest;
  planning.value = true;
  try {
    await loadReports();
    if (requestId !== routeRequest) return;
    const result = planner.value.plan(
      places.value.find((place) => place.id === start.value).coordinates,
      places.value.find((place) => place.id === end.value).coordinates,
      mode.value,
      reports.value
    );
    if (!result) {
      routeError.value =
        mode.value === "wheelchair"
          ? "附近已記錄的道路經排除階梯與已知障礙後無法連通，請確認現場無障礙入口或改選步行參考。"
          : "起終點附近的已記錄道路無法連通，請確認校方入口資訊或選擇鄰近地點。";
      return;
    }
    planned.value = result;
    emit("route-focus", result.coordinates);
  } finally {
    if (requestId === routeRequest) planning.value = false;
  }
}

function percent(distance) {
  return Math.round((distance / planned.value.distance) * 100);
}

function chooseMarker(id) {
  activeMarker.value = id;
  const point = markerOptions.value.find((marker) => marker.id === id);
  if (point) emit("focus", point.coordinates);
}

function chooseReportPlace(id) {
  reportPlace.value = id;
  location.value =
    places.value.find((place) => place.id === id)?.coordinates ?? null;
  if (location.value) emit("focus", location.value);
}

async function submitReport() {
  reportError.value = "";
  submission.value = null;
  const closed = kind.value === "construction" && roadClosed.value;
  if (!location.value) {
    reportError.value = "請先選擇建物或在地圖上選點。";
    return;
  }
  if (
    closed &&
    (reportPlace.value || !planner.value?.nearestRoad(location.value))
  ) {
    reportError.value = "請使用地圖選點，並將標記放在已繪製的封閉路段上。";
    return;
  }
  submitting.value = true;
  try {
    const [longitude, latitude] = location.value;
    const result = await campusRequest("/reports", "POST", {
      kind: kind.value,
      title: title.value,
      details: details.value,
      longitude,
      latitude,
      road_closed: closed,
    });
    submission.value = result.id;
    title.value = "";
    details.value = "";
    chooseReportPlace("");
    roadClosed.value = false;
  } catch (error) {
    reportError.value = error.message;
  } finally {
    submitting.value = false;
  }
}

onMounted(async () => {
  const [access, walking] = await Promise.allSettled([
    loadCampusFile("campus-accessibility.json"),
    loadCampusFile("campus-walking-network.json"),
  ]);
  if (access.status === "fulfilled") accessibility.value = access.value;
  if (walking.status === "fulfilled") {
    network.value = walking.value;
    planner.value = createRoutePlanner(walking.value);
  }
  if (access.status === "rejected" || walking.status === "rejected") {
    datasetError.value = "部分校園地圖資料載入失敗，請重新整理後再試。";
  }
});
</script>

<style scoped>
.tools {
  margin-bottom: 14px;
  font-size: 0.875rem;
  line-height: 1.55;
}
.tool-nav {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}
.tools button,
.tools select,
.tools textarea,
.tools input:not([type="checkbox"]) {
  min-height: 44px;
  max-width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: var(--panel-soft);
  color: inherit;
}
.tools button:hover:not(:disabled),
.tools button[aria-expanded="true"],
.tools .primary {
  border-color: var(--glow);
  color: var(--glow);
}
.tools button:disabled {
  color: var(--muted);
  cursor: default;
}
.tool-panel {
  display: grid;
  gap: 10px;
  margin-top: 8px;
  padding: 13px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
}
.tool-panel h2 {
  font-size: 1rem;
  margin: 0;
}
.tool-panel p {
  margin: 0;
  overflow-wrap: anywhere;
}
.fields,
.fields > label:not(.check) {
  display: grid;
  gap: 7px;
  min-width: 0;
}
.fields select {
  width: 100%;
}
.fields textarea {
  resize: vertical;
}
.tool-panel fieldset {
  min-width: 0;
  margin: 0;
  padding: 0 8px 4px;
  border: 1px solid var(--line);
  border-radius: 5px;
}
.check {
  display: flex;
  align-items: center;
  min-height: 44px;
  gap: 7px;
}
.check input {
  accent-color: var(--glow);
}
.key {
  display: inline-grid;
  place-items: center;
  width: 21px;
  height: 21px;
  border-radius: 50%;
  color: #fff;
  font-weight: 600;
}
.access-key {
  background: #006cc6;
}
.idle-key {
  background: #7f48b4;
}
.result {
  display: grid;
  gap: 6px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: var(--panel-soft);
  overflow-wrap: anywhere;
}
.result ul {
  margin: 0;
  padding-left: 19px;
}
.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}
.muted {
  color: var(--muted);
}
.tool-panel a {
  color: var(--glow);
}
.admin-link {
  display: flex;
  align-items: center;
  min-height: 44px;
}
.report-form {
  padding-top: 10px;
  border-top: 1px solid var(--line);
}
</style>
