<template>
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.7"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path :d="paths[name] || paths.inbox" />
  </svg>
</template>
<script setup>
/* global defineProps */
defineProps({ name: { type: String, default: "inbox" } });
const paths = {
  inbox: "M8 4h8l4 8v7H4v-7l4-8ZM4 12h5l1 3h4l1-3h5M9 8h6",
  clock: "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM12 7v5l3 2",
  check: "m8 12 3 3 5-6M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
  returned: "M9 5 4 10l5 5M4 10h10a6 6 0 0 1 6 6v3",
  arrow: "M5 12h14m-5-5 5 5-5 5",
  back: "M19 12H5m5-5-5 5 5 5",
  download: "M12 3v12m-5-5 5 5 5-5M5 16v5h14v-5",
  refresh: "M20 7v5h-5M4 17v-5h5m11 0a8 8 0 0 0-14-5m-2 5a8 8 0 0 0 14 5",
  search: "M15 15 21 21M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z",
  shield: "m12 3 8 3v6c0 4-4 7-8 9-4-2-8-5-8-9V6l8-3Zm-4 9 3 3 5-6",
  construction: "M4 5h16v8H4V5Zm0 0 8 8m0-8 8 8M7 13v8m10-8v8M3 21h6m6 0h6",
};
</script>
<style scoped>
svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}
</style>
