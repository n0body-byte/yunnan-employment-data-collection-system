<template>
  <el-space direction="vertical" fill size="20">
    <el-card shadow="never">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <h2 style="margin:0 0 8px">省级综合管理</h2>
          <p style="margin:0;color:#606266">覆盖说明书中的备案审核、报表管理、用户和角色管理、通知管理、系统维护</p>
        </div>
        <el-space>
          <el-button @click="router.push({ name: 'province-dashboard' })">返回总览</el-button>
          <el-button @click="logout">退出登录</el-button>
        </el-space>
      </div>
    </el-card>

    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="备案审核" name="filing">
        <el-button type="primary" plain style="margin-bottom:12px" @click="loadEnterprises">刷新待审备案</el-button>
        <el-table :data="enterprises" stripe>
          <el-table-column prop="region" label="地区" min-width="120" />
          <el-table-column prop="organization_code" label="组织机构代码" min-width="150" />
          <el-table-column prop="name" label="企业名称" min-width="180" />
          <el-table-column label="操作" min-width="260"><template #default="scope"><el-space><el-button type="success" size="small" @click="auditFiling(scope.row.id, 'APPROVE')">通过</el-button><el-button type="danger" size="small" @click="openFilingReject(scope.row.id)">退回</el-button></el-space></template></el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="报表管理" name="reports">
        <el-button type="primary" plain style="margin-bottom:12px" @click="loadReports">刷新报表</el-button>
        <el-table :data="reports" stripe>
          <el-table-column prop="report_month" label="月份" min-width="110" />
          <el-table-column prop="enterprise_id" label="企业ID" min-width="100" />
          <el-table-column prop="baseline_employees" label="建档期人数" min-width="120" />
          <el-table-column prop="current_employees" label="调查期人数" min-width="120" />
          <el-table-column prop="review_status" label="状态" min-width="180" />
          <el-table-column label="操作" min-width="360"><template #default="scope"><el-space wrap><el-button size="small" type="success" @click="finalAudit(scope.row.id)">终审归档</el-button><el-button size="small" @click="reportToMinistry(scope.row.id)">上报部级</el-button><el-button size="small" type="warning" @click="openRevision(scope.row)">数据修改</el-button><el-button size="small" type="danger" @click="deleteReport(scope.row.id)">删除</el-button></el-space></template></el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="用户管理" name="users">
        <el-form :inline="true" :model="userForm">
          <el-form-item label="用户名"><el-input v-model="userForm.username" /></el-form-item>
          <el-form-item label="角色"><el-select v-model="userForm.role" style="width:120px"><el-option label="省级" value="PROVINCE" /><el-option label="市级" value="CITY" /><el-option label="企业" value="ENTERPRISE" /></el-select></el-form-item>
          <el-form-item label="地区"><el-input v-model="userForm.region" /></el-form-item>
          <el-form-item label="密码"><el-input v-model="userForm.password" /></el-form-item>
          <el-form-item><el-button type="primary" @click="createUser">新增用户</el-button></el-form-item>
        </el-form>
        <el-table :data="users" stripe>
          <el-table-column prop="username" label="用户名" min-width="150" />
          <el-table-column prop="role" label="角色" min-width="120" />
          <el-table-column prop="region" label="地区" min-width="140" />
          <el-table-column prop="is_active" label="启用" min-width="80" />
          <el-table-column label="操作" min-width="120"><template #default="scope"><el-button type="danger" link @click="deleteUser(scope.row.id)">删除</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="角色管理" name="roles">
        <el-form :inline="true" :model="roleForm">
          <el-form-item label="角色名"><el-input v-model="roleForm.name" /></el-form-item>
          <el-form-item label="适用范围"><el-select v-model="roleForm.scope_role" style="width:130px"><el-option label="省级" value="PROVINCE" /><el-option label="市级" value="CITY" /><el-option label="企业" value="ENTERPRISE" /></el-select></el-form-item>
          <el-form-item label="权限"><el-select v-model="roleForm.permission_codes" multiple collapse-tags style="width:360px"><el-option v-for="item in permissions" :key="item.code" :label="item.code" :value="item.code" /></el-select></el-form-item>
          <el-form-item><el-button type="primary" @click="createRole">新增角色</el-button></el-form-item>
        </el-form>
        <el-table :data="roles" stripe>
          <el-table-column prop="name" label="角色名" min-width="160" />
          <el-table-column prop="scope_role" label="适用范围" min-width="120" />
          <el-table-column label="权限数" min-width="100"><template #default="scope">{{ scope.row.permissions?.length ?? 0 }}</template></el-table-column>
          <el-table-column label="操作" min-width="120"><template #default="scope"><el-button type="danger" link @click="deleteRole(scope.row.id)">删除</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="通知管理" name="notifications">
        <el-form :model="notificationForm" label-width="70px">
          <el-form-item label="标题"><el-input v-model="notificationForm.title" maxlength="50" /></el-form-item>
          <el-form-item label="内容"><el-input v-model="notificationForm.content" type="textarea" :rows="4" maxlength="2000" /></el-form-item>
          <el-button type="primary" @click="saveNotification">发布通知</el-button>
        </el-form>
        <el-divider />
        <el-table :data="notifications" stripe>
          <el-table-column prop="title" label="标题" min-width="180" />
          <el-table-column prop="published_at" label="发布时间" min-width="180" />
          <el-table-column prop="content" label="内容" min-width="320" />
          <el-table-column label="操作" min-width="120"><template #default="scope"><el-button type="danger" link @click="deleteNotification(scope.row.id)">删除</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="系统维护" name="system">
        <el-form :inline="true" :model="windowForm">
          <el-form-item label="月份"><el-date-picker v-model="windowForm.report_month" type="month" value-format="YYYY-MM" /></el-form-item>
          <el-form-item label="开始"><el-date-picker v-model="windowForm.start_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" /></el-form-item>
          <el-form-item label="结束"><el-date-picker v-model="windowForm.end_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" /></el-form-item>
          <el-form-item><el-button type="primary" @click="saveWindow">保存时限</el-button></el-form-item>
        </el-form>
        <el-descriptions :column="2" border style="margin-bottom:16px"><el-descriptions-item label="CPU">{{ monitor.cpu_percent }}%</el-descriptions-item><el-descriptions-item label="内存">{{ monitor.memory_percent }}%</el-descriptions-item><el-descriptions-item label="磁盘">{{ monitor.disk_percent }}%</el-descriptions-item><el-descriptions-item label="系统时间">{{ monitor.current_time }}</el-descriptions-item></el-descriptions>
        <el-button @click="loadMonitor">刷新监控</el-button>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="filingRejectVisible" title="备案退回说明"><el-input v-model="filingRejectRemark" type="textarea" :rows="4" /><template #footer><el-button @click="filingRejectVisible=false">取消</el-button><el-button type="primary" @click="confirmFilingReject">确认退回</el-button></template></el-dialog>
    <el-dialog v-model="revisionVisible" title="报表修订"><el-input v-model="revisionForm.note" placeholder="修改说明" style="margin-bottom:12px" /><el-input-number v-model="revisionForm.baseline_employees" :min="0" style="width:100%;margin-bottom:12px" /><el-input-number v-model="revisionForm.current_employees" :min="0" style="width:100%;margin-bottom:12px" /><el-select v-model="revisionForm.reduction_type" placeholder="减少类型" style="width:100%;margin-bottom:12px"><el-option v-for="item in reductionTypes" :key="item" :label="item" :value="item" /></el-select><el-select v-model="revisionForm.primary_reason" placeholder="主要原因" style="width:100%"><el-option v-for="item in reasonOptions" :key="item" :label="item" :value="item" /></el-select><template #footer><el-button @click="revisionVisible=false">取消</el-button><el-button type="primary" @click="saveRevision">保存修订</el-button></template></el-dialog>
  </el-space>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../api/http'

const router = useRouter()
const activeTab = ref('filing')
const enterprises = ref<any[]>([])
const reports = ref<any[]>([])
const users = ref<any[]>([])
const roles = ref<any[]>([])
const permissions = ref<any[]>([])
const notifications = ref<any[]>([])
const monitor = ref<any>({ cpu_percent: 0, memory_percent: 0, disk_percent: 0, current_time: '' })
const filingRejectVisible = ref(false)
const filingRejectId = ref<number | null>(null)
const filingRejectRemark = ref('')
const revisionVisible = ref(false)
const revisionReportId = ref<number | null>(null)
const reasonOptions = ['产业结构调整','重大技术改革','节能减排、淘汰落后产能','订单不足','原材料涨价','工资、社保等用工成本上升','经营资金困难','税收政策变化（包括税负增加或出口退税减少等）','季节性用工','其他','自行离职','工作调动、企业内部调剂','劳动关系转移、劳务派遣','退休','退职','死亡','自然减员','国际因素变化','招不上人来']
const reductionTypes = ['关闭破产','停业整顿','经济性裁员','业务转移','自然减员','正常解除或终止劳动合同','国际因素变化影响','自然灾害','重大事件影响','其他']
const userForm = reactive({ username: '', password: '', role: 'CITY', region: 'Kunming' })
const roleForm = reactive({ name: '', scope_role: 'CITY', permission_codes: [] as string[] })
const notificationForm = reactive({ title: '', content: '' })
const windowForm = reactive({ report_month: '', start_at: '', end_at: '' })
const revisionForm = reactive({ note: '', baseline_employees: 0, current_employees: 0, reduction_type: '', primary_reason: '', primary_reason_detail: '' })

const loadEnterprises = async () => { const { data } = await http.get('/api/enterprises', { params: { filing_status: 'PENDING' } }); enterprises.value = data }
const loadReports = async () => { const { data } = await http.get('/api/employment-reports'); reports.value = data }
const loadUsers = async () => { const { data } = await http.get('/api/users'); users.value = data }
const loadRoles = async () => { const [roleRes, permissionRes] = await Promise.all([http.get('/api/roles'), http.get('/api/permissions')]); roles.value = roleRes.data; permissions.value = permissionRes.data }
const loadNotifications = async () => { const { data } = await http.get('/api/notifications/manage'); notifications.value = data }
const loadMonitor = async () => { const { data } = await http.get('/api/system/monitor'); monitor.value = data }
const auditFiling = async (id: number, action: 'APPROVE' | 'REJECT', remark?: string) => { await http.post(`/api/enterprises/${id}/filing-audit`, { action, remark }); ElMessage.success(action === 'APPROVE' ? '备案审核通过' : '备案已退回'); await loadEnterprises() }
const openFilingReject = (id: number) => { filingRejectId.value = id; filingRejectRemark.value = ''; filingRejectVisible.value = true }
const confirmFilingReject = async () => { if (!filingRejectId.value || !filingRejectRemark.value) return; await auditFiling(filingRejectId.value, 'REJECT', filingRejectRemark.value); filingRejectVisible.value = false }
const finalAudit = async (id: number) => { try { await http.post(`/api/employment-reports/${id}/final-audit`); ElMessage.success('终审归档成功'); await loadReports() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '终审失败') } }
const reportToMinistry = async (id: number) => { try { await http.post(`/api/employment-reports/${id}/report-to-ministry`); ElMessage.success('已上报部级'); await loadReports() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '上报失败') } }
const deleteReport = async (id: number) => { const remark = await ElMessageBox.prompt('请输入删除原因', '删除报表'); if (!remark.value) return; await http.delete(`/api/employment-reports/${id}`, { params: { remark: remark.value } }); ElMessage.success('报表已删除'); await loadReports() }
const openRevision = (row: any) => { revisionReportId.value = row.id; revisionForm.note = ''; revisionForm.baseline_employees = row.baseline_employees; revisionForm.current_employees = row.current_employees; revisionForm.reduction_type = row.reduction_type || ''; revisionForm.primary_reason = row.primary_reason || ''; revisionVisible.value = true }
const saveRevision = async () => { if (!revisionReportId.value) return; try { await http.post(`/api/employment-reports/${revisionReportId.value}/revisions`, revisionForm); ElMessage.success('修订已保存'); revisionVisible.value = false; await loadReports() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '修订失败') } }
const createUser = async () => { try { await http.post('/api/users', userForm); ElMessage.success('用户创建成功'); userForm.username = ''; userForm.password = ''; await loadUsers() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '用户创建失败') } }
const deleteUser = async (id: number) => { await http.delete(`/api/users/${id}`); ElMessage.success('用户已删除'); await loadUsers() }
const createRole = async () => { try { await http.post('/api/roles', roleForm); ElMessage.success('角色创建成功'); roleForm.name = ''; roleForm.permission_codes = []; await loadRoles() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '角色创建失败') } }
const deleteRole = async (id: number) => { await http.delete(`/api/roles/${id}`); ElMessage.success('角色已删除'); await loadRoles() }
const saveNotification = async () => { try { await http.post('/api/notifications', notificationForm); ElMessage.success('通知发布成功'); notificationForm.title = ''; notificationForm.content = ''; await loadNotifications() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '通知发布失败') } }
const deleteNotification = async (id: number) => { await http.delete(`/api/notifications/${id}`); ElMessage.success('通知已删除'); await loadNotifications() }
const saveWindow = async () => { try { await http.post('/api/system/reporting-windows', windowForm); ElMessage.success('上报时限已保存') } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '保存失败') } }
const logout = async () => { localStorage.clear(); await router.push({ name: 'login' }) }

onMounted(async () => { await Promise.all([loadEnterprises(), loadReports(), loadUsers(), loadRoles(), loadNotifications(), loadMonitor()]) })
</script>
