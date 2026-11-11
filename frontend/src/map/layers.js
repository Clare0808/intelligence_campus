const emptyCollection = () => ({ type: "FeatureCollection", features: [] });

const metersPerFloor = 3;

function positiveNumber(value) {
  if (typeof value !== "number" && typeof value !== "string") return null;
  if (typeof value === "string" && !value.trim()) return null;
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? number : null;
}

export async function loadCampusData(signal) {
  const files = ["buildings", "roads"];
  const responses = await Promise.all(
    files.map((name) =>
      fetch(`${import.meta.env.BASE_URL}data/${name}.geojson`, { signal })
    )
  );
  for (const response of responses) {
    if (!response.ok)
      throw new Error(`GeoJSON 載入失敗：HTTP ${response.status}`);
  }
  const [buildings, roads] = await Promise.all(responses.map((r) => r.json()));
  if (
    buildings.type !== "FeatureCollection" ||
    roads.type !== "FeatureCollection"
  ) {
    throw new Error("GeoJSON 格式錯誤");
  }
  return { buildings, roads };
}

export function prepareBuildings(collection) {
  return {
    ...collection,
    features: collection.features.map((feature) => {
      const {
        height,
        min_height: minHeight,
        building_levels: levels,
      } = feature.properties;
      const measuredHeight = positiveNumber(height);
      const floorCount = positiveNumber(levels);
      const baseHeight = positiveNumber(minHeight);
      const isNonBuilding = levels === 0 || levels === "0";
      // 3 m / floor is only a visual estimate, not surveyed height.
      // Without any height evidence, 6 m is strictly a display placeholder.
      const displayHeight =
        isNonBuilding
          ? 0
          : measuredHeight !== null
          ? measuredHeight
          : floorCount !== null
          ? floorCount * metersPerFloor
          : 6;
      const displaySource =
        isNonBuilding
          ? "non_building"
          : measuredHeight !== null
          ? "osm"
          : floorCount !== null
          ? "levels_estimate"
          : "visual_placeholder";
      return {
        ...feature,
        properties: {
          ...feature.properties,
          display_height: displayHeight,
          display_min_height: isNonBuilding ? 0 : baseHeight ?? 0,
          display_source: displaySource,
        },
      };
    }),
  };
}

export function addCampusLayers(map, data) {
  map.addSource("campus-roads", { type: "geojson", data: data.roads });
  map.addLayer({
    id: "campus-roads-line",
    type: "line",
    source: "campus-roads",
    paint: {
      "line-color": "#d0905a",
      "line-opacity": 0.75,
      "line-width": ["interpolate", ["linear"], ["zoom"], 14, 1, 17, 3],
    },
  });

  map.addSource("campus-buildings", {
    type: "geojson",
    data: prepareBuildings(data.buildings),
    promoteId: "id",
  });
  map.addLayer({
    id: "campus-building-footprints",
    type: "line",
    source: "campus-buildings",
    paint: { "line-color": "#345947", "line-width": 1.3, "line-opacity": 0.85 },
  });
  map.addLayer({
    id: "campus-building-extrusion",
    type: "fill-extrusion",
    source: "campus-buildings",
    filter: ["!=", ["get", "display_source"], "non_building"],
    paint: {
      "fill-extrusion-color": [
        "case",
        ["boolean", ["feature-state", "selected"], false],
        "#e3914b",
        ["==", ["get", "display_source"], "visual_placeholder"],
        "#a7b5aa",
        ["==", ["get", "display_source"], "levels_estimate"],
        "#6a9778",
        "#456f5d",
      ],
      "fill-extrusion-height": ["get", "display_height"],
      "fill-extrusion-base": ["get", "display_min_height"],
      "fill-extrusion-opacity": 0.87,
    },
  });
}

// Each future dataset owns its own source and layers instead of extending the view.
export const futureLayers = {
  streetlights: emptyCollection,
  construction: emptyCollection,
  accessibility: emptyCollection,
  safety: emptyCollection,
};
