import { defineStore } from 'pinia'

export const useDataSyncStore = defineStore('data-sync', {
  state: () => ({
    devicesVersion: 0,
    environmentVersion: 0,
  }),
  actions: {
    notifyDevicesChanged() {
      this.devicesVersion += 1
    },
    notifyEnvironmentChanged() {
      this.environmentVersion += 1
    },
  },
})
