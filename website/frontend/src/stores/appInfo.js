import { defineStore } from 'pinia';

export const useAppInfoStore = defineStore('appInfo', {
  state: () => ({
    instance: { instance_name: 'Default Instance' },
    version: '1.0.0',
  }),

  actions: {
    setInstance(instance) {
      this.instance = instance;
      localStorage.setItem('instance', JSON.stringify(instance));
    },
    setVersion(version) {
      this.version = version;
      localStorage.setItem('version', version);
    },
  },

  getters: {
    getInstance() {
      return this.instance;
    },
    getVersion() {
      return this.version;
    },
  },
});
