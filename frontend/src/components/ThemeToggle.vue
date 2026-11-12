<template>
  <button
    ref="button"
    class="theme-toggle"
    type="button"
    :aria-label="theme === 'dark' ? '切換至淺色模式' : '切換至深色模式'"
    :title="theme === 'dark' ? '切換至淺色模式' : '切換至深色模式'"
    :disabled="disabled"
    @click="toggleTheme"
  >
    <svg
      v-if="theme === 'dark'"
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
    >
      <circle cx="12" cy="12" r="4" />
      <path
        d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"
      />
    </svg>
    <svg v-else viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5a8.5 8.5 0 1 0 10.7 10.7Z" />
    </svg>
  </button>
</template>

<script setup>
import { ref } from "vue";

/* global defineProps, defineEmits */
const props = defineProps({
  theme: { type: String, required: true },
});
const emit = defineEmits(["change"]);
const button = ref(null);
const disabled = ref(false);

async function toggleTheme() {
  if (disabled.value) return;
  const nextTheme = props.theme === "dark" ? "light" : "dark";
  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;
  if (!document.startViewTransition || reducedMotion) {
    emit("change", nextTheme);
    return;
  }

  disabled.value = true;
  const rect = button.value.getBoundingClientRect();
  const x = rect.left + rect.width / 2;
  const y = rect.top + rect.height / 2;
  const radius = Math.hypot(
    Math.max(x, window.innerWidth - x),
    Math.max(y, window.innerHeight - y)
  );
  try {
    const transition = document.startViewTransition(() =>
      emit("change", nextTheme)
    );
    await transition.ready;
    document.documentElement.animate(
      {
        clipPath: [
          `circle(0px at ${x}px ${y}px)`,
          `circle(${radius}px at ${x}px ${y}px)`,
        ],
      },
      {
        duration: 400,
        easing: "ease-in-out",
        pseudoElement: "::view-transition-new(root)",
      }
    );
    await transition.finished;
  } catch {
    // View transitions can be interrupted by navigation; the theme is already updated.
  } finally {
    disabled.value = false;
  }
}
</script>
