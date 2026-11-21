import assert from "node:assert/strict";
import test from "node:test";

import { findGuideBuildingRect } from "../src/map/guideBuilding.js";

const building = (id, name, x, y) => ({
  properties: { id, name },
  geometry: {
    type: "Polygon",
    coordinates: [
      [
        [x - 10, y - 10],
        [x + 10, y - 10],
        [x + 10, y + 10],
        [x - 10, y + 10],
        [x - 10, y - 10],
      ],
    ],
  },
});

test("guide spotlight follows a rendered, named building outside the sidebar", () => {
  const map = {
    getContainer: () => ({
      getBoundingClientRect: () => ({
        width: 1000,
        height: 800,
        left: 10,
        top: 20,
      }),
    }),
    queryRenderedFeatures: () => [
      building("hidden", "側欄後方", 160, 350),
      building("visible", "圖書館", 700, 340),
    ],
    project: ([x, y]) => ({ x, y }),
  };

  assert.deepEqual(findGuideBuildingRect(map, 350), {
    left: "686px",
    top: "336px",
    width: "48px",
    height: "48px",
  });
});

test("guide does not spotlight an arbitrary location when no building is visible", () => {
  const map = {
    getContainer: () => ({
      getBoundingClientRect: () => ({
        width: 1000,
        height: 800,
        left: 0,
        top: 0,
      }),
    }),
    queryRenderedFeatures: () => [building("hidden", "側欄後方", 160, 350)],
    project: ([x, y]) => ({ x, y }),
  };
  assert.equal(findGuideBuildingRect(map, 350), null);
});
