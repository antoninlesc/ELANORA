import { defineStore } from 'pinia';

export const useAppInfoStore = defineStore('appInfo', {
  state: () => ({
    instanceName: 'ELANORA',
    version: '1.0.0',
  }),
});
