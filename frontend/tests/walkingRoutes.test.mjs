import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import {
  createRoutePlanner,
  distanceMeters,
  walkingNetworkGeoJSON,
} from "../src/map/walkingRoutes.js";

function network(nodes, ways) {
  return {
    nodes: Object.fromEntries(
      Object.entries(nodes).map(([id, point]) => [id, [...point, {}]])
    ),
    ways,
  };
}

test("projects endpoints onto an original road segment", () => {
  const data = network({ 1: [0, 0], 2: [0.001, 0] }, [
    { id: 1, nodes: [1, 2], tags: { highway: "footway" } },
  ]);
  const result = createRoutePlanner(data).plan(
    [0.0002, 0.00003],
    [0.0008, 0.00003],
    "walking",
    []
  );
  assert.ok(result);
  assert.ok(
    Math.abs(result.distance - distanceMeters([0.0002, 0], [0.0008, 0])) < 0.001
  );
  assert.deepEqual(result.osmWayIds, [1]);
  assert.equal(result.coordinates[0][1], 0);
  assert.equal(result.coordinates.at(-1)[1], 0);
});

test("a building can use a nearby connected road without drawing a connector", () => {
  const data = network(
    { 1: [0, 0], 2: [0.001, 0], 3: [0.0007, 0.00015], 4: [0.0008, 0.00015] },
    [
      { id: 1, nodes: [1, 2], tags: { highway: "footway" } },
      { id: 2, nodes: [3, 4], tags: { highway: "service" } },
    ]
  );
  const result = createRoutePlanner(data).plan(
    [0, 0],
    [0.00075, 0.00014],
    "walking",
    []
  );
  assert.ok(result);
  assert.ok(result.osmWayIds.every((id) => id === 1));
  assert.ok(result.coordinates.every((point) => point[1] === 0));
  assert.ok(result.endOffset > 10);
});

test("exact road endpoints on disconnected components stay disconnected", () => {
  const data = network(
    { 1: [0, 0], 2: [0.0002, 0], 3: [0.0005, 0], 4: [0.0007, 0] },
    [
      { id: 1, nodes: [1, 2], tags: { highway: "footway" } },
      { id: 2, nodes: [3, 4], tags: { highway: "footway" } },
    ]
  );
  assert.equal(
    createRoutePlanner(data).plan([0, 0], [0.0007, 0], "walking", []),
    null
  );
});

const alternativeNetwork = () =>
  network({ 1: [0, 0], 2: [0.0002, 0], 3: [0.0001, 0.0002] }, [
    { id: 1, nodes: [1, 2], tags: { highway: "steps", lit: "no" } },
    {
      id: 2,
      nodes: [1, 3, 2],
      tags: { highway: "footway", wheelchair: "yes", lit: "yes" },
    },
  ]);

test("wheelchair and lighting preferences use the eligible OSM alternative", () => {
  const planner = createRoutePlanner(alternativeNetwork());
  assert.ok(
    planner.plan([0, 0], [0.0002, 0], "walking", []).osmWayIds.includes(1)
  );
  for (const mode of ["wheelchair", "night"]) {
    const result = planner.plan([0, 0], [0.0002, 0], mode, []);
    assert.ok(result.osmWayIds.every((id) => id === 2));
  }
});

test("private and explicitly forbidden pedestrian roads are excluded", () => {
  for (const tags of [{ access: "private" }, { foot: "no" }]) {
    const data = alternativeNetwork();
    data.ways[0].tags = { highway: "service", ...tags };
    const result = createRoutePlanner(data).plan(
      [0, 0],
      [0.0002, 0],
      "walking",
      []
    );
    assert.ok(result.osmWayIds.every((id) => id === 2));
  }
});

test("a reviewed road-closure point removes its matched segment", () => {
  const result = createRoutePlanner(alternativeNetwork()).plan(
    [0, 0],
    [0.0002, 0],
    "walking",
    [
      {
        kind: "construction",
        road_closed: true,
        longitude: 0.0001,
        latitude: 0,
      },
    ]
  );
  assert.ok(result.osmWayIds.every((id) => id === 2));
});

test("chooses the shortest complete route instead of the nearest road projection", () => {
  const data = network(
    {
      1: [0, 0],
      2: [0.001, 0],
      3: [0, 0.0001],
      4: [0.001, 0.0001],
    },
    [
      { id: 1, nodes: [1, 2], tags: { highway: "footway" } },
      { id: 2, nodes: [3, 4], tags: { highway: "footway" } },
      { id: 3, nodes: [1, 3], tags: { highway: "footway" } },
      { id: 4, nodes: [2, 4], tags: { highway: "footway" } },
    ]
  );
  const result = createRoutePlanner(data).plan(
    [0.0001, 0.000045],
    [0.0009, 0.0001],
    "walking",
    []
  );
  assert.ok(result);
  assert.ok(result.osmWayIds.every((id) => id === 2));
  assert.ok(result.distance < 90);
});

test("a closure forces the shortest remaining detour and cannot be used as an endpoint", () => {
  const data = alternativeNetwork();
  const planner = createRoutePlanner(data);
  const closure = [{
    kind: "construction",
    road_closed: true,
    longitude: 0.0001,
    latitude: 0,
  }];
  const result = planner.plan([0, 0], [0.0002, 0], "walking", closure);
  assert.ok(result);
  assert.ok(result.osmWayIds.every((id) => id === 2));
  assert.equal(
    planner.plan([0.0001, 0], [0.0002, 0], "walking", closure)?.osmWayIds.includes(1),
    false
  );
});

function onSegment(point, a, b) {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const length = dx * dx + dy * dy;
  const ratio = length
    ? ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length
    : 0;
  const closest = [a[0] + ratio * dx, a[1] + ratio * dy];
  return (
    ratio >= -0.000001 &&
    ratio <= 1.000001 &&
    distanceMeters(point, closest) < 0.02
  );
}

test("all campus place pairs use only the same original OSM segments drawn on the map", () => {
  const data = JSON.parse(
    fs.readFileSync(
      new URL("../public/data/campus-walking-network.json", import.meta.url)
    )
  );
  const { places } = JSON.parse(
    fs.readFileSync(
      new URL("../public/data/campus-accessibility.json", import.meta.url)
    )
  );
  const roads = walkingNetworkGeoJSON(data);
  const geometry = new Map(
    roads.features.map((feature) => [
      Number(feature.properties.id.slice(4)),
      feature.geometry.coordinates,
    ])
  );
  const planner = createRoutePlanner(data);
  let checked = 0;
  const disconnected = [];
  for (const mode of ["walking", "wheelchair", "night"]) {
    for (const start of places) {
      for (const end of places) {
        if (start.id === end.id) continue;
        const result = planner.plan(
          start.coordinates,
          end.coordinates,
          mode,
          []
        );
        if (!result) {
          disconnected.push([mode, start.name, end.name]);
          continue;
        }
        assert.ok(Number.isFinite(result.distance) && result.distance > 0);
        assert.ok(result.startOffset <= 120 && result.endOffset <= 120);
        assert.equal(result.osmWayIds.length, result.coordinates.length - 1);
        for (let i = 0; i < result.osmWayIds.length; i += 1) {
          const road = geometry.get(result.osmWayIds[i]);
          assert.ok(
            road
              .slice(1)
              .some(
                (b, index) =>
                  onSegment(result.coordinates[i], road[index], b) &&
                  onSegment(result.coordinates[i + 1], road[index], b)
              ),
            "A route edge must lie on one recorded road segment"
          );
        }
        checked += 1;
      }
    }
  }
  console.log(JSON.stringify({ checked, disconnected }));
  assert.equal(disconnected.length, 0);
  assert.equal(checked, places.length * (places.length - 1) * 3);
});
