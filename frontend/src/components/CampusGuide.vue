<template>
  <button
    ref="trigger"
    class="guide-trigger"
    :class="{ 'guide-trigger-light': theme === 'light' }"
    type="button"
    aria-label="開啟功能導覽"
    title="開啟功能導覽"
    :aria-expanded="open"
    aria-controls="campus-guide"
    :disabled="disabled"
    @click="start"
  >
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        d="M12 6.5C9.7 5 6.8 4.8 3 5.5v13c3.8-.7 6.7-.5 9 1 2.3-1.5 5.2-1.7 9-1v-13c-3.8-.7-6.7-.5-9 1Z"
      />
      <path d="M12 6.5v13" />
    </svg>
  </button>
  <Teleport to="body">
    <div v-if="open" class="guide-backdrop" :class="themeClass">
      <div class="guide-shield" aria-hidden="true"></div>
      <div v-if="!spotlight" class="guide-dim" aria-hidden="true"></div>
      <div
        v-if="spotlight"
        class="guide-spotlight"
        :style="spotlight"
        aria-hidden="true"
      ></div>
      <section
        id="campus-guide"
        ref="dialog"
        class="guide-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="guide-title"
        aria-describedby="guide-description"
        tabindex="-1"
        @keydown="onKeydown"
      >
        <p class="guide-progress">
          功能導覽 {{ index + 1 }} / {{ steps.length }}
        </p>
        <h2 id="guide-title">{{ steps[index].title }}</h2>
        <p id="guide-description">{{ steps[index].description }}</p>
        <div class="guide-actions">
          <button v-if="!isLast" type="button" @click="finish">略過</button>
          <button v-if="index > 0" type="button" @click="previous">
            上一步
          </button>
          <button v-if="!isLast" class="guide-next" type="button" @click="next">
            下一步
          </button>
          <button v-else class="guide-next" type="button" @click="finish">
            關閉
          </button>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import { campusGuideSteps } from "../data/campusGuide.js";

/* global defineProps, defineEmits */
const props = defineProps({
  disabled: { type: Boolean, default: false },
  theme: { type: String, default: "dark" },
  buildingSpotlight: { type: Object, default: null },
});
const emit = defineEmits(["open", "step-change", "close"]);
const steps = campusGuideSteps;
const storageKey = "campus-guide-seen";
const open = ref(false);
const index = ref(0);
const dialog = ref(null);
const trigger = ref(null);
const spotlight = ref(null);
const isLast = computed(() => index.value === steps.length - 1);
const themeClass = computed(() =>
  props.theme === "light" ? "guide-light" : ""
);
let previousFocus;
let targetElement;
let observer;
let frame;

function updateSpotlight() {
  if (steps[index.value].target === "campus-building") {
    spotlight.value = props.buildingSpotlight;
    return;
  }
  if (!open.value || !targetElement?.isConnected) return;
  const rect = targetElement.getBoundingClientRect();
  const gap = 5;
  if (
    rect.bottom <= 0 ||
    rect.top >= window.innerHeight ||
    rect.right <= 0 ||
    rect.left >= window.innerWidth
  ) {
    spotlight.value = null;
    return;
  }
  const left = Math.max(0, rect.left - gap);
  const top = Math.max(0, rect.top - gap);
  const right = Math.min(window.innerWidth, rect.right + gap);
  const bottom = Math.min(window.innerHeight, rect.bottom + gap);
  spotlight.value = {
    left: `${left}px`,
    top: `${top}px`,
    width: `${Math.max(0, right - left)}px`,
    height: `${Math.max(0, bottom - top)}px`,
  };
}

function queueSpotlight() {
  window.cancelAnimationFrame(frame);
  frame = window.requestAnimationFrame(updateSpotlight);
}

async function focusTarget() {
  await nextTick();
  if (!open.value) return;
  observer?.disconnect();
  if (steps[index.value].target === "campus-building") {
    targetElement = null;
    updateSpotlight();
    return;
  }
  targetElement = document.querySelector(steps[index.value].target);
  if (!targetElement) {
    spotlight.value = null;
    return;
  }
  if (targetElement !== trigger.value && targetElement.closest(".sidebar")) {
    targetElement.scrollIntoView({ block: "nearest", inline: "nearest" });
  }
  observer = new ResizeObserver(queueSpotlight);
  observer.observe(targetElement);
  queueSpotlight();
}

function showStep() {
  spotlight.value = null;
  emit("step-change", steps[index.value]);
  focusTarget();
  nextTick(() => dialog.value?.focus());
}

function start() {
  if (open.value || props.disabled) return;
  previousFocus = document.activeElement;
  index.value = 0;
  open.value = true;
  emit("open");
  try {
    localStorage.setItem(storageKey, "true");
  } catch {
    // The guide remains available even when storage is disabled.
  }
  showStep();
}

function finish() {
  open.value = false;
  spotlight.value = null;
  observer?.disconnect();
  window.cancelAnimationFrame(frame);
  targetElement = null;
  emit("close");
  nextTick(() => {
    const target = previousFocus?.isConnected ? previousFocus : trigger.value;
    if (!target?.closest("[inert]")) target?.focus();
  });
}

function next() {
  if (isLast.value) return finish();
  index.value += 1;
  showStep();
}

function previous() {
  if (!index.value) return;
  index.value -= 1;
  showStep();
}

function onKeydown(event) {
  if (event.key === "Escape") {
    event.stopPropagation();
    finish();
  }
  if (event.key !== "Tab") return;
  const buttons = [...dialog.value.querySelectorAll("button")];
  const first = buttons[0];
  const last = buttons[buttons.length - 1];
  if (
    event.shiftKey &&
    (document.activeElement === first ||
      document.activeElement === dialog.value)
  ) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function openOnFirstVisit() {
  try {
    if (localStorage.getItem(storageKey) === "true") return;
  } catch {
    // First visit still displays the guide when storage is unavailable.
  }
  start();
}

onMounted(() => {
  window.addEventListener("resize", queueSpotlight);
  window.addEventListener("scroll", queueSpotlight, true);
  if (!props.disabled) openOnFirstVisit();
});
watch(
  () => props.disabled,
  (disabled) => {
    if (disabled && open.value) finish();
    else if (!disabled) openOnFirstVisit();
  }
);
watch(
  () => props.buildingSpotlight,
  () => {
    if (open.value && steps[index.value].target === "campus-building") {
      updateSpotlight();
    }
  }
);
onBeforeUnmount(() => {
  window.removeEventListener("resize", queueSpotlight);
  window.removeEventListener("scroll", queueSpotlight, true);
  observer?.disconnect();
  window.cancelAnimationFrame(frame);
  if (
    open.value &&
    previousFocus?.isConnected &&
    !previousFocus.closest("[inert]")
  ) {
    previousFocus.focus();
  }
});
</script>

<style scoped>
.guide-trigger {
  position: absolute;
  z-index: 3;
  top: 196px;
  right: 10px;
  display: grid;
  place-items: center;
  width: 29px;
  height: 29px;
  padding: 5px;
  border: 1px solid #35678a;
  border-radius: 3px;
  background: #102f50;
  color: #73d9ff;
  cursor: pointer;
}
.guide-trigger svg {
  width: 19px;
  height: 19px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.guide-trigger:hover:not(:disabled) {
  background: #1a4b75;
}
.guide-trigger-light {
  border-color: #b5c4cc;
  background: #fff;
  color: #17252d;
  box-shadow: 0 4px 18px #364b5b30;
}
.guide-trigger-light:hover:not(:disabled) {
  background: #eaf1f4;
}
.guide-trigger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.guide-trigger:focus-visible,
.guide-dialog button:focus-visible {
  outline: 2px solid var(--glow);
  outline-offset: 2px;
}
.guide-backdrop {
  --panel: #091b31;
  --panel-soft: #0c2642;
  --line: #35678a;
  --glow: #58c8fa;
  color: #e5f6ff;
  position: fixed;
  z-index: 1001;
  inset: 0;
  display: grid;
  place-items: end center;
  padding: 20px;
  pointer-events: none;
}
.guide-shield {
  position: fixed;
  inset: 0;
  pointer-events: auto;
}
.guide-dim {
  position: fixed;
  inset: 0;
  background: rgba(3, 14, 27, 0.72);
}
.guide-spotlight {
  position: fixed;
  border-radius: 6px;
  box-shadow: 0 0 0 9999px rgba(3, 14, 27, 0.72), 0 0 0 3px var(--glow);
  pointer-events: none;
}
.guide-backdrop.guide-light {
  --panel: #fff;
  --panel-soft: #eef2f4;
  --line: #b5c4cc;
  --glow: #205b77;
  color: #17252d;
}
.guide-dialog {
  position: relative;
  z-index: 1;
  pointer-events: auto;
  width: min(100%, 420px);
  max-height: calc(100dvh - 40px);
  overflow-y: auto;
  padding: 22px;
  border: 1px solid var(--glow);
  border-radius: 10px;
  background: var(--panel);
  box-shadow: 0 12px 36px #020b18aa;
  color: inherit;
}
.guide-progress {
  margin: 0 0 10px;
  color: var(--glow);
  font-size: 13px;
  font-weight: 700;
}
.guide-dialog h2 {
  margin: 0 0 10px;
  font-size: 20px;
}
.guide-dialog #guide-description {
  margin: 0;
  line-height: 1.7;
}
.guide-actions {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 20px;
}
.guide-actions button {
  min-height: 44px;
  padding: 8px 12px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--panel-soft);
  color: inherit;
  cursor: pointer;
}
.guide-actions .guide-next {
  border-color: var(--glow);
  color: var(--glow);
  font-weight: 700;
}
@media (max-width: 520px) {
  .guide-backdrop {
    padding: 12px;
  }
  .guide-dialog {
    max-height: calc(100dvh - 24px);
  }
}
</style>
