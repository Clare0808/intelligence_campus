<template>
  <Transition name="success-notification">
    <div
      v-if="visible"
      :key="visible.id"
      class="success-notification"
      :class="{ 'notification-error': visible.type === 'error' }"
      :role="visible.type === 'error' ? 'alert' : 'status'"
      :aria-live="visible.type === 'error' ? 'assertive' : 'polite'"
    >
      {{ visible.message }}
    </div>
  </Transition>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from "vue";
import { notification } from "../services/notifications.js";

const visible = ref(null);
let timer;

watch(notification, (value) => {
  window.clearTimeout(timer);
  visible.value = value;
  if (value) {
    timer = window.setTimeout(() => {
      visible.value = null;
      notification.value = null;
    }, 2000);
  }
});

onBeforeUnmount(() => window.clearTimeout(timer));
</script>

<style scoped>
.success-notification {
  position: fixed;
  top: 10px;
  left: 50%;
  z-index: 10000;
  max-width: min(360px, calc(100vw - 32px));
  padding: 14px 20px;
  border: 1px solid #1c762b;
  border-radius: 10px;
  background: #7cdf9a;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.25);
  color: #1c762b;
  font-size: 0.95rem;
  line-height: 1.5;
  pointer-events: none;
  transform: translateX(-50%);
}

.notification-error {
  color: #a12727;
  border-color: #a12727;
  background: #efa1a9;
}

.success-notification-enter-active,
.success-notification-leave-active {
  transition: all 300ms ease;
}

.success-notification-enter-from,
.success-notification-leave-to {
  transform: translate(-50%, calc(-100% - 32px));
  opacity: 0;
}

@media (max-width: 480px) {
  .success-notification {
    top: 16px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .success-notification-enter-active,
  .success-notification-leave-active {
    transition-duration: 0.01ms;
  }
}
</style>
