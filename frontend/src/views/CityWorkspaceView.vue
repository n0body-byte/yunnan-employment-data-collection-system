<template>
  <DashboardShell
    v-model:active-key="activeNav"
    title="工作台"
    subtitle="处理本市月报审核、通知发布和账户安全。"
    :nav-items="navItems"
    :user-name="currentUserName"
    user-role="CITY"
    current-role="CITY"
    @logout="logout"
  >
    <template #stats>
      <DashboardMetricCard eyebrow="待审月报" :value="reports.length" accent="blue" description="等待市级审核的报表数量" />
      <DashboardMetricCard eyebrow="已发布通知" :value="notifications.length" accent="green" description="当前市级账号发布的通知" />
      <DashboardMetricCard eyebrow="当前地区" :value="currentRegion" accent="orange" description="当前账号的数据管辖范围" />
      <DashboardMetricCard eyebrow="退回处理" :value="rejectHandledCount" accent="red" description="本轮已录入退回说明次数" />
    </template>

    <section v-if="activeNav === 'overview'" class="workspace-grid">
      <article class="surface-card">
        <div class="surface-card__header">
          <div>
            <h3>待审数据概览</h3>
            <p>优先处理待市级审核的企业月报。</p>
          </div>
          <el-button type="primary" round @click="activeNav = 'review'">进入审核</el-button>
        </div>
        <div class="surface-card__body">
          <el-table :data="reports.slice(0, 5)" stripe>
            <el-table-column prop="report_month" label="统计月份" min-width="120" />
            <el-table-column prop="baseline_employees" label="建档期人数" min-width="120" />
            <el-table-column prop="current_employees" label="调查期人数" min-width="120" />
            <el-table-column prop="primary_reason" label="主要原因" min-width="180" />
          </el-table>
        </div>
      </article>

      <article class="surface-card">
        <div class="surface-card__header">
          <div>
            <h3>快捷操作</h3>
            <p>按实际业务流程快速进入对应功能。</p>
          </div>
        </div>
        <div class="surface-card__body" style="display:grid;gap:12px">
          <el-button type="primary" round @click="activeNav = 'review'">审核待审月报</el-button>
          <el-button round @click="activeNav = 'notifications'">发布通知公告</el-button>
          <el-button round @click="activeNav = 'password'">修改账户密码</el-button>
        </div>
      </article>
    </section>

    <article v-else-if="activeNav === 'review'" class="surface-card">
      <div class="surface-card__header">
        <div>
          <h3>数据审核</h3>
          <p>审核通过后流转至省级终审，退回时需填写说明。</p>
        </div>
        <el-button round @click="loadReports">刷新待审数据</el-button>
      </div>
      <div class="surface-card__body">
        <el-table :data="reports" stripe>
          <el-table-column prop="report_month" label="统计月份" min-width="120" />
          <el-table-column prop="baseline_employees" label="建档期人数" min-width="120" />
          <el-table-column prop="current_employees" label="调查期人数" min-width="120" />
          <el-table-column prop="primary_reason" label="主要原因" min-width="180" />
          <el-table-column label="操作" min-width="240" fixed="right">
            <template #default="{ row }">
              <el-space>
                <el-button type="success" size="small" @click="audit(row.id, 'APPROVE')">通过</el-button>
                <el-button type="danger" size="small" @click="openReject(row.id)">退回</el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </article>

    <article v-else-if="activeNav === 'notifications'" class="surface-card">
      <div class="surface-card__header">
        <div>
          <h3>通知公告</h3>
          <p>发布和维护本市可见的系统通知。</p>
        </div>
      </div>
      <div class="surface-card__body">
        <el-form :model="notificationForm" label-width="90px" style="margin-bottom:22px">
          <el-form-item label="标题"><el-input v-model="notificationForm.title" maxlength="50" /></el-form-item>
          <el-form-item label="内容"><el-input v-model="notificationForm.content" type="textarea" :rows="4" maxlength="2000" /></el-form-item>
          <el-button type="primary" @click="saveNotification">发布通知</el-button>
        </el-form>

        <el-table :data="notifications" stripe>
          <el-table-column prop="title" label="标题" min-width="180" />
          <el-table-column prop="published_at" label="发布时间" min-width="180" />
          <el-table-column prop="content" label="内容" min-width="280" />
          <el-table-column label="操作" min-width="100">
            <template #default="{ row }">
              <el-button type="danger" link @click="deleteNotification(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </article>

    <article v-else class="surface-card">
      <div class="surface-card__header">
        <div>
          <h3>账户安全</h3>
          <p>修改当前市级账号密码。</p>
        </div>
      </div>
      <div class="surface-card__body" style="max-width:560px">
        <el-form :model="passwordForm" label-width="100px">
          <el-form-item label="旧密码"><el-input v-model="passwordForm.old_password" type="password" show-password /></el-form-item>
          <el-form-item label="新密码"><el-input v-model="passwordForm.new_password" type="password" show-password /></el-form-item>
          <el-button type="primary" @click="changePassword">修改密码</el-button>
        </el-form>
      </div>
    </article>

    <el-dialog v-model="rejectDialogVisible" title="退回说明" width="480px">
      <el-input v-model="rejectRemark" type="textarea" :rows="4" maxlength="500" />
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmReject">确认退回</el-button>
      </template>
    </el-dialog>
  </DashboardShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import http from '../api/http'
import DashboardMetricCard from '../components/DashboardMetricCard.vue'
import DashboardShell from '../components/DashboardShell.vue'

const router = useRouter()
const activeNav = ref('overview')
const reports = ref<any[]>([])
const notifications = ref<any[]>([])
const rejectDialogVisible = ref(false)
const rejectTargetId = ref<number | null>(null)
const rejectRemark = ref('')
const rejectHandledCount = ref(0)
const notificationForm = reactive({ title: '', content: '' })
const passwordForm = reactive({ old_password: '', new_password: '' })

const currentUserName = localStorage.getItem('username') ?? '市级用户'
const currentRegion = localStorage.getItem('user_region') ?? 'Kunming'

const navItems = computed(() => [
  { key: 'overview', label: '工作台' },
  { key: 'review', label: '数据审核', badge: reports.value.length || undefined },
  { key: 'notifications', label: '通知公告', badge: notifications.value.length || undefined },
  { key: 'password', label: '账户安全' },
])

const loadReports = async () => {
  const { data } = await http.get('/api/employment-reports', { params: { review_status: 'PENDING_CITY_REVIEW' } })
  reports.value = data
}

const loadNotifications = async () => {
  const { data } = await http.get('/api/notifications/manage')
  notifications.value = data
}

const audit = async (id: number, action: 'APPROVE' | 'REJECT', remark?: string) => {
  try {
    await http.post(`/api/employment-reports/${id}/audit`, { action, remark })
    ElMessage.success(action === 'APPROVE' ? '审核通过' : '已退回')
    await loadReports()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? '审核失败')
  }
}

const openReject = (id: number) => {
  rejectTargetId.value = id
  rejectRemark.value = ''
  rejectDialogVisible.value = true
}

const confirmReject = async () => {
  if (!rejectTargetId.value || !rejectRemark.value) return
  await audit(rejectTargetId.value, 'REJECT', rejectRemark.value)
  rejectDialogVisible.value = false
  rejectHandledCount.value += 1
}

const saveNotification = async () => {
  try {
    await http.post('/api/notifications', notificationForm)
    ElMessage.success('通知发布成功')
    notificationForm.title = ''
    notificationForm.content = ''
    await loadNotifications()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? '通知发布失败')
  }
}

const deleteNotification = async (id: number) => {
  try {
    await http.delete(`/api/notifications/${id}`)
    ElMessage.success('通知已删除')
    await loadNotifications()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? '删除失败')
  }
}

const changePassword = async () => {
  try {
    await http.post('/api/auth/change-password', passwordForm)
    ElMessage.success('密码修改成功')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? '密码修改失败')
  }
}

const logout = async () => {
  localStorage.clear()
  await router.push({ name: 'login' })
}

onMounted(async () => {
  await Promise.all([loadReports(), loadNotifications()])
})
</script>
