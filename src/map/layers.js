const emptyCollection = () => ({ type: "FeatureCollection", features: [] });

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
      // 3 m / floor is only a visual estimate, not surveyed height.
      // Without any height evidence, 6 m is strictly a display placeholder.
      const displayHeight =
        height !== null && Number.isFinite(height)
          ? height
          : levels !== null && Number.isFinite(levels)
          ? levels * 3
          : 6;
      const displaySource =
        height !== null && Number.isFinite(height)
          ? "osm"
          : levels !== null && Number.isFinite(levels)
          ? "levels_estimate"
          : "visual_placeholder";
      return {
        ...feature,
        properties: {
          ...feature.properties,
          display_height: displayHeight,
          display_min_height:
            minHeight !== null && Number.isFinite(minHeight) ? minHeight : 0,
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
