<template>
  <el-card shadow="never" class="surface-card">
    <template #header>
      <div>
        <h2 style="margin:0 0 8px">系统维护页面已并入省级综合管理</h2>
        <p style="margin:0;color:var(--text-secondary)">上报时限配置、系统监控和数据交换日志均已迁移到统一的省级管理工作台。</p>
      </div>
    </template>
    <el-result icon="warning" title="请前往省级综合管理" sub-title="系统维护功能已整合到统一后台。">
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
