<template>
  <el-card shadow="never" class="surface-card">
    <template #header>
      <div>
        <h2 style="margin:0 0 8px">企业备案页面已并入企业工作台</h2>
        <p style="margin:0;color:var(--text-secondary)">当前版本已统一使用企业工作台处理备案、填报、历史记录和通知浏览。</p>
      </div>
    </template>
    <el-result icon="info" title="请前往企业工作台" sub-title="企业备案已整合到统一后台界面中。">
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
