<template>
  <el-card shadow="never">
    <template #header>
      <div>
        <h2>省级备案审核</h2>
        <p>审核企业提交的备案信息，决定通过或退回</p>
      </div>
    </template>

    <el-table :data="enterprises" v-loading="loading" stripe>
      <el-table-column prop="region" label="地区" min-width="120" />
      <el-table-column prop="organization_code" label="组织机构代码" min-width="150" />
      <el-table-column prop="name" label="企业名称" min-width="180" />
      <el-table-column prop="industry" label="行业" min-width="160" />
      <el-table-column prop="contact_person" label="联系人" min-width="120" />
      <el-table-column prop="phone" label="电话" min-width="140" />
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

interface EnterpriseItem {
  id: number
  region: string
  organization_code: string
  name: string
  industry: string
  contact_person: string
  phone: string
}

const loading = ref(false)
const enterprises = ref<EnterpriseItem[]>([])

const loadPendingEnterprises = async () => {
  loading.value = true
  try {
    const { data } = await http.get<EnterpriseItem[]>('/api/enterprises', {
      params: { filing_status: 'PENDING' },
    })
    enterprises.value = data
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? '备案列表加载失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

const audit = async (enterpriseId: number, action: 'APPROVE' | 'REJECT') => {
  try {
    await http.post(`/api/enterprises/${enterpriseId}/filing-audit`, { action })
    ElMessage.success(action === 'APPROVE' ? '备案审核通过' : '备案已退回')
    await loadPendingEnterprises()
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? '备案审核失败'
    ElMessage.error(message)
  }
}

onMounted(() => {
  loadPendingEnterprises()
})
</script>
