<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h2>空管设备数据集中分析系统的设计与实现（ATC Monitor）</h2>
        <p>系统测试管理后台</p>
      </div>
      
      <el-form 
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username"
            placeholder="请输入管理员账号"
            size="large"
          >
            <template #prefix>
              <AppIcon name="user" />
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="loginForm.password"
            type="password"
            placeholder="请输入管理员密码"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <AppIcon name="lock" />
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            class="login-btn" 
            size="large"
            :loading="loading"
            @click="handleLogin"
          >
            登录系统
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import request from '../api/request'

const router = useRouter()
const loginFormRef = ref<FormInstance>()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = reactive<FormRules>({
  username: [{ required: true, message: '账号不能为空', trigger: 'blur' }],
  password: [{ required: true, message: '密码不能为空', trigger: 'blur' }]
})

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const data: any = await request({
          url: '/api/token/',
          method: 'post',
          data: {
            username: loginForm.username,
            password: loginForm.password
          },
          withCredentials: true
        })
        
        if (data.access) {
          sessionStorage.setItem('access_token', data.access)
        }
        
        ElMessage.success('登录成功，欢迎回来！')
        await new Promise(resolve => setTimeout(resolve, 300))
        router.push('/')
      } catch (error: any) {
        console.error('登录失败:', error)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #2d3a4b;
  background-image: linear-gradient(135deg, #2d3a4b 0%, #1a2332 100%);
}

.login-box {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  margin: 0;
  font-size: 26px;
  color: #303133;
}

.login-header p {
  margin: 10px 0 0;
  font-size: 14px;
  color: #909399;
}

.login-btn {
  width: 100%;
  margin-top: 10px;
}
</style>
