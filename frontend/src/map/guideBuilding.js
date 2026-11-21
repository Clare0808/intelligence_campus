// Prefer an actual rendered campus building in the visible map area over a fixed screen coordinate.
export function findGuideBuildingRect(map, sidebarWidth = 0) {
  const container = map.getContainer();
  const { width, height, left, top } = container.getBoundingClientRect();
  const visibleLeft = Math.max(0, sidebarWidth);
  const visibleWidth = width - visibleLeft;
  if (visibleWidth < 100 || height < 100) return null;

  const center = { x: visibleLeft + visibleWidth / 2, y: height * 0.43 };
  const layers = ["campus-building-extrusion", "campus-building-flat"];
  const candidates = map.queryRenderedFeatures(
    [
      [visibleLeft + 24, height * 0.16],
      [width - 24, height * 0.68],
    ],
    { layers }
  );
  const seen = new Set();
  const buildings = candidates
    .filter((feature) => {
      const id = feature.properties?.id;
      if (!feature.properties?.name || !id || seen.has(id)) return false;
      seen.add(id);
      return true;
    })
    .map((feature) => {
      const coordinates = feature.geometry.coordinates.flat(
        feature.geometry.type === "MultiPolygon" ? 2 : 1
      );
      if (!coordinates.length) return null;
      const projected = coordinates.map((point) => map.project(point));
      const xs = projected.map((point) => point.x);
      const ys = projected.map((point) => point.y);
      const x = (Math.min(...xs) + Math.max(...xs)) / 2;
      const y = (Math.min(...ys) + Math.max(...ys)) / 2;
      return { x, y, distance: Math.hypot(x - center.x, y - center.y) };
    })
    .filter(
      (building) =>
        building &&
        building.x > visibleLeft + 32 &&
        building.x < width - 32 &&
        building.y > height * 0.18 &&
        building.y < height * 0.65
    )
    .sort((a, b) => a.distance - b.distance);

  if (!buildings.length) return null;
  const { x, y } = buildings[0];
  const radius = 24;
  return {
    left: `${left + x - radius}px`,
    top: `${top + y - radius}px`,
    width: `${radius * 2}px`,
    height: `${radius * 2}px`,
  };
}
