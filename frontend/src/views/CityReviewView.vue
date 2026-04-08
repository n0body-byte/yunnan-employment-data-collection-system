<template>
  <el-card shadow="never" class="surface-card">
    <template #header>
      <div>
        <h2 style="margin:0 0 8px">市级审核页面已并入市级工作台</h2>
        <p style="margin:0;color:var(--text-secondary)">待审月报、退回说明和通知发布功能已经整合到统一的市级工作台。</p>
      </div>
    </template>
    <el-result icon="success" title="请前往市级工作台" sub-title="当前版本统一在市级工作台中处理审核任务。">
      <template #extra>
        <el-button type="primary" @click="router.push({ name: 'city-workspace' })">进入市级工作台</el-button>
      </template>
    </el-result>
  </el-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>
