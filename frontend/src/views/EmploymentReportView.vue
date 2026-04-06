<template>
  <el-card shadow="never">
    <template #header>
      <div>
        <h2>月度数据填报</h2>
        <p>当调查期人数少于建档期人数时，系统自动要求填写减少原因</p>
      </div>
    </template>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" @submit.prevent>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="统计月份" prop="report_month">
            <el-date-picker
              v-model="form.report_month"
              type="month"
              value-format="YYYY-MM"
              placeholder="请选择统计月份"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="建档期人数" prop="baseline_employees">
            <el-input-number v-model="form.baseline_employees" :min="0" :step="1" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="调查期人数" prop="current_employees">
            <el-input-number v-model="form.current_employees" :min="0" :step="1" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>

      <template v-if="showReductionFields">
        <el-divider content-position="left">减少原因</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="减少类型" prop="reduction_type">
              <el-select v-model="form.reduction_type" placeholder="请选择减少类型" style="width: 100%">
                <el-option v-for="item in reductionTypeOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="主要原因" prop="primary_reason">
              <el-select v-model="form.primary_reason" placeholder="请选择主要原因" style="width: 100%">
                <el-option v-for="item in reductionReasonOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="主要原因说明" prop="primary_reason_detail">
              <el-input
                v-model="form.primary_reason_detail"
                type="textarea"
                :rows="3"
                placeholder="请填写主要原因说明"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="次要原因" prop="secondary_reason">
              <el-select v-model="form.secondary_reason" placeholder="可选" clearable style="width: 100%">
                <el-option v-for="item in reductionReasonOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="次要原因说明" prop="secondary_reason_detail">
          <el-input
            v-model="form.secondary_reason_detail"
            type="textarea"
            :rows="3"
            placeholder="如有需要请填写次要原因说明"
          />
        </el-form-item>
      </template>

      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">提交月报</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import http from '../api/http'

interface ReportForm {
  report_month: string
  baseline_employees: number
  current_employees: number
  reduction_type: string
  primary_reason: string
  primary_reason_detail: string
  secondary_reason: string
  secondary_reason_detail: string
}

const formRef = ref<FormInstance>()
const submitting = ref(false)

const reductionTypeOptions = [
  '关闭破产',
  '停业整顿',
  '经济性裁员',
  '业务转移',
  '自然减员',
  '正常解除或终止劳动合同',
  '国际因素变化影响',
  '自然灾害',
  '重大事件影响',
  '其他',
]

const reductionReasonOptions = [
  '产业结构调整',
  '重大技术改革',
  '节能减排、淘汰落后产能',
  '订单不足',
  '原材料涨价',
  '工资、社保等用工成本上升',
  '自然减员',
  '经营资金困难',
  '税收政策变化（包括税负增加或出口退税减少等）',
  '季节性用工',
  '其他',
  '自行离职',
  '工作调动、企业内部调剂',
  '劳动关系转移、劳务派遣',
]

const createInitialForm = (): ReportForm => ({
  report_month: '',
  baseline_employees: 0,
  current_employees: 0,
  reduction_type: '',
  primary_reason: '',
  primary_reason_detail: '',
  secondary_reason: '',
  secondary_reason_detail: '',
})

const form = reactive<ReportForm>(createInitialForm())

const showReductionFields = computed(() => form.current_employees < form.baseline_employees)

watch(showReductionFields, (visible) => {
  if (!visible) {
    form.reduction_type = ''
    form.primary_reason = ''
    form.primary_reason_detail = ''
    form.secondary_reason = ''
    form.secondary_reason_detail = ''
    formRef.value?.clearValidate([
      'reduction_type',
      'primary_reason',
      'primary_reason_detail',
      'secondary_reason',
      'secondary_reason_detail',
    ])
  }
})

const validateReductionField = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (showReductionFields.value && !value) {
    callback(new Error('调查期人数小于建档期人数时，此项必填'))
    return
  }
  callback()
}

const rules: FormRules<ReportForm> = {
  report_month: [{ required: true, message: '请选择统计月份', trigger: 'change' }],
  baseline_employees: [{ required: true, message: '请输入建档期人数', trigger: 'change' }],
  current_employees: [{ required: true, message: '请输入调查期人数', trigger: 'change' }],
  reduction_type: [{ validator: validateReductionField, trigger: 'change' }],
  primary_reason: [{ validator: validateReductionField, trigger: 'change' }],
  primary_reason_detail: [{ validator: validateReductionField, trigger: 'blur' }],
}

const handleSubmit = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await http.post('/api/employment-reports/submit', {
      report_month: form.report_month,
      baseline_employees: form.baseline_employees,
      current_employees: form.current_employees,
      reduction_type: form.reduction_type || null,
      primary_reason: form.primary_reason || null,
      primary_reason_detail: form.primary_reason_detail || null,
      secondary_reason: form.secondary_reason || null,
      secondary_reason_detail: form.secondary_reason_detail || null,
    })
    ElMessage.success('月度数据提交成功')
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? '月度数据提交失败'
    ElMessage.error(message)
  } finally {
    submitting.value = false
  }
}

const handleReset = () => {
  Object.assign(form, createInitialForm())
  formRef.value?.clearValidate()
}
</script>
