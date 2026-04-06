<template>
  <div class="province-dashboard">
    <el-space direction="vertical" fill size="20">
      <el-card shadow="never">
        <div class="toolbar">
          <div>
            <h2>省级数据管理</h2>
            <p>查看全省统计、备案审核与系统维护入口</p>
          </div>
          <el-space>
            <el-button @click="router.push({ name: 'province-filing-audit' })">备案审核</el-button>
            <el-button @click="router.push({ name: 'system-maintenance' })">系统维护</el-button>
            <el-button type="primary" @click="handleExport">导出备案列表</el-button>
          </el-space>
        </div>
      </el-card>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-card shadow="never">
            <template #header>各市企业数量占比</template>
            <CityEnterpriseSharePie :items="cityStats" />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never">
            <template #header>近 6 个月岗位变动趋势</template>
            <JobChangeTrendLine :items="jobChangeTrend" />
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never">
        <template #header>按地市统计</template>
        <el-table :data="cityStats" v-loading="loading" stripe>
          <el-table-column prop="city" label="地市" min-width="140" />
          <el-table-column prop="enterprise_count" label="企业数量" min-width="120" />
          <el-table-column prop="total_employment" label="总就业人数" min-width="140" />
          <el-table-column prop="total_job_changes" label="岗位变动总数" min-width="140" />
        </el-table>
      </el-card>
    </el-space>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import http from '../api/http'
import CityEnterpriseSharePie from '../components/CityEnterpriseSharePie.vue'
import JobChangeTrendLine from '../components/JobChangeTrendLine.vue'

interface CityStatItem {
  city: string
  enterprise_count: number
  total_employment: number
  total_job_changes: number
}

interface TrendItem {
  report_month: string
  total_job_changes: number
}

const router = useRouter()
const loading = ref(false)
const cityStats = ref<CityStatItem[]>([])
const jobChangeTrend = ref<TrendItem[]>([])

const loadDashboardData = async () => {
  loading.value = true
  try {
    const [cityStatsResponse, trendResponse] = await Promise.all([
      http.get<CityStatItem[]>('/api/province/statistics/by-city'),
      http.get<TrendItem[]>('/api/province/statistics/job-change-trend', { params: { months: 6 } }),
    ])
    cityStats.value = cityStatsResponse.data
    jobChangeTrend.value = trendResponse.data
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? '省级统计数据加载失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

const handleExport = async () => {
  try {
    const response = await http.get<Blob>('/api/province/enterprises/export', { responseType: 'blob' })
    const blobUrl = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = 'enterprise_filings.xlsx'
    link.click()
    window.URL.revokeObjectURL(blobUrl)
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? '导出失败'
    ElMessage.error(message)
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>
