import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5175,
    strictPort: true,
    host: true,
    fs: {
      // 允许读取项目根目录（knowledges/docs 下的说明文档）
      allow: [fileURLToPath(new URL('..', import.meta.url))],
    },
  },
})
