import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/console/",
  plugins: [react()],
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
  },
});
