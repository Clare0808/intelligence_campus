<template>
  <router-view />
</template>

<style lang="scss">
::view-transition-old(root),
::view-transition-new(root) {
  animation: none;
  mix-blend-mode: normal;
}
:root {
  font-family: "DM Sans", "Segoe UI", "Microsoft JhengHei", sans-serif;
  color: #23332d;
  background: #f5f6f1;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-optical-sizing: auto;
  font-weight: 400;
}

* {
  box-sizing: border-box;
}

body {
  min-width: 320px;
  margin: 0;
}

button,
input,
select {
  font: inherit;
}

button,
select {
  cursor: pointer;
}

button:focus-visible,
input:focus-visible,
select:focus-visible,
[tabindex]:focus-visible {
  outline: 3px solid #e29b54;
  outline-offset: 3px;
}

::selection {
  color: #fff;
  background: #2d6650;
}
</style>
