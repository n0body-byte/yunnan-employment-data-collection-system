<template>
  <el-card shadow="never" class="surface-card">
    <template #header>
      <div>
        <h2 style="margin:0 0 8px">省级备案审核页面已并入省级综合管理</h2>
        <p style="margin:0;color:var(--text-secondary)">备案审核、报表管理、用户角色和系统维护已统一整合到省级综合管理工作台。</p>
      </div>
    </template>
    <el-result icon="info" title="请前往省级综合管理" sub-title="当前版本已采用统一的省级后台界面。">
      <template #extra>
        <el-button type="primary" @click="router.push({ name: 'province-management' })">进入省级综合管理</el-button>
      </template>
    </el-result>
  </el-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>
