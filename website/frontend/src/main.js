import App from './App.vue';
import { createApp } from 'vue';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import { createPinia } from 'pinia';
import { setupI18n } from './i18n';

import '@css/tailwind.css';
import '@css/style.css';
import '@css/app.css';

import router from '@/router/router.js';

const pinia = createPinia();
const i18n = setupI18n();
const app = createApp(App);

// Register the FontAwesomeIcon component globally
app.component('FontAwesomeIcon', FontAwesomeIcon);

// Use the router instance in the app
app.use(router);

// Use the Pinia store in the app
app.use(pinia);

// Use the i18n instance in the app
app.use(i18n);

// Mount the app to the DOM
app.mount('#app');