<template>
  <div class="login-page">
    <div class="login-hero">
      <section class="login-copy">
        <div class="login-copy__headline">
          <span class="login-copy__badge">云南省企业就业失业数据采集系统</span>
          <h1>统一采集、分级审核、实时掌握全省就业动态。</h1>
          <p>
            系统覆盖企业备案、月度填报、市级审核、省级归档、统计分析和数据导出，
            面向企业、市级和省级用户提供分级工作台，并适配桌面端和移动端访问。
          </p>
        </div>

        <div class="login-feature-grid">
          <article class="login-feature">
            <strong>企业端</strong>
            <p>完成备案提交、月报填报、历史查询、通知浏览和密码修改。</p>
          </article>
          <article class="login-feature">
            <strong>市级端</strong>
            <p>处理待审月报、退回修改、通知发布和本市范围内数据管理。</p>
          </article>
          <article class="login-feature">
            <strong>省级端</strong>
            <p>负责备案审核、终审归档、统计分析、用户角色和系统维护。</p>
          </article>
          <article class="login-feature">
            <strong>响应式布局</strong>
            <p>工作台采用统一后台骨架，在宽屏和窄屏下都能保持清晰的信息层级。</p>
          </article>
        </div>
      </section>

      <section class="login-panel">
        <el-card shadow="never" style="border:none;background:transparent">
          <template #header>
            <div>
              <h2 style="margin:0 0 8px;font-size:1.6rem">登录系统</h2>
              <p style="margin:0;color:var(--text-secondary)">请选择角色并输入账号密码</p>
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
              <el-select v-model="form.role" placeholder="请选择角色" style="width:100%">
                <el-option label="省级用户" value="PROVINCE" />
                <el-option label="市级用户" value="CITY" />
                <el-option label="企业用户" value="ENTERPRISE" />
              </el-select>
            </el-form-item>

            <el-button
              type="primary"
              :loading="submitting"
              style="width:100%;height:46px;border-radius:14px"
              @click="handleLogin"
            >
              进入工作台
            </el-button>

            <div style="margin-top:18px;color:var(--text-muted);font-size:0.88rem;line-height:1.7">
              演示账号：
              <br>
              省级 province_admin
              <br>
              市级 kunming_city
              <br>
              企业 demo_enterprise
            </div>
          </el-form>
        </el-card>
      </section>
    </div>
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
    localStorage.setItem('username', form.username)
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
