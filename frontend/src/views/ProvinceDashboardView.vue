<template>
  <el-space direction="vertical" fill size="20">
    <el-card shadow="never">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:16px">
        <div>
          <h2 style="margin:0 0 8px">省级数据总览</h2>
          <p style="margin:0;color:#606266">查看占比、趋势和调查期对比分析，并进入综合管理页</p>
        </div>
        <el-space>
          <el-button @click="router.push({ name: 'province-management' })">进入综合管理</el-button>
          <el-button type="primary" @click="handleExport">导出企业备案</el-button>
        </el-space>
      </div>
    </el-card>

    <el-row :gutter="20">
      <el-col :span="12"><el-card shadow="never"><template #header>各市企业数量占比</template><CityEnterpriseSharePie :items="cityStats" /></el-card></el-col>
      <el-col :span="12"><el-card shadow="never"><template #header>近 6 个月岗位变动趋势</template><JobChangeTrendLine :items="jobChangeTrend" /></el-card></el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>对比分析</template>
      <el-form :inline="true" :model="compareForm">
        <el-form-item label="起始月份"><el-date-picker v-model="compareForm.start_month" type="month" value-format="YYYY-MM" /></el-form-item>
        <el-form-item label="结束月份"><el-date-picker v-model="compareForm.end_month" type="month" value-format="YYYY-MM" /></el-form-item>
        <el-form-item label="分析维度"><el-select v-model="compareForm.dimension" style="width:160px"><el-option label="地区" value="REGION" /><el-option label="企业性质" value="ENTERPRISE_NATURE" /><el-option label="行业" value="INDUSTRY" /></el-select></el-form-item>
        <el-form-item><el-button type="primary" @click="loadCompare">查询分析</el-button></el-form-item>
      </el-form>
      <el-table :data="compareRows" stripe>
        <el-table-column prop="dimension_value" label="维度值" min-width="160" />
        <el-table-column prop="enterprise_count" label="企业数" min-width="100" />
        <el-table-column prop="baseline_jobs" label="基期岗位数" min-width="120" />
        <el-table-column prop="current_jobs" label="调查期岗位数" min-width="120" />
        <el-table-column prop="job_change_total" label="岗位变化总数" min-width="120" />
        <el-table-column prop="job_reduction_total" label="岗位减少总数" min-width="120" />
        <el-table-column prop="job_change_ratio" label="岗位变化占比" min-width="120" />
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header>按地市汇总</template>
      <el-table :data="cityStats" v-loading="loading" stripe>
        <el-table-column prop="city" label="地市" min-width="140" />
        <el-table-column prop="enterprise_count" label="企业数量" min-width="120" />
        <el-table-column prop="total_employment" label="总就业人数" min-width="140" />
        <el-table-column prop="total_job_changes" label="岗位变动总数" min-width="140" />
      </el-table>
    </el-card>
  </el-space>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import http from '../api/http'
import CityEnterpriseSharePie from '../components/CityEnterpriseSharePie.vue'
import JobChangeTrendLine from '../components/JobChangeTrendLine.vue'

const router = useRouter()
const loading = ref(false)
const cityStats = ref<any[]>([])
const jobChangeTrend = ref<any[]>([])
const compareRows = ref<any[]>([])
const compareForm = reactive({ start_month: '', end_month: '', dimension: 'REGION' })

const loadDashboardData = async () => {
  loading.value = true
  try {
    const [cityStatsResponse, trendResponse] = await Promise.all([
      http.get('/api/province/statistics/by-city'),
      http.get('/api/province/statistics/job-change-trend', { params: { months: 6 } }),
    ])
    cityStats.value = cityStatsResponse.data
    jobChangeTrend.value = trendResponse.data
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? '加载统计数据失败')
  } finally {
    loading.value = false
  }
}

const loadCompare = async () => {
  try {
    const { data } = await http.post('/api/province/statistics/compare', compareForm)
    compareRows.value = data
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? '对比分析失败')
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

onMounted(loadDashboardData)
</script>
