<template>
  <DashboardShell
    v-model:active-key="activeNav"
    title="工作台"
    subtitle="查看全省企业分布、岗位变动趋势和最新上报动态。"
    :nav-items="navItems"
    :user-name="currentUserName"
    user-role="PROVINCE"
    current-role="PROVINCE"
    @logout="logout"
  >
    <template #header-actions>
      <el-button round @click="router.push({ name: 'province-management' })">进入综合管理</el-button>
      <el-button type="primary" round @click="handleExport">导出备案</el-button>
    </template>

    <template #stats>
      <DashboardMetricCard eyebrow="企业总数" :value="summary.enterpriseCount" accent="blue" description="已纳入统计企业数量" />
      <DashboardMetricCard eyebrow="本月上报" :value="summary.reportCount" accent="green" description="最近月份已提交月报数量" />
      <DashboardMetricCard eyebrow="就业总人数" :value="summary.totalEmployment" accent="orange" description="归档报表累计就业人数" />
      <DashboardMetricCard eyebrow="待省级审核" :value="summary.pendingCount" accent="red" description="等待终审的月报数量" />
    </template>

    <section class="workspace-grid">
      <article class="surface-card">
        <div class="surface-card__header">
          <div>
            <h3>全省岗位变动趋势</h3>
            <p>展示近 6 个月岗位变动总量。</p>
          </div>
        </div>
        <div class="surface-card__body surface-card__body--compact">
          <JobChangeTrendLine :items="jobChangeTrend" />
        </div>
      </article>

      <article class="surface-card">
        <div class="surface-card__header">
          <div>
            <h3>各市企业分布</h3>
            <p>按地市展示企业数量占比。</p>
          </div>
        </div>
        <div class="surface-card__body surface-card__body--compact">
          <CityEnterpriseSharePie :items="cityStats" />
        </div>
      </article>
    </section>

    <section class="workspace-grid">
      <article class="surface-card">
        <div class="surface-card__header">
          <div>
            <h3>最近上报记录</h3>
            <p>优先展示最近提交或审核中的月报。</p>
          </div>
          <el-button link type="primary" @click="router.push({ name: 'province-management' })">查看全部</el-button>
        </div>
        <div class="surface-card__body">
          <el-table :data="recentReports" stripe>
            <el-table-column prop="report_month" label="统计月份" min-width="120" />
            <el-table-column prop="enterprise_id" label="企业ID" min-width="100" />
            <el-table-column prop="current_employees" label="调查期人数" min-width="120" />
            <el-table-column prop="review_status" label="状态" min-width="160">
              <template #default="{ row }">{{ reviewStatusText(row.review_status) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </article>

      <article class="surface-card">
        <div class="surface-card__header">
          <div>
            <h3>各市汇总</h3>
            <p>按地市统计企业数、就业人数和岗位变动数。</p>
          </div>
        </div>
        <div class="surface-card__body">
          <el-table :data="cityStats" v-loading="loading" stripe>
            <el-table-column prop="city" label="地市" min-width="120" />
            <el-table-column prop="enterprise_count" label="企业数量" min-width="120" />
            <el-table-column prop="total_employment" label="总就业人数" min-width="130" />
            <el-table-column prop="total_job_changes" label="岗位变动总数" min-width="140" />
          </el-table>
        </div>
      </article>
    </section>
  </DashboardShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import http from '../api/http'
import DashboardMetricCard from '../components/DashboardMetricCard.vue'
import DashboardShell from '../components/DashboardShell.vue'
import CityEnterpriseSharePie from '../components/CityEnterpriseSharePie.vue'
import JobChangeTrendLine from '../components/JobChangeTrendLine.vue'

const router = useRouter()
const loading = ref(false)
const activeNav = ref('dashboard')
const cityStats = ref<any[]>([])
const jobChangeTrend = ref<any[]>([])
const recentReports = ref<any[]>([])
const pendingReports = ref<any[]>([])

const currentUserName = localStorage.getItem('username') ?? '管理员'

const navItems = [
  { key: 'dashboard', label: '工作台' },
  { key: 'management', label: '综合管理' },
]

const summary = computed(() => {
  const enterpriseCount = cityStats.value.reduce((total, item) => total + Number(item.enterprise_count ?? 0), 0)
  const totalEmployment = cityStats.value.reduce((total, item) => total + Number(item.total_employment ?? 0), 0)
  const reportCount = recentReports.value.length
  const pendingCount = pendingReports.value.length
  return {
    enterpriseCount: enterpriseCount.toLocaleString(),
    totalEmployment: totalEmployment.toLocaleString(),
    reportCount: reportCount.toLocaleString(),
    pendingCount: pendingCount.toLocaleString(),
  }
})

const reviewStatusText = (status: string) => ({
  PENDING_CITY_REVIEW: '待市级审核',
  PENDING_PROVINCE_REVIEW: '待省级审核',
  ARCHIVED: '已归档',
  REPORTED_TO_MINISTRY: '已上报部级',
  REJECTED: '已退回',
}[status] ?? status)

const loadDashboardData = async () => {
  loading.value = true
  try {
    const [cityStatsResponse, trendResponse, pendingResponse, reportsResponse] = await Promise.all([
      http.get('/api/province/statistics/by-city'),
      http.get('/api/province/statistics/job-change-trend', { params: { months: 6 } }),
      http.get('/api/employment-reports', { params: { review_status: 'PENDING_PROVINCE_REVIEW' } }),
      http.get('/api/employment-reports'),
    ])
    cityStats.value = cityStatsResponse.data
    jobChangeTrend.value = trendResponse.data
    pendingReports.value = pendingResponse.data
    recentReports.value = reportsResponse.data.slice(0, 5)
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? '加载统计数据失败')
  } finally {
    loading.value = false
  }
}

const handleExport = async () => {
  try {
    const response = await http.get('/api/province/enterprises/export', { responseType: 'blob' })
    const blobUrl = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = 'enterprise_filings.xlsx'
    link.click()
    window.URL.revokeObjectURL(blobUrl)
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? '导出失败')
  }
}

const logout = async () => {
  localStorage.clear()
  await router.push({ name: 'login' })
}

watch(activeNav, (value) => {
  if (value === 'management') {
    void router.push({ name: 'province-management' })
  }
})

onMounted(loadDashboardData)
</script>
