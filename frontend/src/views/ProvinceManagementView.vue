<template>
  <el-space direction="vertical" fill size="20">
    <el-card shadow="never">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <h2 style="margin:0 0 8px">省级综合管理</h2>
          <p style="margin:0;color:#606266">覆盖备案审核、报表管理、用户角色管理、通知管理、系统维护和国家数据交换</p>
        </div>
        <el-space>
          <el-button @click="router.push({ name: 'province-dashboard' })">返回总览</el-button>
          <el-button @click="logout">退出登录</el-button>
        </el-space>
      </div>
    </el-card>

    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="备案审核" name="filing">
        <el-form :inline="true" :model="enterpriseQuery" style="margin-bottom:12px">
          <el-form-item label="地区"><el-input v-model="enterpriseQuery.region" clearable /></el-form-item>
          <el-form-item label="企业名称"><el-input v-model="enterpriseQuery.name" clearable /></el-form-item>
          <el-form-item><el-button type="primary" @click="loadEnterprises">查询</el-button></el-form-item>
          <el-form-item><el-button @click="resetEnterpriseQuery">清空</el-button></el-form-item>
        </el-form>
        <el-table :data="enterprises" stripe>
          <el-table-column prop="region" label="地区" min-width="120" />
          <el-table-column prop="organization_code" label="组织机构代码" min-width="150" />
          <el-table-column prop="name" label="企业名称" min-width="180" />
          <el-table-column prop="industry" label="行业" min-width="160" />
          <el-table-column label="操作" min-width="260">
            <template #default="scope">
              <el-space>
                <el-button type="primary" size="small" @click="viewEnterprise(scope.row)">查看</el-button>
                <el-button type="success" size="small" @click="auditFiling(scope.row.id, 'APPROVE')">通过</el-button>
                <el-button type="danger" size="small" @click="openFilingReject(scope.row.id)">退回</el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="报表管理" name="reports">
        <el-form :inline="true" :model="reportQuery" style="margin-bottom:12px">
          <el-form-item label="统计月份"><el-date-picker v-model="reportQuery.report_month" type="month" value-format="YYYY-MM" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="reportQuery.review_status" clearable style="width:180px"><el-option label="待市级审核" value="PENDING_CITY_REVIEW" /><el-option label="待省级审核" value="PENDING_PROVINCE_REVIEW" /><el-option label="已归档" value="ARCHIVED" /><el-option label="已上报部级" value="REPORTED_TO_MINISTRY" /><el-option label="已退回" value="REJECTED" /></el-select></el-form-item>
          <el-form-item><el-button type="primary" @click="loadReports">查询</el-button></el-form-item>
          <el-form-item><el-button @click="exportReports">导出报表</el-button></el-form-item>
        </el-form>
        <el-table :data="reports" stripe>
          <el-table-column prop="report_month" label="月份" min-width="110" />
          <el-table-column prop="enterprise_id" label="企业ID" min-width="100" />
          <el-table-column prop="baseline_employees" label="建档期人数" min-width="120" />
          <el-table-column prop="current_employees" label="调查期人数" min-width="120" />
          <el-table-column prop="review_status" label="状态" min-width="180" />
          <el-table-column prop="return_remark" label="退回说明" min-width="180" />
          <el-table-column label="操作" min-width="420">
            <template #default="scope">
              <el-space wrap>
                <el-button size="small" type="primary" @click="viewReport(scope.row.id)">查看</el-button>
                <el-button size="small" type="success" @click="finalAudit(scope.row.id)">终审归档</el-button>
                <el-button size="small" type="danger" plain @click="openReportReject(scope.row.id)">退回修改</el-button>
                <el-button size="small" @click="reportToMinistry(scope.row.id)">上报部级</el-button>
                <el-button size="small" type="warning" @click="openRevision(scope.row)">数据修改</el-button>
                <el-button size="small" @click="viewRevisions(scope.row.id)">修订记录</el-button>
                <el-button size="small" type="danger" @click="deleteReport(scope.row.id)">删除</el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="用户管理" name="users">
        <el-form :inline="true" :model="userQuery" style="margin-bottom:12px">
          <el-form-item label="用户名"><el-input v-model="userQuery.username" clearable /></el-form-item>
          <el-form-item label="角色"><el-select v-model="userQuery.role" clearable style="width:120px"><el-option label="省级" value="PROVINCE" /><el-option label="市级" value="CITY" /><el-option label="企业" value="ENTERPRISE" /></el-select></el-form-item>
          <el-form-item label="地区"><el-input v-model="userQuery.region" clearable /></el-form-item>
          <el-form-item><el-button type="primary" @click="loadUsers">查询</el-button></el-form-item>
          <el-form-item><el-button @click="exportUsers">导出</el-button></el-form-item>
          <el-form-item><el-button type="success" @click="openUserEditor()">新增用户</el-button></el-form-item>
        </el-form>
        <el-table :data="users" stripe>
          <el-table-column prop="username" label="用户名" min-width="150" />
          <el-table-column prop="role" label="角色" min-width="120" />
          <el-table-column prop="region" label="地区" min-width="140" />
          <el-table-column prop="is_active" label="启用" min-width="80" />
          <el-table-column label="操作" min-width="180">
            <template #default="scope">
              <el-space>
                <el-button type="primary" link @click="openUserEditor(scope.row)">编辑</el-button>
                <el-button type="danger" link @click="deleteUser(scope.row.id)">删除</el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="角色管理" name="roles">
        <el-button type="success" style="margin-bottom:12px" @click="openRoleEditor()">新增角色</el-button>
        <el-table :data="roles" stripe>
          <el-table-column prop="name" label="角色名" min-width="160" />
          <el-table-column prop="scope_role" label="适用范围" min-width="120" />
          <el-table-column label="权限数" min-width="100"><template #default="scope">{{ scope.row.permissions?.length ?? 0 }}</template></el-table-column>
          <el-table-column label="操作" min-width="180">
            <template #default="scope">
              <el-space>
                <el-button type="primary" link @click="openRoleEditor(scope.row)">编辑</el-button>
                <el-button type="danger" link @click="deleteRole(scope.row.id)">删除</el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="通知管理" name="notifications">
        <el-form :inline="true" :model="notificationQuery" style="margin-bottom:12px">
          <el-form-item label="标题"><el-input v-model="notificationQuery.title" clearable /></el-form-item>
          <el-form-item><el-button type="primary" @click="loadNotifications">查询</el-button></el-form-item>
          <el-form-item><el-button type="success" @click="openNotificationEditor()">新增通知</el-button></el-form-item>
        </el-form>
        <el-table :data="notifications" stripe>
          <el-table-column prop="title" label="标题" min-width="180" />
          <el-table-column prop="published_at" label="发布时间" min-width="180" />
          <el-table-column prop="content" label="内容" min-width="320" />
          <el-table-column label="操作" min-width="180">
            <template #default="scope">
              <el-space>
                <el-button type="primary" link @click="openNotificationEditor(scope.row)">编辑</el-button>
                <el-button type="danger" link @click="deleteNotification(scope.row.id)">删除</el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="系统维护" name="system">
        <el-form :inline="true" :model="windowForm">
          <el-form-item label="月份"><el-date-picker v-model="windowForm.report_month" type="month" value-format="YYYY-MM" /></el-form-item>
          <el-form-item label="开始"><el-date-picker v-model="windowForm.start_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" /></el-form-item>
          <el-form-item label="结束"><el-date-picker v-model="windowForm.end_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" /></el-form-item>
          <el-form-item><el-button type="primary" @click="saveWindow">保存时限</el-button></el-form-item>
        </el-form>
        <el-table :data="windows" stripe style="margin-bottom:16px">
          <el-table-column prop="report_month" label="月份" min-width="120" />
          <el-table-column prop="start_at" label="开始时间" min-width="200" />
          <el-table-column prop="end_at" label="结束时间" min-width="200" />
        </el-table>
        <el-descriptions :column="2" border style="margin-bottom:16px">
          <el-descriptions-item label="CPU">{{ monitor.cpu_percent }}%</el-descriptions-item>
          <el-descriptions-item label="内存">{{ monitor.memory_percent }}%</el-descriptions-item>
          <el-descriptions-item label="磁盘">{{ monitor.disk_percent }}%</el-descriptions-item>
          <el-descriptions-item label="系统时间">{{ monitor.current_time }}</el-descriptions-item>
        </el-descriptions>
        <el-button @click="loadMonitor">刷新监控</el-button>
      </el-tab-pane>

      <el-tab-pane label="数据交换" name="exchange">
        <el-form :inline="true" :model="exchangeForm" style="margin-bottom:12px">
          <el-form-item label="统计月份"><el-date-picker v-model="exchangeForm.report_month" type="month" value-format="YYYY-MM" /></el-form-item>
          <el-form-item><el-button type="primary" @click="exportToMinistry">导出并上报部级</el-button></el-form-item>
          <el-form-item><el-button @click="loadExchangeLogs">刷新日志</el-button></el-form-item>
        </el-form>
        <el-table :data="exchangeLogs" stripe>
          <el-table-column prop="report_month" label="月份" min-width="120" />
          <el-table-column prop="direction" label="方向" min-width="120" />
          <el-table-column prop="initiated_by_id" label="发起人" min-width="120" />
          <el-table-column prop="created_at" label="时间" min-width="180" />
          <el-table-column prop="payload" label="载荷" min-width="360" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="filingRejectVisible" title="备案退回说明">
      <el-input v-model="filingRejectRemark" type="textarea" :rows="4" />
      <template #footer><el-button @click="filingRejectVisible=false">取消</el-button><el-button type="primary" @click="confirmFilingReject">确认退回</el-button></template>
    </el-dialog>

    <el-dialog v-model="revisionVisible" title="报表修订" width="520px">
      <el-input v-model="revisionForm.note" placeholder="修改说明" style="margin-bottom:12px" />
      <el-input-number v-model="revisionForm.baseline_employees" :min="0" style="width:100%;margin-bottom:12px" />
      <el-input-number v-model="revisionForm.current_employees" :min="0" style="width:100%;margin-bottom:12px" />
      <el-select v-model="revisionForm.reduction_type" placeholder="减少类型" style="width:100%;margin-bottom:12px"><el-option v-for="item in reductionTypes" :key="item" :label="item" :value="item" /></el-select>
      <el-select v-model="revisionForm.primary_reason" placeholder="主要原因" style="width:100%;margin-bottom:12px"><el-option v-for="item in reasonOptions" :key="item" :label="item" :value="item" /></el-select>
      <el-input v-model="revisionForm.primary_reason_detail" placeholder="主要原因说明" type="textarea" :rows="3" />
      <template #footer><el-button @click="revisionVisible=false">取消</el-button><el-button type="primary" @click="saveRevision">保存修订</el-button></template>
    </el-dialog>

    <el-dialog v-model="userEditorVisible" :title="editingUserId ? '编辑用户' : '新增用户'" width="520px">
      <el-form :model="userForm" label-width="90px">
        <el-form-item label="用户名"><el-input v-model="userForm.username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="userForm.password" /></el-form-item>
        <el-form-item label="角色"><el-select v-model="userForm.role" style="width:100%"><el-option label="省级" value="PROVINCE" /><el-option label="市级" value="CITY" /><el-option label="企业" value="ENTERPRISE" /></el-select></el-form-item>
        <el-form-item label="地区"><el-input v-model="userForm.region" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="userForm.is_active" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="userEditorVisible=false">取消</el-button><el-button type="primary" @click="saveUser">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="roleEditorVisible" :title="editingRoleId ? '编辑角色' : '新增角色'" width="640px">
      <el-form :model="roleForm" label-width="100px">
        <el-form-item label="角色名"><el-input v-model="roleForm.name" /></el-form-item>
        <el-form-item label="适用范围"><el-select v-model="roleForm.scope_role" style="width:100%"><el-option label="省级" value="PROVINCE" /><el-option label="市级" value="CITY" /><el-option label="企业" value="ENTERPRISE" /></el-select></el-form-item>
        <el-form-item label="权限"><el-select v-model="roleForm.permission_codes" multiple collapse-tags style="width:100%"><el-option v-for="item in permissions" :key="item.code" :label="item.code" :value="item.code" /></el-select></el-form-item>
      </el-form>
      <template #footer><el-button @click="roleEditorVisible=false">取消</el-button><el-button type="primary" @click="saveRole">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="notificationEditorVisible" :title="editingNotificationId ? '编辑通知' : '新增通知'" width="620px">
      <el-form :model="notificationForm" label-width="70px">
        <el-form-item label="标题"><el-input v-model="notificationForm.title" maxlength="50" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="notificationForm.content" type="textarea" :rows="4" maxlength="2000" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="notificationEditorVisible=false">取消</el-button><el-button type="primary" @click="saveNotification">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="revisionListVisible" title="修订记录" width="760px">
      <el-table :data="revisionHistory" stripe>
        <el-table-column prop="created_at" label="时间" min-width="180" />
        <el-table-column prop="note" label="说明" min-width="220" />
        <el-table-column prop="baseline_employees" label="建档期" min-width="100" />
        <el-table-column prop="current_employees" label="调查期" min-width="100" />
        <el-table-column prop="modified_by_id" label="修改人" min-width="100" />
      </el-table>
    </el-dialog>
  </el-space>
    <el-dialog v-model="reportRejectVisible" title="省级退回修改说明" width="520px">
      <el-input v-model="reportRejectRemark" type="textarea" :rows="4" maxlength="500" />
      <template #footer><el-button @click="reportRejectVisible=false">取消</el-button><el-button type="primary" @click="confirmReportReject">确认退回</el-button></template>
    </el-dialog>

    <el-drawer v-model="enterpriseDetailVisible" title="企业备案详情" size="520px">
      <el-descriptions v-if="selectedEnterprise" :column="1" border>
        <el-descriptions-item label="企业名称">{{ selectedEnterprise.name }}</el-descriptions-item>
        <el-descriptions-item label="组织机构代码">{{ selectedEnterprise.organization_code }}</el-descriptions-item>
        <el-descriptions-item label="所属地区">{{ selectedEnterprise.region }}</el-descriptions-item>
        <el-descriptions-item label="企业性质">{{ selectedEnterprise.nature }}</el-descriptions-item>
        <el-descriptions-item label="所属行业">{{ selectedEnterprise.industry }}</el-descriptions-item>
        <el-descriptions-item label="主要经营业务">{{ selectedEnterprise.main_business }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{ selectedEnterprise.contact_person }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ selectedEnterprise.phone }}</el-descriptions-item>
        <el-descriptions-item label="联系地址">{{ selectedEnterprise.address }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ selectedEnterprise.email || '-' }}</el-descriptions-item>
        <el-descriptions-item label="传真">{{ selectedEnterprise.fax || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>

    <el-drawer v-model="reportDetailVisible" title="月报详情" size="520px">
      <el-descriptions v-if="selectedReport" :column="1" border>
        <el-descriptions-item label="统计月份">{{ selectedReport.report_month }}</el-descriptions-item>
        <el-descriptions-item label="企业ID">{{ selectedReport.enterprise_id }}</el-descriptions-item>
        <el-descriptions-item label="建档期人数">{{ selectedReport.baseline_employees }}</el-descriptions-item>
        <el-descriptions-item label="调查期人数">{{ selectedReport.current_employees }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ selectedReport.review_status }}</el-descriptions-item>
        <el-descriptions-item label="减少类型">{{ selectedReport.reduction_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="主要原因">{{ selectedReport.primary_reason || '-' }}</el-descriptions-item>
        <el-descriptions-item label="主要原因说明">{{ selectedReport.primary_reason_detail || '-' }}</el-descriptions-item>
        <el-descriptions-item label="次要原因">{{ selectedReport.secondary_reason || '-' }}</el-descriptions-item>
        <el-descriptions-item label="第三原因">{{ selectedReport.third_reason || '-' }}</el-descriptions-item>
        <el-descriptions-item label="退回说明">{{ selectedReport.return_remark || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
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
const windows = ref<any[]>([])
const exchangeLogs = ref<any[]>([])
const revisionHistory = ref<any[]>([])
const monitor = ref<any>({ cpu_percent: 0, memory_percent: 0, disk_percent: 0, current_time: '' })
const filingRejectVisible = ref(false)
const filingRejectId = ref<number | null>(null)
const filingRejectRemark = ref('')
const revisionVisible = ref(false)
const reportRejectVisible = ref(false)
const reportRejectId = ref<number | null>(null)
const reportRejectRemark = ref('')
const revisionListVisible = ref(false)
const revisionReportId = ref<number | null>(null)
const userEditorVisible = ref(false)
const roleEditorVisible = ref(false)
const notificationEditorVisible = ref(false)
const enterpriseDetailVisible = ref(false)
const reportDetailVisible = ref(false)
const selectedEnterprise = ref<any>(null)
const selectedReport = ref<any>(null)
const editingUserId = ref<number | null>(null)
const editingRoleId = ref<number | null>(null)
const editingNotificationId = ref<number | null>(null)

const reasonOptions = ['产业结构调整','重大技术改革','节能减排、淘汰落后产能','订单不足','原材料涨价','工资、社保等用工成本上升','经营资金困难','税收政策变化（包括税负增加或出口退税减少等）','季节性用工','其他','自行离职','工作调动、企业内部调剂','劳动关系转移、劳务派遣','退休','退职','死亡','自然减员','国际因素变化','招不上人来']
const reductionTypes = ['关闭破产','停业整顿','经济性裁员','业务转移','自然减员','正常解除或终止劳动合同','国际因素变化影响','自然灾害','重大事件影响','其他']

const enterpriseQuery = reactive({ region: '', name: '' })
const reportQuery = reactive({ report_month: '', review_status: '' })
const userQuery = reactive({ username: '', role: '', region: '' })
const notificationQuery = reactive({ title: '' })
const exchangeForm = reactive({ report_month: '' })
const userForm = reactive({ username: '', password: '', role: 'CITY', region: 'Kunming', is_active: true })
const roleForm = reactive({ name: '', scope_role: 'CITY', permission_codes: [] as string[] })
const notificationForm = reactive({ title: '', content: '' })
const windowForm = reactive({ report_month: '', start_at: '', end_at: '' })
const revisionForm = reactive({ note: '', baseline_employees: 0, current_employees: 0, reduction_type: '', primary_reason: '', primary_reason_detail: '' })

const loadEnterprises = async () => {
  const { data } = await http.get('/api/enterprises', { params: { filing_status: 'PENDING', region: enterpriseQuery.region || undefined, name: enterpriseQuery.name || undefined } })
  enterprises.value = data
}
const resetEnterpriseQuery = async () => { enterpriseQuery.region = ''; enterpriseQuery.name = ''; await loadEnterprises() }
const loadReports = async () => {
  const { data } = await http.get('/api/employment-reports', { params: { report_month: reportQuery.report_month || undefined, review_status: reportQuery.review_status || undefined } })
  reports.value = data
}
const loadUsers = async () => {
  const { data } = await http.get('/api/users', { params: { username: userQuery.username || undefined, role: userQuery.role || undefined, region: userQuery.region || undefined } })
  users.value = data
}
const loadRoles = async () => {
  const [roleRes, permissionRes] = await Promise.all([http.get('/api/roles'), http.get('/api/permissions')])
  roles.value = roleRes.data
  permissions.value = permissionRes.data
}
const loadNotifications = async () => {
  const { data } = await http.get('/api/notifications/manage')
  notifications.value = notificationQuery.title ? data.filter((item: any) => item.title.includes(notificationQuery.title)) : data
}
const loadWindows = async () => {
  const { data } = await http.get('/api/system/reporting-windows')
  windows.value = data
}
const loadMonitor = async () => {
  const { data } = await http.get('/api/system/monitor')
  monitor.value = data
}
const loadExchangeLogs = async () => {
  const { data } = await http.get('/api/integration/exchange-logs')
  exchangeLogs.value = data
}
const auditFiling = async (id: number, action: 'APPROVE' | 'REJECT', remark?: string) => {
  await http.post(`/api/enterprises/${id}/filing-audit`, { action, remark })
  ElMessage.success(action === 'APPROVE' ? '备案审核通过' : '备案已退回')
  await loadEnterprises()
}
const openFilingReject = (id: number) => { filingRejectId.value = id; filingRejectRemark.value = ''; filingRejectVisible.value = true }
const confirmFilingReject = async () => { if (!filingRejectId.value || !filingRejectRemark.value) return; await auditFiling(filingRejectId.value, 'REJECT', filingRejectRemark.value); filingRejectVisible.value = false }
const viewEnterprise = (row: any) => { selectedEnterprise.value = row; enterpriseDetailVisible.value = true }
const finalAudit = async (id: number) => { try { await http.post(`/api/employment-reports/${id}/final-audit`); ElMessage.success('终审归档成功'); await loadReports() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '终审失败') } }
const openReportReject = (id: number) => { reportRejectId.value = id; reportRejectRemark.value = ''; reportRejectVisible.value = true }
const confirmReportReject = async () => {
  if (!reportRejectId.value || !reportRejectRemark.value) return
  try {
    await http.post(`/api/employment-reports/${reportRejectId.value}/province-return`, { action: 'REJECT', remark: reportRejectRemark.value })
    ElMessage.success('报表已退回修改')
    reportRejectVisible.value = false
    await loadReports()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? '退回失败')
  }
}
const viewReport = async (id: number) => {
  try {
    const { data } = await http.get(`/api/employment-reports/${id}`)
    selectedReport.value = data
    reportDetailVisible.value = true
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? '报表详情加载失败')
  }
}
const reportToMinistry = async (id: number) => { try { await http.post(`/api/employment-reports/${id}/report-to-ministry`); ElMessage.success('已上报部级'); await loadReports() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '上报失败') } }
const deleteReport = async (id: number) => { const remark = await ElMessageBox.prompt('请输入删除原因', '删除报表'); if (!remark.value) return; await http.delete(`/api/employment-reports/${id}`, { params: { remark: remark.value } }); ElMessage.success('报表已删除'); await loadReports() }
const openRevision = (row: any) => { revisionReportId.value = row.id; revisionForm.note = ''; revisionForm.baseline_employees = row.baseline_employees; revisionForm.current_employees = row.current_employees; revisionForm.reduction_type = row.reduction_type || ''; revisionForm.primary_reason = row.primary_reason || ''; revisionForm.primary_reason_detail = row.primary_reason_detail || ''; revisionVisible.value = true }
const saveRevision = async () => { if (!revisionReportId.value) return; try { await http.post(`/api/employment-reports/${revisionReportId.value}/revisions`, revisionForm); ElMessage.success('修订已保存'); revisionVisible.value = false; await loadReports() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '修订失败') } }
const viewRevisions = async (id: number) => { const { data } = await http.get(`/api/employment-reports/${id}/revisions`); revisionHistory.value = data; revisionListVisible.value = true }
const openUserEditor = (row?: any) => { editingUserId.value = row?.id ?? null; userForm.username = row?.username ?? ''; userForm.password = ''; userForm.role = row?.role ?? 'CITY'; userForm.region = row?.region ?? 'Kunming'; userForm.is_active = row?.is_active ?? true; userEditorVisible.value = true }
const saveUser = async () => { try { if (editingUserId.value) { await http.put(`/api/users/${editingUserId.value}`, { ...userForm, password: userForm.password || undefined }) } else { await http.post('/api/users', userForm) } ElMessage.success('用户保存成功'); userEditorVisible.value = false; await loadUsers() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '用户保存失败') } }
const deleteUser = async (id: number) => { try { await http.delete(`/api/users/${id}`); ElMessage.success('用户已删除'); await loadUsers() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '删除失败') } }
const exportUsers = async () => { const response = await http.get('/api/users/export', { params: { username: userQuery.username || undefined, role: userQuery.role || undefined, region: userQuery.region || undefined }, responseType: 'blob' }); downloadBlob(response.data, 'users.xlsx') }
const openRoleEditor = (row?: any) => { editingRoleId.value = row?.id ?? null; roleForm.name = row?.name ?? ''; roleForm.scope_role = row?.scope_role ?? 'CITY'; roleForm.permission_codes = row?.permissions?.map((item: any) => item.code) ?? []; roleEditorVisible.value = true }
const saveRole = async () => { try { if (editingRoleId.value) { await http.put(`/api/roles/${editingRoleId.value}`, roleForm) } else { await http.post('/api/roles', roleForm) } ElMessage.success('角色保存成功'); roleEditorVisible.value = false; await loadRoles() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '角色保存失败') } }
const deleteRole = async (id: number) => { try { await http.delete(`/api/roles/${id}`); ElMessage.success('角色已删除'); await loadRoles() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '删除失败') } }
const openNotificationEditor = (row?: any) => { editingNotificationId.value = row?.id ?? null; notificationForm.title = row?.title ?? ''; notificationForm.content = row?.content ?? ''; notificationEditorVisible.value = true }
const saveNotification = async () => { try { if (editingNotificationId.value) { await http.put(`/api/notifications/${editingNotificationId.value}`, notificationForm) } else { await http.post('/api/notifications', notificationForm) } ElMessage.success('通知保存成功'); notificationEditorVisible.value = false; await loadNotifications() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '通知保存失败') } }
const deleteNotification = async (id: number) => { try { await http.delete(`/api/notifications/${id}`); ElMessage.success('通知已删除'); await loadNotifications() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '删除失败') } }
const saveWindow = async () => { try { await http.post('/api/system/reporting-windows', windowForm); ElMessage.success('上报时限已保存'); await loadWindows() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '保存失败') } }
const exportReports = async () => { const response = await http.get('/api/province/reports/export', { params: { report_month: reportQuery.report_month || undefined }, responseType: 'blob' }); downloadBlob(response.data, 'employment_reports.xlsx') }
const exportToMinistry = async () => { try { const { data } = await http.get('/api/integration/ministry/export', { params: { report_month: exchangeForm.report_month } }); ElMessage.success(`已导出并上报 ${data.row_count} 条数据`); await Promise.all([loadExchangeLogs(), loadReports()]) } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '交换失败') } }
const downloadBlob = (data: BlobPart, filename: string) => { const blobUrl = window.URL.createObjectURL(new Blob([data])); const link = document.createElement('a'); link.href = blobUrl; link.download = filename; link.click(); window.URL.revokeObjectURL(blobUrl) }
const logout = async () => { localStorage.clear(); await router.push({ name: 'login' }) }

onMounted(async () => {
  await Promise.all([loadEnterprises(), loadReports(), loadUsers(), loadRoles(), loadNotifications(), loadWindows(), loadMonitor(), loadExchangeLogs()])
})
</script>
