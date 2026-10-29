<template>
  <div class="visualizer-container" ref="containerRef"></div>
  <div class="visualizer-overlay">
    <div class="visualizer-info">
      <h3>3D 实时状态同步</h3>
      <p>操作左侧立方体，右侧将实时同步位置</p>
      <div class="status-indicator">
        <span :class="['dot', wsStore.isConnected ? 'online' : 'offline']"></span>
        {{ wsStore.isConnected ? '已连接' : '未连接' }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import * as THREE from 'three';
import { useWebSocketStore } from '@/store/websocket';

const containerRef = ref<HTMLDivElement | null>(null);
const wsStore = useWebSocketStore();

let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let localCube: THREE.Mesh;
let remoteCube: THREE.Mesh;
let raycaster = new THREE.Raycaster();
let mouse = new THREE.Vector2();
let isDragging = false;
let unsubscribe: (() => void) | null = null;

const initThree = () => {
  if (!containerRef.value) return;

  // 1. 场景
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1a1a1a);

  // 2. 相机
  camera = new THREE.PerspectiveCamera(
    75,
    containerRef.value.clientWidth / containerRef.value.clientHeight,
    0.1,
    1000
  );
  camera.position.z = 5;

  // 3. 渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(containerRef.value.clientWidth, containerRef.value.clientHeight);
  containerRef.value.appendChild(renderer.domElement);

  // 4. 光照
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambientLight);
  const pointLight = new THREE.PointLight(0xffffff, 1);
  pointLight.position.set(5, 5, 5);
  scene.add(pointLight);

  // 5. 物体
  const geometry = new THREE.BoxGeometry(1, 1, 1);
  
  // 本地立方体 (绿色)
  const localMaterial = new THREE.MeshStandardMaterial({ color: 0x52c41a });
  localCube = new THREE.Mesh(geometry, localMaterial);
  localCube.position.x = -1.5;
  scene.add(localCube);

  // 远程同步立方体 (蓝色)
  const remoteMaterial = new THREE.MeshStandardMaterial({ color: 0x1890ff, transparent: true, opacity: 0.8 });
  remoteCube = new THREE.Mesh(geometry, remoteMaterial);
  remoteCube.position.x = 1.5;
  scene.add(remoteCube);

  // 6. 网格辅助线
  const gridHelper = new THREE.GridHelper(10, 10, 0x444444, 0x222222);
  gridHelper.rotation.x = Math.PI / 2;
  scene.add(gridHelper);
};

const onMouseMove = (event: MouseEvent) => {
  if (!containerRef.value) return;
  
  const rect = containerRef.value.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

  if (isDragging) {
    // 简单的拖拽逻辑
    localCube.position.x = mouse.x * 3;
    localCube.position.y = mouse.y * 2;
    
    // 发送同步消息
    wsStore.sendMessage({
      type: '3D_SYNC',
      data: {
        x: localCube.position.x,
        y: localCube.position.y,
        z: localCube.position.z,
        rotation: {
          x: localCube.rotation.x,
          y: localCube.rotation.y
        }
      }
    });
  }
};

const onMouseDown = () => {
  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObject(localCube);
  if (intersects.length > 0) {
    isDragging = true;
    (localCube.material as THREE.MeshStandardMaterial).emissive.setHex(0x333333);
  }
};

const onMouseUp = () => {
  isDragging = false;
  (localCube.material as THREE.MeshStandardMaterial).emissive.setHex(0x000000);
};

const animate = () => {
  requestAnimationFrame(animate);
  
  // 基础动画
  localCube.rotation.y += 0.01;
  remoteCube.rotation.y += 0.01;
  
  renderer.render(scene, camera);
};

const handleResize = () => {
  if (!containerRef.value) return;
  camera.aspect = containerRef.value.clientWidth / containerRef.value.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(containerRef.value.clientWidth, containerRef.value.clientHeight);
};

onMounted(() => {
  initThree();
  animate();

  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mousedown', onMouseDown);
  window.addEventListener('mouseup', onMouseUp);
  window.addEventListener('resize', handleResize);

  // 订阅 WebSocket 消息进行同步
  unsubscribe = wsStore.onMessage((message) => {
    if (message.type === '3D_SYNC') {
      const { x, y, z, rotation } = message.data;
      remoteCube.position.set(x, y, z);
      if (rotation) {
        remoteCube.rotation.x = rotation.x;
        remoteCube.rotation.y = rotation.y;
      }
    }
  });
});

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove);
  window.removeEventListener('mousedown', onMouseDown);
  window.removeEventListener('mouseup', onMouseUp);
  window.removeEventListener('resize', handleResize);
  
  if (unsubscribe) unsubscribe();
  if (renderer) renderer.dispose();
});
</script>

<style scoped>
.visualizer-container {
  width: 100%;
  height: 400px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  background: #1a1a1a;
  box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
}

.visualizer-overlay {
  position: absolute;
  top: 20px;
  left: 20px;
  pointer-events: none;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}

.visualizer-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #409EFF;
}

.visualizer-info p {
  margin: 0 0 12px 0;
  font-size: 12px;
  opacity: 0.8;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.online {
  background: #52c41a;
  box-shadow: 0 0 8px #52c41a;
}

.dot.offline {
  background: #f5222d;
}
</style>
