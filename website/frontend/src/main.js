import { createApp } from 'vue';
import App from './App.vue';
import { createPinia } from 'pinia';
import { setupI18n } from '@plugins/i18n';
import FontAwesomeIcon from '@plugins/fontawesome';
import { createHead } from '@unhead/vue/client';

import '@css/tailwind.css';
import '@css/style.css';
import '@css/app.css';

import router from '@/router/router.js';

const app = createApp(App);
const pinia = createPinia();
const i18n = setupI18n();
const head = createHead();

app.use(pinia);
app.use(i18n);
app.use(router);
app.use(head);

// eslint-disable-next-line vue/component-definition-name-casing
app.component('font-awesome-icon', FontAwesomeIcon);

app.mount('#app');
