<template>
  <div class="assistant" :class="{ 'assistant-light': theme === 'light' }">
    <section
      v-if="open"
      id="campus-assistant-chat"
      class="chat"
      aria-label="AI 助手聊天室"
    >
      <header class="chat-header">
        <div>
          <strong>校園 AI 助手</strong><small>施工資訊與地圖使用諮詢</small>
        </div>
        <button type="button" aria-label="關閉 AI 助手" @click="close">
          ✕
        </button>
      </header>
      <div
        ref="conversation"
        class="conversation"
        role="log"
        aria-label="對話紀錄"
        aria-live="polite"
      >
        <p v-if="!messages.length" class="welcome">
          你好！可以詢問校園施工資訊或地圖功能。現場狀況請以校方公告為準。
        </p>
        <div v-for="(turn, index) in turns" :key="index" class="turn">
          <div class="user-message">
            <p>{{ turn.question.content }}</p>
          </div>
          <div
            v-if="turn.answer || (loading && index === turns.length - 1)"
            class="assistant-message"
          >
            <span class="speaker">AI 助手</span>
            <p v-if="turn.answer">
              {{ turn.answer.content
              }}<span
                v-if="turn.answer.typing"
                class="cursor"
                aria-hidden="true"
                >▍</span
              >
            </p>
            <p v-else role="status" aria-label="AI 助手思考中">
              思考中<span class="thinking-dots" aria-hidden="true">...</span>
            </p>
          </div>
        </div>
      </div>
      <div class="composer">
        <div class="suggestions" aria-label="快速提問">
          <button
            v-for="question in suggestions"
            :key="question"
            type="button"
            :disabled="loading || typing"
            @click="send(question)"
          >
            {{ question }}
          </button>
        </div>
        <form @submit.prevent="send(draft)">
          <label class="sr-only" for="assistant-question">輸入問題</label>
          <input
            id="assistant-question"
            ref="input"
            v-model="draft"
            maxlength="500"
            placeholder="輸入問題…"
            :disabled="loading || typing"
          />
          <button type="submit" :disabled="!draft.trim() || loading || typing">
            傳送
          </button>
        </form>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <p class="disclaimer">AI 回答僅供參考，請確認官方公告與現場路況。</p>
      </div>
    </section>
    <button
      class="assistant-trigger"
      type="button"
      :aria-label="open ? '關閉 AI 助手' : '開啟 AI 助手'"
      :aria-expanded="open"
      aria-controls="campus-assistant-chat"
      :disabled="disabled"
      @click="open ? close() : show()"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
        focusable="false"
      >
        <path d="M4 5.5h16v11H9l-5 3v-14Z" />
        <path d="M8 10h8M8 13h5" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref } from "vue";
import { askCampusAssistant } from "../services/campusTools.js";

/* global defineProps */
defineProps({
  theme: { type: String, default: "dark" },
  disabled: { type: Boolean, default: false },
});

const suggestions = ["目前有哪些施工資訊？", "如何使用路線規劃？"];
const open = ref(false);
const draft = ref("");
const messages = ref([]);
const turns = computed(() => {
  const result = [];
  for (const message of messages.value) {
    if (message.role === "user")
      result.push({ question: message, answer: null });
    else if (result.length) result[result.length - 1].answer = message;
  }
  return result;
});
const loading = ref(false);
const typing = ref(false);
const error = ref("");
const conversation = ref(null);
const input = ref(null);
let timer;
let requestId = 0;

async function scrollToLatestQuestion() {
  await nextTick();
  const log = conversation.value;
  const latest = log?.querySelector(".turn:last-child");
  if (latest) log.scrollTop = latest.offsetTop - log.offsetTop;
}

async function show() {
  open.value = true;
  await nextTick();
  await scrollToLatestQuestion();
  input.value?.focus();
}

function close() {
  open.value = false;
  requestId += 1;
  loading.value = false;
  clearInterval(timer);
  typing.value = false;
  for (const message of messages.value) {
    if (!message.typing) continue;
    message.content = "回覆已中斷，請重新提問。";
    message.typing = false;
  }
}

function typeAnswer(answer) {
  const letters = Array.from(answer);
  const message = { role: "assistant", content: "", typing: true };
  messages.value.push(message);
  typing.value = true;
  let position = 0;
  timer = setInterval(() => {
    message.content += letters.slice(position, position + 3).join("");
    position += 3;
    if (position >= letters.length) {
      clearInterval(timer);
      message.typing = false;
      typing.value = false;
      input.value?.focus();
    }
  }, 25);
}

async function send(value) {
  const question = value.trim();
  if (!question || question.length > 500 || loading.value || typing.value)
    return;
  const history = messages.value
    .filter(
      ({ role, content }) =>
        role === "user" ||
        (role === "assistant" && content !== "回覆已中斷，請重新提問。")
    )
    .slice(-8)
    .map(({ role, content }) => ({ role, content }));
  draft.value = "";
  error.value = "";
  messages.value.push({ role: "user", content: question });
  loading.value = true;
  scrollToLatestQuestion();
  const id = ++requestId;
  try {
    const { answer } = await askCampusAssistant(question, history);
    if (id === requestId) {
      if (typeof answer !== "string" || !answer.trim())
        throw new Error("AI 助手未傳回有效答覆。");
      typeAnswer(answer);
    }
  } catch (cause) {
    if (id === requestId) {
      error.value = cause.message || "AI 助手暫時無法回答。";
    }
  } finally {
    if (id === requestId) loading.value = false;
  }
}

onBeforeUnmount(() => {
  requestId += 1;
  clearInterval(timer);
});
</script>

<style scoped>
.assistant {
  position: absolute;
  z-index: 4;
  right: 16px;
  bottom: 46px;
  display: grid;
  justify-items: end;
  gap: 10px;
  color: #17252d;
  --chat-panel: #fffdf5;
  --chat-soft: #eaf1f4;
  --chat-line: #b5c4cc;
  --chat-accent: #205b77;
}
.assistant-light {
  color: #e5f6ff;
  --chat-panel: #091b31;
  --chat-soft: #123759;
  --chat-line: #35678a;
  --chat-accent: #73d9ff;
}
.assistant button {
  cursor: pointer;
  font: inherit;
}
.assistant button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
.assistant-trigger {
  display: grid;
  place-items: center;
  width: 54px;
  height: 54px;
  border: 1px solid var(--chat-line);
  border-radius: 50%;
  background: var(--chat-panel);
  color: var(--chat-accent);
  box-shadow: 0 6px 22px #020b1880;
}
.assistant-trigger svg {
  width: 27px;
  height: 27px;
}
.chat {
  display: flex;
  flex-direction: column;
  width: min(370px, calc(100vw - 32px));
  height: min(530px, calc(100dvh - 100px));
  min-height: 260px;
  overflow: hidden;
  border: 1px solid var(--chat-line);
  border-radius: 12px;
  background: var(--chat-panel);
  box-shadow: 0 12px 38px #020b18a6;
}
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--chat-line);
}
.chat-header div {
  display: grid;
  gap: 3px;
}
.chat-header small,
.disclaimer,
.speaker {
  font-size: 11px;
  opacity: 0.8;
}
.chat-header button {
  border: 0;
  background: transparent;
  color: inherit;
  font-size: 18px;
}
.conversation {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 18px 16px 24px;
  font-size: 14px;
  line-height: 1.7;
}
.welcome {
  margin: 0;
  color: var(--chat-accent);
}
.turn + .turn {
  margin-top: 30px;
}
.user-message {
  width: fit-content;
  max-width: 85%;
  margin-left: auto;
  padding: 9px 14px;
  border-radius: 18px 18px 4px 18px;
  background: var(--chat-soft);
}
.assistant-message {
  margin-top: 18px;
  padding: 0 4px;
}
.assistant-message .speaker {
  display: block;
  color: var(--chat-accent);
  font-size: 12px;
  font-weight: 700;
  opacity: 1;
}
.user-message p,
.assistant-message p {
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.assistant-message p {
  margin-top: 6px;
}
.cursor {
  color: var(--chat-accent);
  animation: cursor-blink 0.8s steps(1) infinite;
}
.thinking-dots {
  display: inline-block;
  width: 1.5em;
  overflow: hidden;
  vertical-align: bottom;
  white-space: nowrap;
  animation: thinking-dots 1.2s steps(4, end) infinite;
}
@keyframes cursor-blink {
  50% {
    opacity: 0;
  }
}
@keyframes thinking-dots {
  from {
    width: 0;
  }
  to {
    width: 1.5em;
  }
}
.composer {
  padding: 12px;
  border-top: 1px solid var(--chat-line);
}
.suggestions {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 10px;
}
.suggestions button {
  flex: 0 0 auto;
  padding: 6px 9px;
  border: 1px solid var(--chat-line);
  border-radius: 16px;
  background: var(--chat-soft);
  color: inherit;
  font-size: 12px;
}
.composer form {
  display: flex;
  gap: 6px;
}
.composer input {
  min-width: 0;
  flex: 1;
  padding: 10px;
  border: 1px solid var(--chat-line);
  border-radius: 7px;
  background: var(--chat-soft);
  color: inherit;
}
.composer form button {
  padding: 6px 12px;
  border: 1px solid var(--chat-line);
  border-radius: 7px;
  background: var(--chat-accent);
  color: var(--chat-panel);
}
.error {
  margin: 8px 0 0;
  color: #ffb3a5;
  font-size: 12px;
}
.assistant-light .error {
  color: #a12727;
}
.disclaimer {
  margin: 8px 0 0;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}
@media (prefers-reduced-motion: reduce) {
  .cursor {
    display: none;
  }
  .thinking-dots {
    animation: none;
  }
}
</style>
