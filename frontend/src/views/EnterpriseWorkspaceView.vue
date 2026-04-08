<template>
  <DashboardShell
    v-model:active-key="activeNav"
    title="工作台"
    subtitle="完成企业备案、月报填报、历史查询和通知浏览。"
    :nav-items="navItems"
    :user-name="currentUserName"
    user-role="ENTERPRISE"
    current-role="ENTERPRISE"
    @logout="logout"
  >
    <template #stats>
      <DashboardMetricCard eyebrow="备案状态" :value="filingStatusText(enterpriseInfo?.filing_status ?? 'PENDING')" accent="blue" description="企业基础信息审核结果" />
      <DashboardMetricCard eyebrow="月报总数" :value="reports.length" accent="green" description="当前账号已提交月报" />
      <DashboardMetricCard eyebrow="待审核" :value="pendingCount" accent="orange" description="待市级或省级审核的月报" />
      <DashboardMetricCard eyebrow="通知公告" :value="notifications.length" accent="red" description="可浏览的系统通知数量" />
    </template>

    <section v-if="activeNav === 'overview'" class="workspace-stack">
      <div class="workspace-grid">
        <article class="surface-card">
          <div class="surface-card__header">
            <div>
              <h3>企业概况</h3>
              <p>查看当前备案状态和基础信息。</p>
            </div>
            <el-tag :type="statusTagType(enterpriseInfo?.filing_status ?? 'PENDING')">
              {{ filingStatusText(enterpriseInfo?.filing_status ?? 'PENDING') }}
            </el-tag>
          </div>
          <div class="surface-card__body">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="企业名称">{{ enterpriseInfo?.name || '未备案' }}</el-descriptions-item>
              <el-descriptions-item label="所属地区">{{ enterpriseInfo?.region || currentRegion }}</el-descriptions-item>
              <el-descriptions-item label="组织机构代码">{{ enterpriseInfo?.organization_code || '-' }}</el-descriptions-item>
              <el-descriptions-item label="所属行业">{{ enterpriseInfo?.industry || '-' }}</el-descriptions-item>
              <el-descriptions-item label="联系人">{{ enterpriseInfo?.contact_person || '-' }}</el-descriptions-item>
              <el-descriptions-item label="联系电话">{{ enterpriseInfo?.phone || '-' }}</el-descriptions-item>
              <el-descriptions-item label="退回说明" :span="2">{{ enterpriseInfo?.filing_audit_remark || '无' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </article>

        <article class="surface-card">
          <div class="surface-card__header">
            <div>
              <h3>上报提醒</h3>
              <p>查看当前月份的上报时限和处理建议。</p>
            </div>
          </div>
          <div class="surface-card__body">
            <el-alert :title="windowTip" :type="windowTipType" :closable="false" />
            <div style="margin-top:18px;display:grid;gap:12px">
              <el-button type="primary" round @click="activeNav = 'report'">立即填报月报</el-button>
              <el-button round @click="activeNav = 'filing'">完善备案信息</el-button>
              <el-button round @click="activeNav = 'history'">查看历史记录</el-button>
            </div>
          </div>
        </article>
      </div>

      <article class="surface-card">
        <div class="surface-card__header">
          <div>
            <h3>最近上报记录</h3>
            <p>展示当前账号最近提交的月报。</p>
          </div>
          <el-button link type="primary" @click="activeNav = 'history'">查看全部</el-button>
        </div>
        <div class="surface-card__body">
          <el-table :data="reports.slice(0, 5)" stripe>
            <el-table-column prop="report_month" label="统计月份" min-width="120" />
            <el-table-column prop="baseline_employees" label="建档期人数" min-width="120" />
            <el-table-column prop="current_employees" label="调查期人数" min-width="120" />
            <el-table-column prop="review_status" label="状态" min-width="160">
              <template #default="{ row }">{{ reviewStatusText(row.review_status) }}</template>
            </el-table-column>
            <el-table-column prop="return_remark" label="退回说明" min-width="220" />
          </el-table>
        </div>
      </article>
    </section>

    <article v-else-if="activeNav === 'filing'" class="surface-card">
      <div class="surface-card__header">
        <div>
          <h3>企业信息备案</h3>
          <p>按要求完善企业基础信息并提交审核。</p>
        </div>
      </div>
      <div class="surface-card__body">
        <el-form ref="filingFormRef" :model="filingForm" :rules="filingRules" label-width="120px">
          <el-row :gutter="16">
            <el-col :xs="24" :md="12"><el-form-item label="所属地区" prop="region"><el-input v-model="filingForm.region" disabled /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="组织机构代码" prop="organization_code"><el-input v-model="filingForm.organization_code" maxlength="9" show-word-limit /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="企业名称" prop="name"><el-input v-model="filingForm.name" /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="企业性质" prop="nature"><el-select v-model="filingForm.nature" placeholder="请选择企业性质" style="width:100%"><el-option v-for="item in enterpriseNatureOptions" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="所属行业" prop="industry_path"><el-cascader v-model="filingForm.industry_path" :options="industryOptions" clearable style="width:100%" /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="主营业务" prop="main_business"><el-input v-model="filingForm.main_business" type="textarea" :rows="3" /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="联系人" prop="contact_person"><el-input v-model="filingForm.contact_person" /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="联系电话" prop="phone"><el-input v-model="filingForm.phone" /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="联系地址" prop="address"><el-input v-model="filingForm.address" /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="邮政编码" prop="postal_code"><el-input v-model="filingForm.postal_code" maxlength="6" /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="传真" prop="fax"><el-input v-model="filingForm.fax" /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="邮箱" prop="email"><el-input v-model="filingForm.email" /></el-form-item></el-col>
          </el-row>
          <el-space wrap>
            <el-button type="primary" :loading="filingSubmitting" @click="submitFiling">提交备案</el-button>
            <el-button @click="loadEnterprise">重新加载</el-button>
          </el-space>
        </el-form>
      </div>
    </article>

    <article v-else-if="activeNav === 'report'" class="surface-card">
      <div class="surface-card__header">
        <div>
          <h3>月度数据填报</h3>
          <p>调查期人数低于建档期人数时，系统会自动要求填写减少类型和原因。</p>
        </div>
      </div>
      <div class="surface-card__body">
        <el-alert :title="windowTip" :type="windowTipType" :closable="false" style="margin-bottom:18px" />
        <el-form ref="reportFormRef" :model="reportForm" :rules="reportRules" label-width="130px">
          <el-row :gutter="16">
            <el-col :xs="24" :md="12"><el-form-item label="统计月份" prop="report_month"><el-date-picker v-model="reportForm.report_month" type="month" value-format="YYYY-MM" style="width:100%" /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="建档期人数" prop="baseline_employees"><el-input-number v-model="reportForm.baseline_employees" :min="0" style="width:100%" /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="调查期人数" prop="current_employees"><el-input-number v-model="reportForm.current_employees" :min="0" style="width:100%" /></el-form-item></el-col>
          </el-row>

          <el-row v-if="showReductionFields" :gutter="16">
            <el-col :xs="24" :md="12"><el-form-item label="减少类型" prop="reduction_type"><el-select v-model="reportForm.reduction_type" style="width:100%"><el-option v-for="item in reductionTypeOptions" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="主要原因" prop="primary_reason"><el-select v-model="reportForm.primary_reason" style="width:100%"><el-option v-for="item in reasonOptions" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="主要原因说明" prop="primary_reason_detail"><el-input v-model="reportForm.primary_reason_detail" type="textarea" :rows="3" /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="次要原因"><el-select v-model="reportForm.secondary_reason" clearable style="width:100%"><el-option v-for="item in reasonOptions" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="次要原因说明"><el-input v-model="reportForm.secondary_reason_detail" type="textarea" :rows="3" /></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="第三原因"><el-select v-model="reportForm.third_reason" clearable style="width:100%"><el-option v-for="item in reasonOptions" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
            <el-col :xs="24" :md="12"><el-form-item label="第三原因说明"><el-input v-model="reportForm.third_reason_detail" type="textarea" :rows="3" /></el-form-item></el-col>
          </el-row>

          <el-space>
            <el-button type="primary" :loading="reportSubmitting" @click="submitReport">提交月报</el-button>
            <el-button @click="resetReportForm">重置</el-button>
          </el-space>
        </el-form>
      </div>
    </article>

    <article v-else-if="activeNav === 'history'" class="surface-card">
      <div class="surface-card__header">
        <div>
          <h3>历史记录</h3>
          <p>按月份和审核状态筛选已提交的月报。</p>
        </div>
      </div>
      <div class="surface-card__body">
        <el-form :inline="true" :model="historyQuery" style="margin-bottom:12px">
          <el-form-item label="统计月份"><el-date-picker v-model="historyQuery.report_month" type="month" value-format="YYYY-MM" /></el-form-item>
          <el-form-item label="审核状态"><el-select v-model="historyQuery.review_status" clearable style="width:180px"><el-option v-for="item in reviewStatusOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
          <el-form-item><el-button type="primary" @click="loadReports">查询</el-button></el-form-item>
          <el-form-item><el-button @click="resetHistoryQuery">重置</el-button></el-form-item>
        </el-form>
        <el-table :data="reports" stripe>
          <el-table-column prop="report_month" label="统计月份" min-width="120" />
          <el-table-column prop="baseline_employees" label="建档期人数" min-width="120" />
          <el-table-column prop="current_employees" label="调查期人数" min-width="120" />
          <el-table-column prop="review_status" label="审核状态" min-width="160">
            <template #default="{ row }">{{ reviewStatusText(row.review_status) }}</template>
          </el-table-column>
          <el-table-column prop="return_remark" label="退回说明" min-width="220" />
          <el-table-column label="操作" min-width="100">
            <template #default="{ row }">
              <el-button type="primary" link @click="openReportDetail(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </article>

    <article v-else-if="activeNav === 'notifications'" class="surface-card">
      <div class="surface-card__header">
        <div>
          <h3>通知公告</h3>
          <p>查看市级和省级发布的最新通知。</p>
        </div>
        <el-button round @click="loadNotifications">刷新通知</el-button>
      </div>
      <div class="surface-card__body">
        <el-table :data="notifications" stripe>
          <el-table-column prop="title" label="标题" min-width="180" />
          <el-table-column prop="published_at" label="发布时间" min-width="180" />
          <el-table-column prop="content" label="内容" min-width="360" />
        </el-table>
      </div>
    </article>

    <article v-else class="surface-card">
      <div class="surface-card__header">
        <div>
          <h3>账户安全</h3>
          <p>定期修改密码，确保账号安全。</p>
        </div>
      </div>
      <div class="surface-card__body" style="max-width:560px">
        <el-form ref="passwordFormRef" :model="passwordForm" label-width="100px">
          <el-form-item label="旧密码"><el-input v-model="passwordForm.old_password" type="password" show-password /></el-form-item>
          <el-form-item label="新密码"><el-input v-model="passwordForm.new_password" type="password" show-password /></el-form-item>
          <el-button type="primary" @click="changePassword">修改密码</el-button>
        </el-form>
      </div>
    </article>

    <el-drawer v-model="reportDetailVisible" title="月报详情" size="520px">
      <el-descriptions v-if="selectedReport" :column="1" border>
        <el-descriptions-item label="统计月份">{{ selectedReport.report_month }}</el-descriptions-item>
        <el-descriptions-item label="审核状态">{{ reviewStatusText(selectedReport.review_status) }}</el-descriptions-item>
        <el-descriptions-item label="建档期人数">{{ selectedReport.baseline_employees }}</el-descriptions-item>
        <el-descriptions-item label="调查期人数">{{ selectedReport.current_employees }}</el-descriptions-item>
        <el-descriptions-item label="减少类型">{{ selectedReport.reduction_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="主要原因">{{ selectedReport.primary_reason || '-' }}</el-descriptions-item>
        <el-descriptions-item label="主要原因说明">{{ selectedReport.primary_reason_detail || '-' }}</el-descriptions-item>
        <el-descriptions-item label="次要原因">{{ selectedReport.secondary_reason || '-' }}</el-descriptions-item>
        <el-descriptions-item label="第三原因">{{ selectedReport.third_reason || '-' }}</el-descriptions-item>
        <el-descriptions-item label="退回说明">{{ selectedReport.return_remark || '无' }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </DashboardShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import http from '../api/http'
import DashboardMetricCard from '../components/DashboardMetricCard.vue'
import DashboardShell from '../components/DashboardShell.vue'

const router = useRouter()
const activeNav = ref('overview')
const filingFormRef = ref<FormInstance>()
const reportFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const filingSubmitting = ref(false)
const reportSubmitting = ref(false)
const enterpriseInfo = ref<any>(null)
const reports = ref<any[]>([])
const notifications = ref<any[]>([])
const selectedReport = ref<any>(null)
const reportDetailVisible = ref(false)
const windowInfo = ref<any>(null)
const currentRegion = localStorage.getItem('user_region') ?? 'Kunming'
const currentUserName = localStorage.getItem('username') ?? '企业用户'

const navItems = computed(() => [
  { key: 'overview', label: '工作台' },
  { key: 'filing', label: '企业备案' },
  { key: 'report', label: '数据填报' },
  { key: 'history', label: '历史记录' },
  { key: 'notifications', label: '通知公告', badge: notifications.value.length || undefined },
  { key: 'password', label: '账户安全' },
])

const enterpriseNatureOptions = ['国有企业', '集体企业', '私营企业', '股份制企业', '外商投资企业', '港澳台投资企业', '其他企业']
const industryOptions = [
  { value: '制造业', label: '制造业', children: [{ value: '装备制造', label: '装备制造' }, { value: '食品加工', label: '食品加工' }, { value: '医药制造', label: '医药制造' }] },
  { value: '建筑业', label: '建筑业', children: [{ value: '房屋建筑', label: '房屋建筑' }, { value: '市政工程', label: '市政工程' }, { value: '装饰装修', label: '装饰装修' }] },
  { value: '批发和零售业', label: '批发和零售业', children: [{ value: '批发业', label: '批发业' }, { value: '零售业', label: '零售业' }] },
  { value: '住宿和餐饮业', label: '住宿和餐饮业', children: [{ value: '住宿业', label: '住宿业' }, { value: '餐饮业', label: '餐饮业' }] },
  { value: '信息传输、软件和信息技术服务业', label: '信息传输、软件和信息技术服务业', children: [{ value: '软件开发', label: '软件开发' }, { value: '信息技术服务', label: '信息技术服务' }] },
  { value: '居民服务业', label: '居民服务业', children: [{ value: '居民服务', label: '居民服务' }, { value: '其他服务', label: '其他服务' }] },
]
const reasonOptions = ['产业结构调整', '重大技术改革', '节能减排、淘汰落后产能', '订单不足', '原材料涨价', '工资、社保等用工成本上升', '经营资金困难', '税收政策变化（包括税负增加或出口退税减少等）', '季节性用工', '其他', '自行离职', '工作调动、企业内部调剂', '劳动关系转移、劳务派遣', '退休', '退职', '死亡', '自然减员', '国际因素变化', '招不上人来']
const reductionTypeOptions = ['关闭破产', '停业整顿', '经济性裁员', '业务转移', '自然减员', '正常解除或终止劳动合同', '国际因素变化影响', '自然灾害', '重大事件影响', '其他']
const reviewStatusOptions = [
  { label: '待市级审核', value: 'PENDING_CITY_REVIEW' },
  { label: '待省级审核', value: 'PENDING_PROVINCE_REVIEW' },
  { label: '已归档', value: 'ARCHIVED' },
  { label: '已上报部级', value: 'REPORTED_TO_MINISTRY' },
  { label: '已退回', value: 'REJECTED' },
]

const filingForm = reactive({
  region: currentRegion,
  organization_code: '',
  name: '',
  nature: '',
  industry_path: [] as string[],
  main_business: '',
  contact_person: '',
  phone: '',
  address: '',
  postal_code: '',
  fax: '',
  email: '',
})
const reportForm = reactive({
  report_month: '',
  baseline_employees: 0,
  current_employees: 0,
  reduction_type: '',
  primary_reason: '',
  primary_reason_detail: '',
  secondary_reason: '',
  secondary_reason_detail: '',
  third_reason: '',
  third_reason_detail: '',
})
const historyQuery = reactive({ report_month: '', review_status: '' })
const passwordForm = reactive({ old_password: '', new_password: '' })

const showReductionFields = computed(() => reportForm.current_employees < reportForm.baseline_employees)
const pendingCount = computed(() => reports.value.filter((item) => ['PENDING_CITY_REVIEW', 'PENDING_PROVINCE_REVIEW'].includes(item.review_status)).length)
const windowTip = computed(() => {
  if (!reportForm.report_month) return '请选择统计月份后查看该月上报时限。'
  if (windowInfo.value === null) return '当前月份尚未配置上报时限，提交前请联系省级管理员。'
  return `上报时限：${windowInfo.value.start_at} 至 ${windowInfo.value.end_at}`
})
const windowTipType = computed(() => windowInfo.value === null ? 'warning' : 'info')

const organizationCodeValidator = (_rule: any, value: string, callback: (error?: Error) => void) => {
  if (!/^[A-Za-z0-9]{9}$/.test(value)) callback(new Error('组织机构代码必须是 9 位字母或数字'))
  else callback()
}
const phoneValidator = (_rule: any, value: string, callback: (error?: Error) => void) => {
  if (!/^(?:1[3-9]\d{9}|\(?0\d{2,3}\)?-?\d{7,8})$/.test(value)) callback(new Error('请输入正确的手机号或带区号座机'))
  else callback()
}
const postalValidator = (_rule: any, value: string, callback: (error?: Error) => void) => {
  if (!/^\d{6}$/.test(value)) callback(new Error('邮政编码必须是 6 位数字'))
  else callback()
}

const filingRules: FormRules = {
  organization_code: [{ required: true, message: '请输入组织机构代码', trigger: 'blur' }, { validator: organizationCodeValidator, trigger: 'blur' }],
  name: [{ required: true, message: '请输入企业名称', trigger: 'blur' }],
  nature: [{ required: true, message: '请选择企业性质', trigger: 'change' }],
  industry_path: [{ required: true, message: '请选择所属行业', trigger: 'change' }],
  main_business: [{ required: true, message: '请输入主营业务', trigger: 'blur' }],
  contact_person: [{ required: true, message: '请输入联系人', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }, { validator: phoneValidator, trigger: 'blur' }],
  address: [{ required: true, message: '请输入联系地址', trigger: 'blur' }],
  postal_code: [{ required: true, message: '请输入邮政编码', trigger: 'blur' }, { validator: postalValidator, trigger: 'blur' }],
}
const reportRules: FormRules = {
  report_month: [{ required: true, message: '请选择统计月份', trigger: 'change' }],
  baseline_employees: [{ required: true, message: '请输入建档期人数', trigger: 'change' }],
  current_employees: [{ required: true, message: '请输入调查期人数', trigger: 'change' }],
  reduction_type: [{ validator: (_r, value, cb) => showReductionFields.value && !value ? cb(new Error('人数下降时必须填写减少类型')) : cb(), trigger: 'change' }],
  primary_reason: [{ validator: (_r, value, cb) => showReductionFields.value && !value ? cb(new Error('人数下降时必须填写主要原因')) : cb(), trigger: 'change' }],
  primary_reason_detail: [{ validator: (_r, value, cb) => showReductionFields.value && !value ? cb(new Error('人数下降时必须填写主要原因说明')) : cb(), trigger: 'blur' }],
}

const filingStatusText = (status: string) => ({ PENDING: '待审核', APPROVED: '已通过', REJECTED: '已退回' }[status] ?? status)
const reviewStatusText = (status: string) => ({
  PENDING_CITY_REVIEW: '待市级审核',
  PENDING_PROVINCE_REVIEW: '待省级审核',
  ARCHIVED: '已归档',
  REPORTED_TO_MINISTRY: '已上报部级',
  REJECTED: '已退回',
}[status] ?? status)
const statusTagType = (status: string) => status === 'APPROVED' ? 'success' : status === 'REJECTED' ? 'danger' : 'warning'

const applyEnterpriseToForm = (data: any) => {
  filingForm.region = data.region ?? currentRegion
  filingForm.organization_code = data.organization_code ?? ''
  filingForm.name = data.name ?? ''
  filingForm.nature = data.nature ?? ''
  filingForm.industry_path = data.industry ? String(data.industry).split('/') : []
  filingForm.main_business = data.main_business ?? ''
  filingForm.contact_person = data.contact_person ?? ''
  filingForm.phone = data.phone ?? ''
  filingForm.address = data.address ?? ''
  filingForm.postal_code = data.postal_code ?? ''
  filingForm.fax = data.fax ?? ''
  filingForm.email = data.email ?? ''
}

const loadEnterprise = async () => {
  try {
    const { data } = await http.get('/api/enterprises/me')
    enterpriseInfo.value = data
    applyEnterpriseToForm(data)
  } catch (error: any) {
    if (error?.response?.status !== 404) {
      ElMessage.error(error?.response?.data?.detail ?? '企业备案信息加载失败')
    }
    enterpriseInfo.value = { region: currentRegion, filing_status: 'PENDING', filing_audit_remark: '' }
  }
}

const loadReports = async () => {
  const params = {
    report_month: historyQuery.report_month || undefined,
    review_status: historyQuery.review_status || undefined,
  }
  const { data } = await http.get('/api/employment-reports', { params })
  reports.value = data
}

const loadNotifications = async () => {
  const { data } = await http.get('/api/notifications/browse')
  notifications.value = data
}

const loadReportingWindow = async (reportMonth: string) => {
  if (!reportMonth) {
    windowInfo.value = null
    return
  }
  try {
    const { data } = await http.get(`/api/system/reporting-windows/${reportMonth}`)
    windowInfo.value = data
  } catch (error: any) {
    if (error?.response?.status === 404) {
      windowInfo.value = null
      return
    }
    windowInfo.value = null
    ElMessage.error(error?.response?.data?.detail ?? '上报时限查询失败')
  }
}

const submitFiling = async () => {
  if (!filingFormRef.value) return
  const valid = await filingFormRef.value.validate().catch(() => false)
  if (!valid) return
  filingSubmitting.value = true
  try {
    const payload = {
      region: filingForm.region,
      organization_code: filingForm.organization_code,
      name: filingForm.name,
      nature: filingForm.nature,
      industry: filingForm.industry_path.join('/'),
      main_business: filingForm.main_business,
      contact_person: filingForm.contact_person,
      phone: filingForm.phone,
      address: filingForm.address,
      postal_code: filingForm.postal_code,
      fax: filingForm.fax || null,
      email: filingForm.email || null,
    }
    const { data } = await http.post('/api/enterprises/filing/submit', payload)
    enterpriseInfo.value = data
    applyEnterpriseToForm(data)
    ElMessage.success('备案提交成功')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? '备案提交失败')
  } finally {
    filingSubmitting.value = false
  }
}

const submitReport = async () => {
  if (!reportFormRef.value) return
  const valid = await reportFormRef.value.validate().catch(() => false)
  if (!valid) return
  reportSubmitting.value = true
  try {
    await http.post('/api/employment-reports/submit', {
      ...reportForm,
      reduction_type: reportForm.reduction_type || null,
      primary_reason: reportForm.primary_reason || null,
      primary_reason_detail: reportForm.primary_reason_detail || null,
      secondary_reason: reportForm.secondary_reason || null,
      secondary_reason_detail: reportForm.secondary_reason_detail || null,
      third_reason: reportForm.third_reason || null,
      third_reason_detail: reportForm.third_reason_detail || null,
    })
    ElMessage.success('月报提交成功')
    resetReportForm()
    await loadReports()
    activeNav.value = 'history'
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? '月报提交失败')
  } finally {
    reportSubmitting.value = false
  }
}

const resetReportForm = () => {
  reportForm.report_month = ''
  reportForm.baseline_employees = 0
  reportForm.current_employees = 0
  reportForm.reduction_type = ''
  reportForm.primary_reason = ''
  reportForm.primary_reason_detail = ''
  reportForm.secondary_reason = ''
  reportForm.secondary_reason_detail = ''
  reportForm.third_reason = ''
  reportForm.third_reason_detail = ''
  windowInfo.value = null
}

const resetHistoryQuery = async () => {
  historyQuery.report_month = ''
  historyQuery.review_status = ''
  await loadReports()
}

const openReportDetail = (row: any) => {
  selectedReport.value = row
  reportDetailVisible.value = true
}

const changePassword = async () => {
  try {
    await http.post('/api/auth/change-password', passwordForm)
    ElMessage.success('密码修改成功')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? '密码修改失败')
  }
}

const logout = async () => {
  localStorage.clear()
  await router.push({ name: 'login' })
}

watch(() => reportForm.report_month, (value) => {
  void loadReportingWindow(value)
})

onMounted(async () => {
  await Promise.all([loadEnterprise(), loadReports(), loadNotifications()])
})
</script>
