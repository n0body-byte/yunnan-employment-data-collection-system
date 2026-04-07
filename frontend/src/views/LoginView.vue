<template>
  <div class="login-page">
    <el-card shadow="hover" style="max-width: 440px; width: 100%">
      <template #header>
        <div>
          <h2 style="margin: 0 0 8px">云南省企业就业失业数据采集系统</h2>
          <p style="margin: 0; color: #606266">请选择角色并登录系统</p>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" clearable />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="省级用户" value="PROVINCE" />
            <el-option label="市级用户" value="CITY" />
            <el-option label="企业用户" value="ENTERPRISE" />
          </el-select>
        </el-form-item>

        <el-button type="primary" :loading="submitting" style="width: 100%" @click="handleLogin">
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import http from '../api/http'

type UserRole = 'PROVINCE' | 'CITY' | 'ENTERPRISE'

interface LoginForm {
  username: string
  password: string
  role: UserRole | ''
}

interface LoginResponse {
  access_token: string
  token_type?: string
  role: UserRole
  region?: string
}

const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = reactive<LoginForm>({
  username: '',
  password: '',
  role: '',
})

const rules: FormRules<LoginForm> = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

const roleRouteMap: Record<UserRole, { name: string }> = {
  ENTERPRISE: { name: 'enterprise-workspace' },
  CITY: { name: 'city-workspace' },
  PROVINCE: { name: 'province-dashboard' },
}

const handleLogin = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const { data } = await http.post<LoginResponse>('/api/auth/login', form)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user_role', data.role)
    localStorage.setItem('user_region', data.region ?? '')
    await router.push(roleRouteMap[data.role])
    ElMessage.success('登录成功')
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? '登录失败，请检查账号、密码和角色'
    ElMessage.error(message)
  } finally {
    submitting.value = false
  }
}
</script>
