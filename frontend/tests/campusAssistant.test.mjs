import assert from "node:assert/strict";
import test from "node:test";
import {
  askCampusAssistant,
  useCampusAccount,
} from "../src/services/campusTools.js";

const account = useCampusAccount();

function mockFetch(responses) {
  const requests = [];
  globalThis.fetch = async (url, options) => {
    requests.push({ url, options });
    const response = responses.shift();
    assert.ok(response, "unexpected request");
    return {
      ok: response.status === 200,
      status: response.status,
      json: async () => response.data,
    };
  };
  return requests;
}

test("chat initializes an anonymous session before sending the CSRF-protected question", async () => {
  account.session.value = null;
  const originalFetch = globalThis.fetch;
  try {
    const requests = mockFetch([
      { status: 200, data: { account: null, csrf: "guest-token" } },
      { status: 200, data: { answer: "你好！" } },
    ]);
    assert.deepEqual(await askCampusAssistant("你好", []), { answer: "你好！" });
    assert.deepEqual(requests.map(({ url }) => url), [
      "/api/campus/session",
      "/api/campus/assistant/chat",
    ]);
    assert.equal(requests[1].options.headers["X-Campus-CSRF"], "guest-token");
    assert.equal(requests[1].options.credentials, "same-origin");
  } finally {
    globalThis.fetch = originalFetch;
    account.session.value = null;
  }
});

test("chat refreshes an expired session once and retries with the new token", async () => {
  account.session.value = { csrf: "old-token" };
  const originalFetch = globalThis.fetch;
  try {
    const requests = mockFetch([
      { status: 403, data: { message: "工作階段已更新，請重新整理頁面。" } },
      { status: 200, data: { account: null, csrf: "new-token" } },
      { status: 200, data: { answer: "可以使用路線規劃。" } },
    ]);
    assert.equal(
      (await askCampusAssistant("如何走？", [])).answer,
      "可以使用路線規劃。"
    );
    assert.deepEqual(requests.map(({ url }) => url), [
      "/api/campus/assistant/chat",
      "/api/campus/session",
      "/api/campus/assistant/chat",
    ]);
    assert.equal(requests[0].options.headers["X-Campus-CSRF"], "old-token");
    assert.equal(requests[2].options.headers["X-Campus-CSRF"], "new-token");
  } finally {
    globalThis.fetch = originalFetch;
    account.session.value = null;
  }
});

test("chat does not retry non-CSRF failures or retry repeatedly", async () => {
  const originalFetch = globalThis.fetch;
  try {
    account.session.value = { csrf: "token" };
    const unavailable = mockFetch([
      { status: 503, data: { message: "AI 助手尚未設定。" } },
    ]);
    await assert.rejects(askCampusAssistant("你好", []), /AI 助手尚未設定/);
    assert.equal(unavailable.length, 1);

    const invalid = mockFetch([
      { status: 403, data: { message: "工作階段已更新" } },
      { status: 200, data: { csrf: "new-token" } },
      { status: 403, data: { message: "工作階段已更新" } },
    ]);
    await assert.rejects(askCampusAssistant("你好", []), /工作階段已更新/);
    assert.equal(invalid.length, 3);
  } finally {
    globalThis.fetch = originalFetch;
    account.session.value = null;
  }
});