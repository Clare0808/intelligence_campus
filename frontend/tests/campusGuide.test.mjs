import assert from "node:assert/strict";
import test from "node:test";

import { campusGuideSteps } from "../src/data/campusGuide.js";

test("campus guide covers all major tools and ends with the replay control", () => {
  assert.deepEqual(
    campusGuideSteps.map((step) => step.panel),
    ["", "construction", "construction", "route", "markers", "report", "", ""]
  );
  assert.match(campusGuideSteps[0].description, /地圖/);
  assert.equal(campusGuideSteps[6].title, "AI 助手");
  assert.match(campusGuideSteps[6].description, /公告/);
  assert.match(campusGuideSteps.at(-1).description, /功能導覽/);
  assert.deepEqual(
    campusGuideSteps.map((step) => step.target),
    [
      "campus-building",
      "[data-guide='construction']",
      "#building-search",
      "[data-guide='route']",
      "[data-guide='markers']",
      "[data-guide='report']",
      ".assistant-trigger",
      ".guide-trigger",
    ]
  );
  for (const step of campusGuideSteps) {
    assert.ok(step.title);
    assert.ok(step.description);
  }
});
