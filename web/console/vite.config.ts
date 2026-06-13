import { resolve } from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/console/",
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@api": resolve(__dirname, "src/api"),
      "@features": resolve(__dirname, "src/features"),
      "@shared": resolve(__dirname, "src/shared"),
    },
  },
  build: {
    outDir: "../../src/mery_tts/console",
    emptyOutDir: false,
    rollupOptions: {
      input: "index.html",
    },
  },
  server: {
    host: "127.0.0.1",
    proxy: {
      "/v1": {
        target: "http://127.0.0.1:8765",
        changeOrigin: false,
      },
    },
  },
});
