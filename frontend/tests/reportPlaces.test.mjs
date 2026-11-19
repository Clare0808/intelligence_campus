import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { reportPlacesFromBuildings } from "../src/map/reportPlaces.js";

test("report options include every named map building, including dorm nine", async () => {
  const data = JSON.parse(await readFile(new URL("../public/data/buildings.geojson", import.meta.url), "utf8"));
  const places = reportPlacesFromBuildings(data.features);
  assert.equal(places.length, data.features.filter((f) => f.properties?.name?.trim()).length);
  assert.ok(places.some((p) => p.name === "男九舍"));
  assert.equal(new Set(places.map((p) => p.id)).size, places.length);
  assert.ok(places.every((p) => p.coordinates.every(Number.isFinite)));
});
