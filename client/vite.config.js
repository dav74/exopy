import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
  ],
  // En production Docker, la base est '/'. Pour pixees.fr, passer VITE_BASE_URL=/informatiquelycee/exopy/
  base: process.env.VITE_BASE_URL || '/',
})
