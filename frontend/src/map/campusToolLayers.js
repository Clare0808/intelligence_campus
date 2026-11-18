const empty = { type: "FeatureCollection", features: [] };

export function addToolLayers(map) {
  map.addSource("campus-tools-route", { type: "geojson", data: empty });
  map.addSource("campus-tools-points", { type: "geojson", data: empty });

  for (const [id, color, width] of [
    ["campus-tools-route-outline", "#14283e", 9],
    ["campus-tools-route-line", "#f8cd57", 5],
  ]) {
    map.addLayer({
      id,
      type: "line",
      source: "campus-tools-route",
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-color": color, "line-width": width },
    });
  }
  map.addLayer({
    id: "campus-tools-point",
    type: "circle",
    source: "campus-tools-points",
    paint: {
      "circle-color": [
        "match",
        ["get", "kind"],
        "accessibility",
        "#006cc6",
        "idle",
        "#7f48b4",
        "construction",
        "#b4492b",
        "damage",
        "#a23d63",
        "draft",
        "#00765d",
        "#253e56",
      ],
      "circle-radius": ["case", ["==", ["get", "kind"], "route"], 19, 12],
      "circle-stroke-color": "#fff",
      "circle-stroke-width": 2,
    },
  });
  map.addLayer({
    id: "campus-tools-point-label",
    type: "symbol",
    source: "campus-tools-points",
    layout: {
      "text-field": ["get", "label"],
      "text-size": 12,
      "text-font": ["Noto Sans Regular"],
      "text-allow-overlap": true,
    },
    paint: { "text-color": "#fff" },
  });
}

export function updateToolLayers(map, { route, points }) {
  map?.getSource("campus-tools-route")?.setData({
    ...empty,
    features: route.length
      ? [
          {
            type: "Feature",
            geometry: { type: "LineString", coordinates: route },
            properties: {},
          },
        ]
      : [],
  });
  map?.getSource("campus-tools-points")?.setData({
    ...empty,
    features: points.map(({ coordinates, ...properties }) => ({
      type: "Feature",
      geometry: { type: "Point", coordinates },
      properties,
    })),
  });
}
