import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
    // Load env file from parent directory
    const env = loadEnv(mode, path.resolve(__dirname, '..'), '')

    return {
        plugins: [react()],
        envDir: path.resolve(__dirname, '..'), // Look for .env files in parent directory
        define: {
            // Expose specific env variables to the client
            'process.env.REACT_APP_ELEVENLABS_AGENT_ID': JSON.stringify(env.REACT_APP_ELEVENLABS_AGENT_ID),
            'process.env.REACT_APP_ELEVENLABS_API_KEY': JSON.stringify(env.REACT_APP_ELEVENLABS_API_KEY),
        },
        server: {
            port: 3000,
            open: true
        },
        build: {
            outDir: 'dist',
            sourcemap: true
        }
    }
})
