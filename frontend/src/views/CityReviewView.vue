<template>
  <el-card shadow="never">
    <template #header>
      <div>
        <h2>市级报表审核</h2>
        <p>仅展示本市待审核月报，审核后进入省级终审或退回</p>
      </div>
    </template>

    <el-table :data="reports" v-loading="loading" stripe>
      <el-table-column prop="report_month" label="统计月份" min-width="120" />
      <el-table-column prop="baseline_employees" label="建档期人数" min-width="120" />
      <el-table-column prop="current_employees" label="调查期人数" min-width="120" />
      <el-table-column prop="reduction_type" label="减少类型" min-width="160" />
      <el-table-column prop="primary_reason" label="主要原因" min-width="180" />
      <el-table-column label="操作" min-width="180" fixed="right">
        <template #default="scope">
          <el-space>
            <el-button type="success" size="small" @click="audit(scope.row.id, 'APPROVE')">通过</el-button>
            <el-button type="danger" size="small" @click="audit(scope.row.id, 'REJECT')">退回</el-button>
          </el-space>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import http from '../api/http'

interface ReportItem {
  id: number
  report_month: string
  baseline_employees: number
  current_employees: number
  reduction_type: string | null
  primary_reason: string | null
}

const loading = ref(false)
const reports = ref<ReportItem[]>([])

const loadPendingReports = async () => {
  loading.value = true
  try {
    const { data } = await http.get<ReportItem[]>('/api/employment-reports', {
      params: { review_status: 'PENDING_CITY_REVIEW' },
    })
    reports.value = data
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? '待审核报表加载失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

const audit = async (reportId: number, action: 'APPROVE' | 'REJECT') => {
  try {
    await http.post(`/api/employment-reports/${reportId}/audit`, { action })
    ElMessage.success(action === 'APPROVE' ? '市级审核已通过' : '报表已退回')
    await loadPendingReports()
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? '市级审核失败'
    ElMessage.error(message)
  }
}

onMounted(() => {
  loadPendingReports()
})
</script>
