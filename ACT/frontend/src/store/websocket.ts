import { defineStore } from 'pinia';
import { useWebSocket } from '../api/websocket';

const { connect, send, subscribe } = useWebSocket();

export const useWebSocketStore = defineStore('websocket', {
  state: () => ({
    isConnected: false,
    wsInstance: null as WebSocket | null,
  }),
  actions: {
    init() {
      if (this.isConnected) return;
      connect();
      this.isConnected = true;
    },
    sendMessage(data: any) {
      send(data);
    },
    onMessage(callback: (data: any) => void) {
      return subscribe(callback);
    }
  }
});
