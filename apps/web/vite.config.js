import { defineConfig, loadEnv } from "vite";

export default defineConfig(function buildConfig(context) {
  var env = loadEnv(context.mode, process.cwd(), "");
  var proxyTarget =
    env.VITE_TRUST_LEDGER_DEV_API_PROXY_TARGET || "http://127.0.0.1:8000";

  return {
    server: {
      host: "127.0.0.1",
      port: 5173,
      proxy: {
        "/api": {
          target: proxyTarget,
          changeOrigin: true
        }
      }
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks: function manualChunks(id) {
            if (id.includes("node_modules")) {
              return "react-vendor";
            }

            return undefined;
          }
        }
      }
    }
  };
});
