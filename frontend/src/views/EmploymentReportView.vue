<template>
  <el-card shadow="never" class="surface-card">
    <template #header>
      <div>
        <h2 style="margin:0 0 8px">月报填报页面已并入企业工作台</h2>
        <p style="margin:0;color:var(--text-secondary)">当前版本统一在企业工作台中完成月报填报、动态校验和历史查询。</p>
      </div>
    </template>
    <el-result icon="success" title="请前往企业工作台" sub-title="月度数据填报已经并入统一工作台。">
      <template #extra>
        <el-button type="primary" @click="router.push({ name: 'enterprise-workspace' })">进入企业工作台</el-button>
      </template>
    </el-result>
  </el-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>
