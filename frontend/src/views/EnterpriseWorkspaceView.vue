<template>
  <el-space direction="vertical" fill size="20">
    <el-card shadow="never">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:16px">
        <div>
          <h2 style="margin:0 0 8px">企业工作台</h2>
          <p style="margin:0;color:#606266">备案、填报、历史查询、通知浏览和密码修改</p>
        </div>
        <el-button @click="logout">退出登录</el-button>
      </div>
    </el-card>

    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="企业备案" name="filing">
        <el-form ref="filingFormRef" :model="filingForm" :rules="filingRules" label-width="110px">
          <el-row :gutter="16">
            <el-col :span="12"><el-form-item label="所属地区" prop="region"><el-input v-model="filingForm.region" disabled /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="组织机构代码" prop="organization_code"><el-input v-model="filingForm.organization_code" maxlength="9" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="企业名称" prop="name"><el-input v-model="filingForm.name" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="企业性质" prop="nature"><el-input v-model="filingForm.nature" placeholder="如：民营企业" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="所属行业" prop="industry"><el-input v-model="filingForm.industry" placeholder="二级行业，用 / 分隔" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="主要经营业务" prop="main_business"><el-input v-model="filingForm.main_business" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="联系人" prop="contact_person"><el-input v-model="filingForm.contact_person" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="联系电话" prop="phone"><el-input v-model="filingForm.phone" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="联系地址" prop="address"><el-input v-model="filingForm.address" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="邮政编码" prop="postal_code"><el-input v-model="filingForm.postal_code" maxlength="6" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="传真" prop="fax"><el-input v-model="filingForm.fax" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="邮箱" prop="email"><el-input v-model="filingForm.email" /></el-form-item></el-col>
          </el-row>
          <el-space>
            <el-button type="primary" :loading="filingSubmitting" @click="submitFiling">提交备案</el-button>
            <el-tag v-if="enterpriseInfo" :type="statusTagType(enterpriseInfo.filing_status)">{{ enterpriseInfo.filing_status }}</el-tag>
            <span v-if="enterpriseInfo?.filing_audit_remark" style="color:#e6a23c">退回说明：{{ enterpriseInfo.filing_audit_remark }}</span>
          </el-space>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="月报填报" name="report">
        <el-form ref="reportFormRef" :model="reportForm" :rules="reportRules" label-width="130px">
          <el-row :gutter="16">
            <el-col :span="12"><el-form-item label="统计月份" prop="report_month"><el-date-picker v-model="reportForm.report_month" type="month" value-format="YYYY-MM" style="width:100%" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="建档期就业人数" prop="baseline_employees"><el-input-number v-model="reportForm.baseline_employees" :min="0" style="width:100%" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="调查期就业人数" prop="current_employees"><el-input-number v-model="reportForm.current_employees" :min="0" style="width:100%" /></el-form-item></el-col>
          </el-row>
          <template v-if="showReductionFields">
            <el-row :gutter="16">
              <el-col :span="12"><el-form-item label="减少类型" prop="reduction_type"><el-select v-model="reportForm.reduction_type" style="width:100%"><el-option v-for="item in reductionTypeOptions" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="主要原因" prop="primary_reason"><el-select v-model="reportForm.primary_reason" style="width:100%"><el-option v-for="item in reasonOptions" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="主要原因说明" prop="primary_reason_detail"><el-input v-model="reportForm.primary_reason_detail" type="textarea" :rows="3" /></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="次要原因"><el-select v-model="reportForm.secondary_reason" clearable style="width:100%"><el-option v-for="item in reasonOptions" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="次要原因说明"><el-input v-model="reportForm.secondary_reason_detail" type="textarea" :rows="3" /></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="第三原因"><el-select v-model="reportForm.third_reason" clearable style="width:100%"><el-option v-for="item in reasonOptions" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
            </el-row>
          </template>
          <el-button type="primary" :loading="reportSubmitting" @click="submitReport">提交月报</el-button>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="历史查询" name="history">
        <el-button type="primary" plain style="margin-bottom:12px" @click="loadReports">刷新历史数据</el-button>
        <el-table :data="reports" stripe>
          <el-table-column prop="report_month" label="统计月份" min-width="120" />
          <el-table-column prop="baseline_employees" label="建档期人数" min-width="120" />
          <el-table-column prop="current_employees" label="调查期人数" min-width="120" />
          <el-table-column prop="review_status" label="状态" min-width="180" />
          <el-table-column prop="return_remark" label="退回说明" min-width="220" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="通知浏览" name="notifications">
        <el-button type="primary" plain style="margin-bottom:12px" @click="loadNotifications">刷新通知</el-button>
        <el-table :data="notifications" stripe>
          <el-table-column prop="title" label="标题" min-width="180" />
          <el-table-column prop="published_at" label="发布时间" min-width="180" />
          <el-table-column prop="content" label="内容" min-width="320" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="修改密码" name="password">
        <el-form ref="passwordFormRef" :model="passwordForm" label-width="100px">
          <el-form-item label="旧密码"><el-input v-model="passwordForm.old_password" type="password" show-password /></el-form-item>
          <el-form-item label="新密码"><el-input v-model="passwordForm.new_password" type="password" show-password /></el-form-item>
          <el-button type="primary" @click="changePassword">修改密码</el-button>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </el-space>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import http from '../api/http'

const router = useRouter()
const activeTab = ref('filing')
const filingFormRef = ref<FormInstance>()
const reportFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const filingSubmitting = ref(false)
const reportSubmitting = ref(false)
const enterpriseInfo = ref<any>(null)
const reports = ref<any[]>([])
const notifications = ref<any[]>([])
const currentRegion = localStorage.getItem('user_region') ?? 'Kunming'

const filingForm = reactive({ region: currentRegion, organization_code: '', name: '', nature: '', industry: '', main_business: '', contact_person: '', phone: '', address: '', postal_code: '', fax: '', email: '' })
const reportForm = reactive({ report_month: '', baseline_employees: 0, current_employees: 0, reduction_type: '', primary_reason: '', primary_reason_detail: '', secondary_reason: '', secondary_reason_detail: '', third_reason: '' })
const passwordForm = reactive({ old_password: '', new_password: '' })

const reasonOptions = ['产业结构调整','重大技术改革','节能减排、淘汰落后产能','订单不足','原材料涨价','工资、社保等用工成本上升','经营资金困难','税收政策变化（包括税负增加或出口退税减少等）','季节性用工','其他','自行离职','工作调动、企业内部调剂','劳动关系转移、劳务派遣','退休','退职','死亡','自然减员','国际因素变化','招不上人来']
const reductionTypeOptions = ['关闭破产','停业整顿','经济性裁员','业务转移','自然减员','正常解除或终止劳动合同','国际因素变化影响','自然灾害','重大事件影响','其他']
const showReductionFields = computed(() => reportForm.current_employees < reportForm.baseline_employees)

const filingRules: FormRules = {
  organization_code: [{ required: true, message: '请输入组织机构代码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入企业名称', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }],
}
const reportRules: FormRules = {
  report_month: [{ required: true, message: '请选择统计月份', trigger: 'change' }],
  baseline_employees: [{ required: true, message: '请输入建档期人数', trigger: 'change' }],
  current_employees: [{ required: true, message: '请输入调查期人数', trigger: 'change' }],
  reduction_type: [{ validator: (_r, v, cb) => showReductionFields.value && !v ? cb(new Error('人数下降时必须填写减少类型')) : cb(), trigger: 'change' }],
  primary_reason: [{ validator: (_r, v, cb) => showReductionFields.value && !v ? cb(new Error('人数下降时必须填写主要原因')) : cb(), trigger: 'change' }],
  primary_reason_detail: [{ validator: (_r, v, cb) => showReductionFields.value && !v ? cb(new Error('人数下降时必须填写主要原因说明')) : cb(), trigger: 'blur' }],
}

const statusTagType = (status: string) => status === 'APPROVED' ? 'success' : status === 'REJECTED' ? 'danger' : 'warning'
const loadEnterprise = async () => { try { const { data } = await http.get('/api/enterprises/me'); enterpriseInfo.value = data; Object.assign(filingForm, data) } catch {} }
const loadReports = async () => { const { data } = await http.get('/api/employment-reports'); reports.value = data }
const loadNotifications = async () => { const { data } = await http.get('/api/notifications/browse'); notifications.value = data }
const submitFiling = async () => { if (!filingFormRef.value) return; const valid = await filingFormRef.value.validate().catch(() => false); if (!valid) return; filingSubmitting.value = true; try { const { data } = await http.post('/api/enterprises/filing/submit', filingForm); enterpriseInfo.value = data; ElMessage.success('备案提交成功') } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '备案提交失败') } finally { filingSubmitting.value = false } }
const submitReport = async () => { if (!reportFormRef.value) return; const valid = await reportFormRef.value.validate().catch(() => false); if (!valid) return; reportSubmitting.value = true; try { await http.post('/api/employment-reports/submit', { ...reportForm, reduction_type: reportForm.reduction_type || null, primary_reason: reportForm.primary_reason || null, primary_reason_detail: reportForm.primary_reason_detail || null, secondary_reason: reportForm.secondary_reason || null, secondary_reason_detail: reportForm.secondary_reason_detail || null, third_reason: reportForm.third_reason || null }); ElMessage.success('月报提交成功'); await loadReports() } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '月报提交失败') } finally { reportSubmitting.value = false } }
const changePassword = async () => { try { await http.post('/api/auth/change-password', passwordForm); ElMessage.success('密码修改成功'); passwordForm.old_password = ''; passwordForm.new_password = '' } catch (error: any) { ElMessage.error(error?.response?.data?.detail ?? '密码修改失败') } }
const logout = async () => { localStorage.clear(); await router.push({ name: 'login' }) }

onMounted(async () => { await Promise.all([loadEnterprise(), loadReports(), loadNotifications()]) })
</script>
