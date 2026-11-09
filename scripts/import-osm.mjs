import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";

// Import a small bounding-box export from https://api.openstreetmap.org/api/0.6/map?bbox=...
// OSM XML uses WGS84 coordinates, the coordinate system required by GeoJSON.
const input = resolve(process.argv[2] || "osm-campus.osm");
const output = resolve(process.argv[3] || "public/data");
const xml = readFileSync(input, "utf8");
const decode = (text) =>
  text
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&");
const attributes = (tag) =>
  Object.fromEntries(
    [...tag.matchAll(/([\w:]+)="([^"]*)"/g)].map((match) => [
      match[1],
      decode(match[2]),
    ])
  );
const tagsOf = (body) =>
  Object.fromEntries(
    [...body.matchAll(/<tag\s+([^>]*?)\s*\/>/g)].map((match) => {
      const { k, v } = attributes(match[1]);
      return [k, v];
    })
  );
const nodes = new Map();
for (const match of xml.matchAll(
  /<node\s+([^>]*?)(?:\/>|>([\s\S]*?)<\/node>)/g
)) {
  const { id, lat, lon } = attributes(match[1]);
  nodes.set(id, [Number(lon), Number(lat)]);
}

const buildings = [];
const roads = [];
const buildingParts = [];
const timestamp = new Date().toISOString().slice(0, 10);
const heightValue = (raw) => {
  // OSM height tags can include units or lists. Only plain numbers in metres
  // are converted; all other formats remain unknown rather than guessed.
  if (!raw || !/^\d+(?:\.\d+)?(?:\s*m)?$/.test(raw.trim())) return null;
  return Number(raw.trim().replace(/\s*m$/, ""));
};

for (const match of xml.matchAll(/<way\s+([^>]*?)>([\s\S]*?)<\/way>/g)) {
  const way = attributes(match[1]);
  const tags = tagsOf(match[2]);
  if (!tags.building && !tags.highway) continue;
  const references = [...match[2].matchAll(/<nd\s+ref="(\d+)"\s*\/>/g)].map(
    (entry) => entry[1]
  );
  const coordinates = references.map((ref) => nodes.get(ref));
  if (coordinates.some((point) => !point)) continue;

  if (
    tags.building &&
    coordinates.length >= 4 &&
    references[0] === references.at(-1)
  ) {
    const feature = {
      type: "Feature",
      id: `way/${way.id}`,
      properties: {
        id: `way/${way.id}`,
        name: tags["name:zh"] || tags.name || tags["name:en"] || null,
        height: heightValue(tags.height),
        min_height: heightValue(tags.min_height),
        building_levels: tags["building:levels"]
          ? Number(tags["building:levels"]) || null
          : null,
        height_source:
          heightValue(tags.height) !== null ? "OSM height tag" : null,
        data_source: "OpenStreetMap contributors",
        osm_url: `https://www.openstreetmap.org/way/${way.id}`,
        building: tags.building,
      },
      geometry: { type: "Polygon", coordinates: [coordinates] },
    };
    if (tags["building:part"]) buildingParts.push(feature);
    else buildings.push(feature);
  }

  if (tags.highway && coordinates.length >= 2) {
    roads.push({
      type: "Feature",
      id: `way/${way.id}`,
      properties: {
        id: `way/${way.id}`,
        name: tags["name:zh"] || tags.name || null,
        highway: tags.highway,
        access: tags.access || null,
        data_source: "OpenStreetMap contributors",
        osm_url: `https://www.openstreetmap.org/way/${way.id}`,
      },
      geometry: { type: "LineString", coordinates },
    });
  }
}

// Only parts with explicitly supplied heights are overlaid. Avoid drawing a
// building part and its parent as two coincident 3D volumes with guessed data.
const knownParts = buildingParts.filter(
  (part) => part.properties.height !== null
);
const collection = (features) => ({ type: "FeatureCollection", features });
mkdirSync(output, { recursive: true });
for (const [name, features] of [
  ["buildings", [...buildings, ...knownParts]],
  ["roads", roads],
]) {
  const path = resolve(output, `${name}.geojson`);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(collection(features))}\n`);
}
console.log(
  JSON.stringify({
    source: input,
    imported: timestamp,
    buildings: buildings.length,
    named: buildings.filter((f) => f.properties.name).length,
    knownHeights: buildings.filter((f) => f.properties.height !== null).length,
    knownLevels: buildings.filter((f) => f.properties.building_levels !== null)
      .length,
    roads: roads.length,
    buildingParts: knownParts.length,
  })
);
