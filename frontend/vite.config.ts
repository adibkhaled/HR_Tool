import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/health": "http://localhost:8000",
      "/ready": "http://localhost:8000",
      "/metrics": "http://localhost:8000",
      "/resumes": "http://localhost:8000",
      "/jobs": "http://localhost:8000",
      "/match": "http://localhost:8000",
      "/chat": "http://localhost:8000",
      "/search": "http://localhost:8000",
      "/operations": "http://localhost:8000",
      "/feedback": "http://localhost:8000",
    },
  },
});
