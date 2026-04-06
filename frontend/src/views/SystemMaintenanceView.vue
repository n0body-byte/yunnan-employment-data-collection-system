<template>
  <el-space direction="vertical" fill size="20">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>上报时限设置</template>
          <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
            <el-form-item label="统计月份" prop="report_month">
              <el-date-picker
                v-model="form.report_month"
                type="month"
                value-format="YYYY-MM"
                placeholder="请选择月份"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="开始时间" prop="start_at">
              <el-date-picker
                v-model="form.start_at"
                type="datetime"
                value-format="YYYY-MM-DD HH:mm:ss"
                placeholder="请选择开始时间"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="结束时间" prop="end_at">
              <el-date-picker
                v-model="form.end_at"
                type="datetime"
                value-format="YYYY-MM-DD HH:mm:ss"
                placeholder="请选择结束时间"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="saveWindow">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <template #header>系统监控</template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="CPU 使用率">{{ monitor.cpu_percent }}%</el-descriptions-item>
            <el-descriptions-item label="内存使用率">{{ monitor.memory_percent }}%</el-descriptions-item>
            <el-descriptions-item label="已用内存">{{ formatBytes(monitor.memory_used_bytes) }}</el-descriptions-item>
            <el-descriptions-item label="总内存">{{ formatBytes(monitor.memory_total_bytes) }}</el-descriptions-item>
          </el-descriptions>
          <el-button style="margin-top: 16px" @click="loadMonitor">刷新监控</el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>已配置上报时限</template>
      <el-table :data="windows" v-loading="loading" stripe>
        <el-table-column prop="report_month" label="统计月份" min-width="120" />
        <el-table-column prop="start_at" label="开始时间" min-width="220" />
        <el-table-column prop="end_at" label="结束时间" min-width="220" />
      </el-table>
    </el-card>
  </el-space>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import http from '../api/http'

interface ReportingWindow {
  id: number
  report_month: string
  start_at: string
  end_at: string
}

interface MonitorData {
  cpu_percent: number
  memory_percent: number
  memory_used_bytes: number
  memory_total_bytes: number
}

const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)
const windows = ref<ReportingWindow[]>([])
const monitor = ref<MonitorData>({
  cpu_percent: 0,
  memory_percent: 0,
  memory_used_bytes: 0,
  memory_total_bytes: 0,
})

const form = reactive({
  report_month: '',
  start_at: '',
  end_at: '',
})

const rules: FormRules<typeof form> = {
  report_month: [{ required: true, message: '请选择统计月份', trigger: 'change' }],
  start_at: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_at: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
}

const loadWindows = async () => {
  loading.value = true
  try {
    const { data } = await http.get<ReportingWindow[]>('/api/system/reporting-windows')
    windows.value = data
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? '上报时限加载失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

const loadMonitor = async () => {
  try {
    const { data } = await http.get<MonitorData>('/api/system/monitor')
    monitor.value = data
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? '系统监控加载失败'
    ElMessage.error(message)
  }
}

const saveWindow = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    await http.post('/api/system/reporting-windows', form)
    ElMessage.success('上报时限已保存')
    await loadWindows()
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? '保存失败'
    ElMessage.error(message)
  } finally {
    saving.value = false
  }
}

const formatBytes = (value: number) => {
  if (!value) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = value
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`
}

onMounted(() => {
  loadWindows()
  loadMonitor()
})
</script>
