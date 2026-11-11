<template>
  <div class="map-shell">
    <div
      ref="container"
      class="map-container"
      aria-label="中央大學互動式 3D 地圖"
    ></div>
    <div v-if="error" class="map-message" role="alert">{{ error }}</div>
    <div v-else-if="loading" class="map-message" role="status">
      載入校園地圖中…
    </div>
    <div v-if="!loading && !error" class="construction-legend" role="status">
      <span class="construction-key">紅色建築：有施工相關公告</span>
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
import {
  addCampusLayers,
  loadCampusData,
  prepareBuildings,
  loadConstructionData,
  markConstructionBuildings,
} from "../map/layers";

// Vue compiler macros are global at runtime, and ESLint 7 needs explicit globals.
/* global defineProps, defineEmits */
const props = defineProps({ selectedId: { type: String, default: "" } });
const emit = defineEmits(["select", "loaded", "reset", "construction-loaded"]);
const container = ref(null);
const loading = ref(true);
const error = ref("");
const constructionStatus = ref("loading");
const constructionCount = ref(0);
const abortController = new AbortController();
// MapLibre's default worker URL is relative to its entry module. Vite hashes
// that module during build, so explicitly use the worker asset emitted by Vite.
setWorkerUrl(workerUrl);
let map;
let activeId = "";
let buildingLookup = new globalThis.Map();
const defaultView = {
  center: [121.1915503, 24.9684403], // Nominatim OSM relation 18727079
  zoom: 15.5,
  pitch: 55,
  bearing: -24,
};
// Outer extent of OSM National Central University multipolygon relation 18727079
// (outer ways 179149377, 1361161284, 1361161285). This is a bounding box,
// not the exact irregular campus boundary.
const campusBounds = [
  [121.1843596, 24.9635065],
  [121.1980519, 24.9722322],
];

function styleBasemap(mapInstance) {
  // Recolor the existing vector style only; all sources and feature geometry stay intact.
  const colors = {
    background: "#071522",
    water: "#0c3957",
    waterway: "#146087",
    landuse_park: "#103348",
    landcover_wood: "#103348",
    landcover_grass: "#12344b",
  };
  for (const layer of mapInstance.getStyle().layers || []) {
    if (layer.type === "symbol" || layer.type === "fill-extrusion") {
      mapInstance.setLayoutProperty(layer.id, "visibility", "none");
    } else if (colors[layer.id] && layer.type === "background") {
      mapInstance.setPaintProperty(layer.id, "background-color", colors[layer.id]);
    } else if (colors[layer.id] && layer.type === "fill") {
      mapInstance.setPaintProperty(layer.id, "fill-color", colors[layer.id]);
    } else if (colors[layer.id] && layer.type === "line") {
      mapInstance.setPaintProperty(layer.id, "line-color", colors[layer.id]);
    } else if (layer.id.startsWith("road_") && layer.type === "line") {
      mapInstance.setPaintProperty(layer.id, "line-color", "#245072");
    }
  }
}

function resetView() {
  if (map && !loading.value && !error.value) {
    updateSelection("");
    emit("reset");
    map.easeTo({ ...defaultView, duration: 800 });
  }
}

async function loadConstruction() {
  try {
    const data = await loadConstructionData(abortController.signal);
    if (abortController.signal.aborted) return;
    const ids = [...new Set(data.building_ids)].filter((id) =>
      buildingLookup.has(id)
    );
    markConstructionBuildings(map, ids);
    emit(
      "construction-loaded",
      data.announcements.filter((announcement) =>
        ids.includes(announcement?.location?.location_id)
      )
    );
    constructionCount.value = ids.length;
    constructionStatus.value = data.data_status;
  } catch {
    if (!abortController.signal.aborted) constructionStatus.value = "error";
  }
}

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
}

function focusBuilding(id) {
  const building = buildingLookup.get(id);
  if (!building || !map) return;
  const points = building.geometry.coordinates.flat(1);
  const bounds = points.reduce(
    (result, point) => result.extend(point),
    new LngLatBounds(points[0], points[0])
  );
  map.fitBounds(bounds, { padding: 120, maxZoom: 18, duration: 800 });
}

watch(
  () => props.selectedId,
  (id) => {
    updateSelection(id);
    if (id) focusBuilding(id);
  }
);

onMounted(async () => {
  try {
    const data = await loadCampusData(abortController.signal);
    if (abortController.signal.aborted) return;
    const preparedBuildings = prepareBuildings(data.buildings);
    buildingLookup = new globalThis.Map(
      preparedBuildings.features.map((feature) => [feature.properties.id, feature])
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
    map.addControl(new ScaleControl({ unit: "metric" }), "bottom-left");
    map.on("load", () => {
      styleBasemap(map);
      addCampusLayers(map, data);
      updateSelection(props.selectedId);
      loading.value = false;
      loadConstruction();
      emit("loaded", preparedBuildings.features);
      map.on("click", "campus-building-extrusion", (event) => {
        const feature = event.features?.[0];
        if (feature) emit("select", feature.properties.id);
      });
      map.on("mouseenter", "campus-building-extrusion", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "campus-building-extrusion", () => {
        map.getCanvas().style.cursor = "";
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
  abortController.abort();
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
.reset-view {
  position: absolute;
  z-index: 1;
  top: 118px;
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
.reset-view:hover:not(:disabled) {
  background: #1a4b75;
}
.reset-view:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.reset-view svg {
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
</style>
