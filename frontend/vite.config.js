import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "node:path";

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:5000",
    },
  },
  resolve: {
    alias: {
      "@": path.resolve("src"),
    },
  },
});
