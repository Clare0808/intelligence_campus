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
import { addCampusLayers, loadCampusData } from "../map/layers";

// Vue compiler macros are global at runtime, and ESLint 7 needs explicit globals.
/* global defineProps, defineEmits */
const props = defineProps({ selectedId: { type: String, default: "" } });
const emit = defineEmits(["select", "loaded"]);
const container = ref(null);
const loading = ref(true);
const error = ref("");
const abortController = new AbortController();
// MapLibre's default worker URL is relative to its entry module. Vite hashes
// that module during build, so explicitly use the worker asset emitted by Vite.
setWorkerUrl(workerUrl);
let map;
let activeId = "";
let buildingLookup = new globalThis.Map();

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
    buildingLookup = new globalThis.Map(
      data.buildings.features.map((feature) => [feature.properties.id, feature])
    );
    map = new Map({
      container: container.value,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: [121.1915503, 24.9684403], // Nominatim OSM relation 18727079
      zoom: 15.5,
      pitch: 55,
      bearing: -24,
      maxPitch: 85,
      antialias: true,
    });
    map.addControl(
      new NavigationControl({ visualizePitch: true }),
      "top-right"
    );
    map.addControl(new ScaleControl({ unit: "metric" }), "bottom-left");
    map.on("load", () => {
      // Remove basemap's own building extrusions to avoid double rendering.
      for (const layer of map.getStyle().layers || []) {
        if (layer.type === "fill-extrusion")
          map.setLayoutProperty(layer.id, "visibility", "none");
      }
      addCampusLayers(map, data);
      updateSelection(props.selectedId);
      loading.value = false;
      emit("loaded", data.buildings.features);
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
.map-message {
  position: absolute;
  top: 16px;
  left: 16px;
  max-width: 65%;
  padding: 12px;
  border-radius: 8px;
  background: white;
  color: #294532;
  box-shadow: 0 4px 20px #0002;
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
