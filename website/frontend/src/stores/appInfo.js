import { defineStore } from 'pinia';

export const useAppInfoStore = defineStore('appInfo', {
  state: () => ({
    instance: null,
    version: '1.0.0',
  }),
});
