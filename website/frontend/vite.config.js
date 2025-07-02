/* eslint-env node */
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';
import express from 'express';

// Detect if running in Docker
const inDocker = process.env.DOCKER === 'true';

// Custom plugin to serve external static files
function serveStaticFiles() {
  return {
    name: 'serve-static-files',
    configureServer(server) {
      const staticPath = inDocker 
        ? path.resolve('/app/lsfb_static') 
        : path.resolve('../lsfb_static');
      
      server.middlewares.use('/lsfb_static', express.static(staticPath));
    }
  };
}

export default defineConfig(({ mode }) => {
  const envDir = '../env';
  
  const envFileMap = {
    dev: '.env.dev',
    'dev-docker': '.env.dev.docker',
    prod: '.env.prod',
    server: '.env.server'
  };
  
  let envFile;
  if (inDocker && mode === 'dev') {
    envFile = '.env.dev.docker';
  } else {
    envFile = envFileMap[mode] || '.env.dev';
  }
  
  return {
    plugins: [
      vue(), 
      tailwindcss(),
      ...(mode === 'dev' ? [serveStaticFiles()] : [])
    ],
    envDir: envDir,
    envFile: envFile,
    resolve: {
      alias: {
        '@': '/src',
        '@api': '/src/api',
        '@apiServices': '/src/api/services',
        '@assets': '/src/assets',
        '@components': '/src/components',
        '@views': '/src/views',
        '@css': '/src/assets/css',
        '@images': '/images',
        '@icons': '/images/icons', 
        '@search': '/images/search',
        '@videos': '/videos', 
        '@router': '/src/router',
        '@stores': '/src/stores',
        '@locales': '/src/locales',
        '@utils': '/src/utils',
        '@data': '/src/data',
      },
    },
    server: {
      watch: {
        usePolling: true,
      },
      host: '0.0.0.0',
      port: 8888,
      strictPort: true,
      hmr: inDocker ? false : {
        port: 8888,
        host: 'localhost',
        clientPort: inDocker ? 8888 : undefined
      },
      proxy: {
        '/api/v1': {
          target: inDocker ? 'http://backend:8008' : 'http://localhost:8008',
          changeOrigin: true,
          secure: false,
          configure: (proxy, options) => {
            console.log('Proxy configured with target:', options.target);
          }
        },
      }
    },
  };
});