<template>
  <i class="app-icon" :class="{ 'is-spin': spin }" v-html="svgContent" />
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    /** 图标文件名（不含 .svg），对应 src/assets/icons 下的文件 */
    name: string
    /** 是否旋转（用于 loading/refresh） */
    spin?: boolean
  }>(),
  { spin: false }
)

// 一次性把 icons 目录下所有 svg 以原始字符串形式载入（构建期内联，无运行时请求）
const modules = import.meta.glob('../assets/icons/*.svg', {
  query: '?raw',
  import: 'default',
  eager: true
}) as Record<string, string>

const svgContent = computed(() => {
  const key = Object.keys(modules).find((k) => k.endsWith(`/${props.name}.svg`))
  return key ? modules[key] : ''
})
</script>

<style scoped>
.app-icon {
  display: inline-flex;
  width: 1em;
  height: 1em;
  line-height: 0;
  vertical-align: -0.15em;
}
.app-icon :deep(svg) {
  width: 100%;
  height: 100%;
  display: block;
}
.app-icon.is-spin :deep(svg) {
  animation: app-icon-spin 1s linear infinite;
}
@keyframes app-icon-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
