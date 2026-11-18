<template>
  <div class="map-shell" :class="{ 'theme-light': theme === 'light' }">
    <div
      ref="container"
      class="map-container"
      :aria-label="
        viewMode === '3d' ? '中央大學互動式 3D 地圖' : '中央大學互動式平面地圖'
      "
    ></div>
    <div
      v-if="selectedLabel && labelPosition"
      class="building-label"
      :style="{ left: labelPosition.x + 'px', top: labelPosition.y + 'px' }"
      role="group"
      aria-label="選取建物名稱"
    >
      <button
        type="button"
        :aria-label="selectedLabel.name + '，再點一次回到預設視角'"
        @click="emit('select', selectedId)"
      >
        <strong>{{ selectedLabel.name }}</strong>
        <span v-if="selectedLabel.aliases.length" class="building-aliases"
          >別名：{{ selectedLabel.aliases.join("、") }}</span
        >
        <span v-if="selectedLabel.englishName" class="building-english">{{
          selectedLabel.englishName
        }}</span>
        <small>再點一次，回到預設視角</small>
      </button>
      <a
        v-if="selectedLabel.source"
        :href="selectedLabel.source"
        target="_blank"
        rel="noopener noreferrer"
        >名稱來源 ↗</a
      >
    </div>
    <div v-if="error" class="map-message" role="alert">{{ error }}</div>
    <div v-else-if="loading" class="map-message" role="status">
      載入校園地圖中…
    </div>
    <div v-if="!loading && !error" class="construction-legend" role="status">
      <span class="construction-key">紅色建築：兩週內施工中或即將施工</span>
      <span v-if="constructionStatus === 'loading'">施工資料載入中…</span>
      <span v-else-if="constructionStatus === 'error'"
        >施工資訊暫時無法取得</span
      >
      <span v-else-if="constructionStatus === 'missing'">尚無施工公告資料</span>
      <span v-else>已標記 {{ constructionCount }} 棟建築</span>
    </div>
    <button
      class="reset-view"
      type="button"
      title="回到預設視角"
      aria-label="回到預設視角"
      :disabled="loading || !!error"
      @click="resetView"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M4 11a8 8 0 1 1 2.3 6.1" />
        <path d="M4 5v6h6" />
      </svg>
      <span>回歸視角</span>
    </button>
    <ThemeToggle :theme="theme" @change="emit('theme-change', $event)" />
    <button
      v-if="toolLayers?.route?.length"
      class="clear-route"
      type="button"
      @click="emit('clear-route')"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="m6 6 12 12M18 6 6 18" />
      </svg>
      <span>清除路線</span>
    </button>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from "vue";
import {
  Map,
  NavigationControl,
  ScaleControl,
  LngLatBounds,
  setWorkerUrl,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import ThemeToggle from "./ThemeToggle.vue";
import { addToolLayers, updateToolLayers } from "../map/campusToolLayers.js";
import { buildingLabel } from "../map/buildingLabels.js";
import {
  addCampusLayers,
  loadCampusData,
  prepareBuildings,
  loadConstructionData,
  markConstructionBuildings,
} from "../map/layers";

// Vue compiler macros are global at runtime, and ESLint 7 needs explicit globals.
/* global defineProps, defineEmits */
const props = defineProps({
  selectedId: { type: String, default: "" },
  sidebarOpen: { type: Boolean, default: false },
  constructionVersion: { type: Number, default: 0 },
  theme: { type: String, default: "dark" },
  toolLayers: { type: Object, default: null },
  toolFocus: { type: Object, default: null },
  pickingLocation: { type: Boolean, default: false },
});
const emit = defineEmits([
  "select",
  "loaded",
  "reset",
  "clear-route",
  "construction-loaded",
  "theme-change",
  "tool-point",
  "tool-marker",
]);
const container = ref(null);
const loading = ref(true);
const error = ref("");
const constructionStatus = ref("loading");
const constructionCount = ref(0);
const viewMode = ref("3d");
const selectedLabel = ref(null);
const labelPosition = ref(null);
const abortController = new AbortController();
// MapLibre's default worker URL is relative to its entry module. Vite hashes
// that module during build, so explicitly use the worker asset emitted by Vite.
setWorkerUrl(workerUrl);
let map;
let compassButton;
let activeId = "";
let markedConstructionIds = [];
let buildingLookup = new globalThis.Map();
let basemapLayerIds = [];
let darkBasemapPaint = new globalThis.Map();
let basemapReady = false;
let constructionTimer;
let loadingConstruction = false;
const defaultView = {
  center: [121.1915503, 24.9684403], // Nominatim OSM relation 18727079
  zoom: 15.5,
  pitch: 55,
  bearing: -24,
};
let saved3dOrientation = {
  pitch: defaultView.pitch,
  bearing: defaultView.bearing,
};
// Outer extent of OSM National Central University multipolygon relation 18727079
// (outer ways 179149377, 1361161284, 1361161285). This is a bounding box,
// not the exact irregular campus boundary.
const campusBounds = [
  [121.1843596, 24.9635065],
  [121.1980519, 24.9722322],
];
const darkColors = {
  background: "#071522",
  water: "#0c3957",
  waterway: "#146087",
  landuse_park: "#103348",
  landcover_wood: "#103348",
  landcover_grass: "#12344b",
};
const lightColors = {
  background: "#f5f6f1",
  water: "#b8dce8",
  waterway: "#96c9dc",
  landuse_park: "#d5e8cb",
  landcover_wood: "#c7debf",
  landcover_grass: "#dfebd4",
  landuse_residential: "#e7e7e2",
};
// OpenFreeMap publishes dark and bright styles, but no /styles/light endpoint.
// Recoloring its existing vector layers keeps the campus sources and feature state.

function styleBasemap(mapInstance, theme) {
  // Recolor the existing vector style only; all sources and feature geometry stay intact.
  const colors = theme === "light" ? lightColors : darkColors;
  for (const id of basemapLayerIds) {
    const layer = mapInstance.getLayer(id);
    if (!layer) continue;
    if (layer.type === "symbol" || layer.type === "fill-extrusion") {
      mapInstance.setLayoutProperty(id, "visibility", "none");
    } else if (colors[id] && layer.type === "background") {
      mapInstance.setPaintProperty(id, "background-color", colors[id]);
    } else if (colors[id] && layer.type === "fill") {
      mapInstance.setPaintProperty(id, "fill-color", colors[id]);
    } else if (colors[id] && layer.type === "line") {
      mapInstance.setPaintProperty(id, "line-color", colors[id]);
    } else if (id === "road_pier" && layer.type === "line") {
      mapInstance.setPaintProperty(
        id,
        "line-color",
        theme === "light" ? "#354953" : "#245072"
      );
    } else if (id.startsWith("highway_") && layer.type === "line") {
      mapInstance.setPaintProperty(
        id,
        "line-color",
        theme === "light" ? "#354953" : darkBasemapPaint.get(id)
      );
    } else if (id === "building" && layer.type === "fill") {
      mapInstance.setPaintProperty(
        id,
        "fill-color",
        theme === "light" ? "#e3e5e3" : darkBasemapPaint.get(id)
      );
    } else if (id === "road_area_pier" && layer.type === "fill") {
      mapInstance.setPaintProperty(
        id,
        "fill-color",
        theme === "light" ? "#e3e5e3" : darkBasemapPaint.get(id)
      );
    }
  }
  if (mapInstance.getLayer("campus-roads-line")) {
    mapInstance.setPaintProperty(
      "campus-roads-line",
      "line-color",
      theme === "light" ? "#354953" : "#48c4df"
    );
  }
}

watch(
  () => props.theme,
  (value) => {
    if (basemapReady) styleBasemap(map, value);
  }
);

function resetView() {
  if (map && !loading.value && !error.value) {
    updateSelection("");
    emit("reset");
    restoreDefaultView();
  }
}

function restoreDefaultView() {
  map.stop();
  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;
  saved3dOrientation = {
    pitch: defaultView.pitch,
    bearing: defaultView.bearing,
  };
  map.easeTo({
    ...defaultView,
    padding: { top: 0, bottom: 0, left: 0, right: 0 },
    ...(viewMode.value === "2d"
      ? { pitch: 0, bearing: 0 }
      : saved3dOrientation),
    duration: reducedMotion ? 0 : 800,
  });
}

function updateCompassLabel() {
  if (!compassButton) return;
  const label =
    viewMode.value === "3d"
      ? "指北針：切換至平面地圖"
      : "指北針：切換至 3D 地圖";
  compassButton.title = label;
  compassButton.setAttribute("aria-label", label);
}

function toggleViewMode(event) {
  // Capture the existing control's click before its default north-reset handler.
  event.preventDefault();
  event.stopImmediatePropagation();
  if (!map || loading.value || error.value) return;
  map.stop();
  if (viewMode.value === "3d") {
    saved3dOrientation = { pitch: map.getPitch(), bearing: map.getBearing() };
  }
  viewMode.value = viewMode.value === "3d" ? "2d" : "3d";
  updateCompassLabel();
  const flat = viewMode.value === "2d";
  map.setMaxPitch(flat ? 0 : 85);
  map.setLayoutProperty(
    "campus-building-flat",
    "visibility",
    flat ? "visible" : "none"
  );
  map.setLayoutProperty(
    "campus-building-extrusion",
    "visibility",
    flat ? "none" : "visible"
  );
  map.easeTo({
    ...(flat ? { pitch: 0, bearing: 0 } : saved3dOrientation),
    duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? 0
      : 500,
  });
}

async function loadConstruction() {
  if (loadingConstruction || !map?.getSource("campus-buildings")) return;
  loadingConstruction = true;
  try {
    const data = await loadConstructionData(abortController.signal);
    if (abortController.signal.aborted) return;
    const ids = [...new Set(data.building_ids)].filter((id) =>
      buildingLookup.has(id)
    );
    for (const id of markedConstructionIds) {
      map.setFeatureState(
        { source: "campus-buildings", id },
        { construction: false }
      );
    }
    markConstructionBuildings(map, ids);
    markedConstructionIds = ids;
    emit("construction-loaded", data.announcements, data.refresh);
    constructionCount.value = ids.length;
    constructionStatus.value = data.data_status;
  } catch {
    if (!abortController.signal.aborted) constructionStatus.value = "error";
  } finally {
    loadingConstruction = false;
  }
}

watch(() => props.constructionVersion, loadConstruction);

watch(
  () => props.toolLayers,
  (value) => {
    if (value) updateToolLayers(map, value);
  }
);

watch(
  () => props.toolFocus,
  (value) => {
    if (!map || loading.value || !value) return;
    const duration = window.matchMedia("(prefers-reduced-motion: reduce)")
      .matches
      ? 0
      : 600;
    if (value.route) {
      const bounds = new LngLatBounds();
      for (const point of value.route) bounds.extend(point);
      map.fitBounds(bounds, { padding: 50, maxZoom: 17.5, duration });
    } else {
      map.easeTo({
        center: value.point,
        zoom: Math.max(map.getZoom(), 17),
        duration,
      });
    }
  }
);

watch(
  () => props.pickingLocation,
  (value) => {
    if (map) map.getCanvas().style.cursor = value ? "crosshair" : "";
  }
);

function updateSelection(id) {
  if (!map?.getSource("campus-buildings")) return;
  if (activeId)
    map.setFeatureState(
      { source: "campus-buildings", id: activeId },
      { selected: false }
    );
  activeId = id;
  if (id)
    map.setFeatureState({ source: "campus-buildings", id }, { selected: true });
  const building = buildingLookup.get(id);
  selectedLabel.value = building ? buildingLabel(building.properties) : null;
  updateBuildingLabelPosition();
}

function buildingBounds(id) {
  const building = buildingLookup.get(id);
  if (!building) return null;
  const points = building.geometry.coordinates.flat(
    building.geometry.type === "MultiPolygon" ? 2 : 1
  );
  return points.reduce(
    (result, point) => result.extend(point),
    new LngLatBounds(points[0], points[0])
  );
}

function updateBuildingLabelPosition() {
  const bounds = buildingBounds(activeId);
  if (!map || !bounds) {
    labelPosition.value = null;
    return;
  }
  const point = map.project(bounds.getCenter());
  const { clientWidth: width, clientHeight: height } = map.getContainer();
  labelPosition.value =
    point.x > 0 && point.x < width && point.y > 0 && point.y < height
      ? { x: point.x, y: point.y }
      : null;
}

function focusBuilding(id) {
  const bounds = buildingBounds(id);
  if (!bounds || !map) return;
  const { clientWidth: width, clientHeight: height } = map.getContainer();
  const sidebarWidth = props.sidebarOpen
    ? Math.min(width <= 520 ? 340 : 350, width - 40)
    : 0;
  const horizontal = Math.min(80, Math.max(24, (width - sidebarWidth) * 0.12));
  const vertical = Math.min(110, height * 0.18);
  map.stop();
  map.fitBounds(bounds, {
    padding: {
      left: sidebarWidth + horizontal,
      right: horizontal,
      top: vertical + 50,
      bottom: vertical,
    },
    maxZoom: 18,
    duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ? 0
      : 800,
  });
}

watch([() => props.selectedId, () => props.sidebarOpen], ([id]) => {
  const hadSelection = Boolean(activeId);
  updateSelection(id);
  if (id) focusBuilding(id);
  else if (hadSelection) restoreDefaultView();
});

onMounted(async () => {
  try {
    const data = await loadCampusData(abortController.signal);
    if (abortController.signal.aborted) return;
    const preparedBuildings = prepareBuildings(data.buildings);
    buildingLookup = new globalThis.Map(
      preparedBuildings.features.map((feature) => [
        feature.properties.id,
        feature,
      ])
    );
    map = new Map({
      container: container.value,
      style: "https://tiles.openfreemap.org/styles/dark",
      ...defaultView,
      minZoom: 15,
      maxZoom: 18,
      maxBounds: campusBounds,
      maxPitch: 85,
      antialias: true,
    });
    map.addControl(
      new NavigationControl({ visualizePitch: true }),
      "top-right"
    );
    compassButton = map
      .getContainer()
      .querySelector(".maplibregl-ctrl-compass");
    if (compassButton) {
      compassButton.disabled = true;
      updateCompassLabel();
      compassButton.addEventListener("click", toggleViewMode, true);
    }
    map.addControl(new ScaleControl({ unit: "metric" }), "bottom-left");
    map.on("move", updateBuildingLabelPosition);
    map.on("resize", updateBuildingLabelPosition);
    map.on("load", () => {
      const basemapLayers = map.getStyle().layers;
      basemapLayerIds = basemapLayers.map((layer) => layer.id);
      darkBasemapPaint = new globalThis.Map(
        basemapLayers.map((layer) => [
          layer.id,
          layer.paint?.[layer.type === "fill" ? "fill-color" : "line-color"],
        ])
      );
      basemapReady = true;
      styleBasemap(map, props.theme);
      addCampusLayers(map, data);
      styleBasemap(map, props.theme);
      addToolLayers(map);
      if (props.toolLayers) updateToolLayers(map, props.toolLayers);
      updateSelection(props.selectedId);
      loading.value = false;
      if (compassButton) compassButton.disabled = false;
      loadConstruction();
      constructionTimer = window.setInterval(loadConstruction, 60_000);
      emit("loaded", preparedBuildings.features);
      const markerAt = (event) =>
        map
          .queryRenderedFeatures(event.point, {
            layers: ["campus-tools-point"],
          })
          .find((feature) =>
            ["accessibility", "idle", "construction", "damage"].includes(
              feature.properties.kind
            )
          );
      map.on("click", (event) => {
        if (props.pickingLocation) {
          emit("tool-point", [event.lngLat.lng, event.lngLat.lat]);
          return;
        }
        const marker = markerAt(event);
        if (marker) emit("tool-marker", { id: marker.properties.id });
      });
      const buildingLayers = [
        "campus-building-extrusion",
        "campus-building-flat",
      ];
      map.on("click", buildingLayers, (event) => {
        if (props.pickingLocation || markerAt(event)) return;
        const feature = event.features?.[0];
        if (feature) emit("select", feature.properties.id);
      });
      map.on("mouseenter", buildingLayers, () => {
        if (!props.pickingLocation) map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", buildingLayers, () => {
        if (!props.pickingLocation) map.getCanvas().style.cursor = "";
      });
      map.on("mouseenter", "campus-tools-point", () => {
        if (!props.pickingLocation) map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "campus-tools-point", () => {
        if (!props.pickingLocation) map.getCanvas().style.cursor = "";
      });
    });
    map.on("error", (event) => {
      if (loading.value)
        error.value = `地圖載入失敗：${
          event.error?.message || "請檢查網路連線"
        }`;
    });
  } catch (cause) {
    if (!abortController.signal.aborted) error.value = cause.message;
  }
});

onBeforeUnmount(() => {
  window.clearInterval(constructionTimer);
  abortController.abort();
  compassButton?.removeEventListener("click", toggleViewMode, true);
  map?.remove();
});
</script>

<style scoped>
.map-shell {
  position: relative;
  width: 100%;
  height: 100%;
}
.map-container {
  width: 100%;
  height: 100%;
}
.reset-view,
.clear-route,
.map-shell :deep(.theme-toggle) {
  position: absolute;
  z-index: 1;
  right: 10px;
  display: grid;
  place-items: center;
  width: 29px;
  height: 29px;
  padding: 5px;
  border: 1px solid #35678a;
  border-radius: 3px;
  background: #102f50;
  color: #73d9ff;
  cursor: pointer;
}
.reset-view {
  top: 118px;
  width: auto;
  height: 36px;
  grid-auto-flow: column;
  gap: 5px;
  padding: 5px 8px;
  font-size: 12px;
}
.clear-route {
  bottom: 48px;
  grid-auto-flow: column;
  gap: 5px;
  width: auto;
  height: 44px;
  padding: 6px 10px;
  font-size: 13px;
}
.building-label {
  position: absolute;
  z-index: 1;
  width: max-content;
  max-width: min(240px, calc(100% - 60px));
  transform: translate(-50%, calc(-100% - 18px));
  border: 1px solid #58c8fa;
  border-radius: 10px;
  background: #102f50;
  color: #e5f6ff;
  box-shadow: 0 5px 22px #020b1866;
  text-align: center;
}
.building-label::after {
  position: absolute;
  top: 100%;
  left: calc(50% - 7px);
  border: 7px solid transparent;
  border-top-color: #58c8fa;
  content: "";
  pointer-events: none;
}
.building-label button {
  display: grid;
  gap: 4px;
  width: 100%;
  min-height: 44px;
  padding: 12px 16px;
  border: 0;
  border-radius: 10px;
  background: none;
  color: inherit;
  text-align: center;
  overflow-wrap: anywhere;
}
.building-label button:hover {
  background: #1a4b75;
}
.building-label strong {
  font-size: 16px;
  line-height: 1.5;
}
.building-aliases {
  color: #91e0ff;
  font-size: 13px;
}
.building-english {
  color: #c3d9e6;
  font-size: 12px;
}
.building-label small {
  margin-top: 4px;
  color: #c3d9e6;
  font-size: 12px;
}
.building-label a {
  display: inline-block;
  padding: 0 12px 10px;
  color: #91e0ff;
  font-size: 12px;
}
.theme-light .building-label {
  background: #fffdf5;
  color: #302c20;
  border-color: #9b8555;
  box-shadow: 0 5px 22px #364b5b30;
}
.theme-light .building-label::after {
  border-top-color: #9b8555;
}
.theme-light .building-label button:hover {
  background: #f5ecd7;
}
.theme-light .building-aliases,
.theme-light .building-label a {
  color: #715719;
}
.theme-light .building-english,
.theme-light .building-label small {
  color: #5e5a4b;
}
.map-shell :deep(.theme-toggle) {
  top: 157px;
}
.map-shell :deep(.theme-toggle:disabled) {
  cursor: wait;
}
.reset-view:hover:not(:disabled),
.clear-route:hover {
  background: #1a4b75;
}
.map-shell :deep(.theme-toggle:hover:not(:disabled)) {
  background: #1a4b75;
}
.reset-view:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.reset-view svg,
.clear-route svg,
.map-shell :deep(.theme-toggle svg) {
  width: 19px;
  height: 19px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.map-message {
  position: absolute;
  top: 16px;
  left: 16px;
  max-width: 65%;
  padding: 12px;
  border: 1px solid #35678a;
  border-radius: 3px;
  background: rgba(9, 27, 49, 0.97);
  color: #dceef6;
  box-shadow: 0 4px 20px #07182777;
}
.map-shell :deep(.maplibregl-ctrl-group) {
  border: 1px solid #35678a;
  border-radius: 3px;
  background: #102f50;
  box-shadow: 0 4px 18px #020b1877;
}
.map-shell :deep(.maplibregl-ctrl-group button) {
  background-color: transparent;
  border-color: #35678a;
}
.map-shell :deep(.maplibregl-ctrl-group button:hover) {
  background-color: #1a4b75;
}
.map-shell :deep(.maplibregl-ctrl-group button span) {
  filter: invert(1) sepia(1) saturate(3) hue-rotate(160deg);
}
.map-shell :deep(.maplibregl-ctrl-scale) {
  border-color: #73d9ff;
  background: #102f50e8;
  color: #dceef6;
}
.construction-legend {
  position: absolute;
  z-index: 1;
  top: 10px;
  right: 59px;
  display: grid;
  gap: 4px;
  max-width: calc(100% - 95px);
  padding: 9px 12px;
  border: 1px solid #35678a;
  border-radius: 3px;
  background: #102f50;
  color: #dceef6;
  box-shadow: 0 4px 18px #020b1877;
  font-size: 12px;
  line-height: 1.5;
}
.construction-legend span + span {
  color: #73d9ff;
  font-size: 11px;
}
.construction-key::before {
  content: "";
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-right: 6px;
  border-radius: 2px;
  background: #ff4b48;
}
.map-credit {
  position: absolute;
  right: 5px;
  bottom: 5px;
  padding: 3px 6px;
  background: #ffffffe8;
  color: #46574b;
  font-size: 10px;
}
.map-credit a {
  color: #285743;
}
.theme-light .reset-view,
.theme-light .clear-route,
.theme-light :deep(.theme-toggle),
.theme-light .construction-legend,
.theme-light :deep(.maplibregl-ctrl-group) {
  border-color: #b5c4cc;
  background: #fff;
  color: #17252d;
  box-shadow: 0 4px 18px #364b5b30;
}
.theme-light .reset-view:hover:not(:disabled),
.theme-light .clear-route:hover,
.theme-light :deep(.theme-toggle:hover:not(:disabled)),
.theme-light :deep(.maplibregl-ctrl-group button:hover) {
  background: #eaf1f4;
}
.theme-light :deep(.maplibregl-ctrl-group button) {
  border-color: #b5c4cc;
}
.theme-light :deep(.maplibregl-ctrl-group button span) {
  filter: none;
}
.theme-light :deep(.maplibregl-ctrl-scale) {
  border-color: #17252d;
  background: #fff;
  color: #17252d;
}
.theme-light .construction-legend span + span {
  color: #205b77;
}
.theme-light .map-message {
  border-color: #b5c4cc;
  background: #fff;
  color: #17252d;
}
</style>
