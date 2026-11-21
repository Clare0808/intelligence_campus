import { ref } from "vue";

export const notification = ref(null);
let notificationId = 0;

export function showNotification(message, type = "success") {
  notification.value = { id: ++notificationId, message, type };
}
