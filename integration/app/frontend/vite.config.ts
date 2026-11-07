import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import {loadEnv} from 'vite'
export default defineConfig(({mode})=>{
const env=loadEnv(mode,'.','APP_')
return {
 cacheDir:'.vite',
 plugins:[react(),tailwindcss()],
 server:{host:'127.0.0.1',port:Number(env.APP_WEB_PORT||5173),strictPort:true,proxy:{'/api':`http://127.0.0.1:${env.APP_API_PORT||8000}`}},
 test:{include:['src/**/*.{test,spec}.{ts,tsx}'],environment:'jsdom',setupFiles:['./src/test/setup.ts'],globals:true},
}})
