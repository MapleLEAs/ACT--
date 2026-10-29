import { createApp } from 'vue'
import './style.css'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import store from './store'
import AppIcon from './components/AppIcon.vue'

const app = createApp(App)

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册项目统一图标组件：<app-icon name="dashboard" />
app.component('AppIcon', AppIcon)

app.use(ElementPlus)
app.use(router)
app.use(store)
app.mount('#app')
