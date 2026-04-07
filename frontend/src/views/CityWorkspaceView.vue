<template>
  <el-space direction="vertical" fill size="20">
    <el-card shadow="never">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <h2 style="margin:0 0 8px">市级工作台</h2>
          <p style="margin:0;color:#606266">月报审核、通知发布和密码修改</p>
        </div>
        <el-button @click="logout">退出登录</el-button>
      </div>
    </el-card>

    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="数据审核" name="review">
        <el-button type="primary" plain style="margin-bottom:12px" @click="loadReports">刷新待审数据</el-button>
        <el-table :data="reports" stripe>
          <el-table-column prop="report_month" label="统计月份" min-width="120" />
          <el-table-column prop="baseline_employees" label="建档期人数" min-width="120" />
          <el-table-column prop="current_employees" label="调查期人数" min-width="120" />
          <el-table-column prop="primary_reason" label="主要原因" min-width="180" />
          <el-table-column label="操作" min-width="240" fixed="right">
            <template #default="scope">
              <el-space>
                <el-button type="success" size="small" @click="audit(scope.row.id, 'APPROVE')">通过</el-button>
                <el-button type="danger" size="small" @click="openReject(scope.row.id)">退回</el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="通知发布" name="notifications">
        <el-form :model="notificationForm" label-width="90px">
          <el-form-item label="标题"><el-input v-model="notificationForm.title" maxlength="50" /></el-form-item>
          <el-form-item label="内容"><el-input v-model="notificationForm.content" type="textarea" :rows="4" maxlength="2000" /></el-form-item>
          <el-button type="primary" @click="saveNotification">发布通知</el-button>
        </el-form>
        <el-divider />
        <el-table :data="notifications" stripe>
          <el-table-column prop="title" label="标题" min-width="180" />
          <el-table-column prop="published_at" label="发布时间" min-width="180" />
          <el-table-column prop="content" label="内容" min-width="280" />
          <el-table-column label="操作" min-width="100"><template #default="scope"><el-button type="danger" link @click="deleteNotification(scope.row.id)">删除</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="修改密码" name="password">
        <el-form :model="passwordForm" label-width="100px">
          <el-form-item label="旧密码"><el-input v-model="passwordForm.old_password" type="password" show-password /></el-form-item>
          <el-form-item label="新密码"><el-input v-model="passwordForm.new_password" type="password" show-password /></el-form-item>
          <el-button type="primary" @click="changePassword">修改密码</el-button>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="rejectDialogVisible" title="退回说明" width="480px">
      <el-input v-model="rejectRemark" type="textarea" :rows="4" maxlength="500" />
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmReject">确认退回</el-button>
      </template>
    </el-dialog>
  </el-space>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import http from '../api/http'

const router = useRouter()
const activeTab = ref('review')
const reports = ref<any[]>([])
const notifications = ref<any[]>([])
const rejectDialogVisible = ref(false)
const rejectTargetId = ref<number | null>(null)
const rejectRemark = ref('')
const notificationForm = reactive({ title: '', content: '' })
const passwordForm = reactive({ old_password: '', new_password: '' })

const loadReports = async () => { const { data } = await http.get('/api/employment-reports', { params: { review_status: 'PENDING_CITY_REVIEW' } }); reports.value = data }
const loadNotifications = async () => { const { data } = await http.get('/api/notifications/manage'); notifications.value = data }
const audit = async (id: number, action: 'APPROVE' | 'REJECT', remark?: string) => { try { await http.post(`/api/employment-reports/${id}/audit`, { action, remark }); ElMessage.success(action === 'APPROVE' ? '审核通过' : '已退回'); await loadReports() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '审核失败') } }
const openReject = (id: number) => { rejectTargetId.value = id; rejectRemark.value = ''; rejectDialogVisible.value = true }
const confirmReject = async () => { if (!rejectTargetId.value || !rejectRemark.value) return; await audit(rejectTargetId.value, 'REJECT', rejectRemark.value); rejectDialogVisible.value = false }
const saveNotification = async () => { try { await http.post('/api/notifications', notificationForm); ElMessage.success('通知发布成功'); notificationForm.title = ''; notificationForm.content = ''; await loadNotifications() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '通知发布失败') } }
const deleteNotification = async (id: number) => { try { await http.delete(`/api/notifications/${id}`); ElMessage.success('通知已删除'); await loadNotifications() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '删除失败') } }
const changePassword = async () => { try { await http.post('/api/auth/change-password', passwordForm); ElMessage.success('密码修改成功'); passwordForm.old_password = ''; passwordForm.new_password = '' } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '密码修改失败') } }
const logout = async () => { localStorage.clear(); await router.push({ name: 'login' }) }

onMounted(async () => { await Promise.all([loadReports(), loadNotifications()]) })
</script>
