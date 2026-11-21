import assert from "node:assert/strict";
import test from "node:test";

import {
  notification,
  showNotification,
} from "../src/services/notifications.js";

test("success notifications replace the previous message with a new id", () => {
  showNotification("登入成功！");
  const first = notification.value;
  assert.equal(first.message, "登入成功！");
  assert.equal(first.type, "success");

  showNotification("請填寫標題。", "error");
  assert.equal(notification.value.message, "請填寫標題。");
  assert.equal(notification.value.type, "error");
  assert.ok(notification.value.id > first.id);

  showNotification("回報 #12 已送出，等待管理員審核。");
  assert.equal(notification.value.type, "success");
  notification.value = null;
});