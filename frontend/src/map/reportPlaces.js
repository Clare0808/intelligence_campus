// Reference points use the same bounding-box center as building map focus.
export function reportPlacesFromBuildings(features) {
  return features
    .flatMap((feature, index) => {
      const name = feature.properties?.name?.trim();
      const geometry = feature.geometry;
      if (!name || !geometry) return [];
      const points = [];
      function collect(value) {
        if (!Array.isArray(value)) return;
        if (typeof value[0] === "number") {
          if (value.length >= 2 && value.slice(0, 2).every(Number.isFinite)) {
            points.push(value);
          }
        } else value.forEach(collect);
      }
      collect(geometry.coordinates);
      if (!points.length) return [];
      const lng = points.map((point) => point[0]);
      const lat = points.map((point) => point[1]);
      return [
        {
          id: String(
            feature.properties.id ?? feature.id ?? `building-${index}`
          ),
          name,
          coordinates: [
            (Math.min(...lng) + Math.max(...lng)) / 2,
            (Math.min(...lat) + Math.max(...lat)) / 2,
          ],
        },
      ];
    })
    .sort((a, b) => a.name.localeCompare(b.name, "zh-Hant", { numeric: true }));
}
