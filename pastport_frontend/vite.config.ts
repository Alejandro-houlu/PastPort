import { defineConfig } from 'vite';

export default defineConfig({
  publicDir: 'public',
  assetsInclude: [
    '**/*.bin',
    '**/*-shard*',
    '**/*.json',
    '**/models/**'
  ],
  server: {
    fs: {
      allow: ['..']
    },
    headers: {
      'Cross-Origin-Embedder-Policy': 'require-corp',
      'Cross-Origin-Opener-Policy': 'same-origin'
    }
  },
  optimizeDeps: {
    exclude: ['@tensorflow/tfjs', 'face-api.js']
  },
  build: {
    rollupOptions: {
      external: ['@tensorflow/tfjs']
    }
  }
});
