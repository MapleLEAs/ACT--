<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useWebSocketStore } from './store/websocket';

const wsStore = useWebSocketStore();

onMounted(() => {
  wsStore.init();
});
</script>

<style>
#app {
  width: 100vw;
  height: 100vh;
  margin: 0;
  padding: 0;
}
</style>
