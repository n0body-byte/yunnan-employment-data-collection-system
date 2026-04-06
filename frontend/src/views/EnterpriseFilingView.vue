<template>
  <el-card shadow="never">
    <template #header>
      <div>
        <h2>企业信息备案</h2>
        <p>根据说明书 3.1.1 填写并提交企业备案信息</p>
      </div>
    </template>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" @submit.prevent>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="所属地区" prop="region">
            <el-input v-model="form.region" placeholder="请输入所属地区" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="组织机构代码" prop="organization_code">
            <el-input v-model="form.organization_code" maxlength="9" show-word-limit placeholder="9位字母数字" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="企业名称" prop="name">
            <el-input v-model="form.name" placeholder="请输入企业名称" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="企业性质" prop="nature">
            <el-select v-model="form.nature" placeholder="请选择企业性质" style="width: 100%">
              <el-option label="国有企业" value="国有企业" />
              <el-option label="民营企业" value="民营企业" />
              <el-option label="外商投资企业" value="外商投资企业" />
              <el-option label="股份制企业" value="股份制企业" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="所属行业" prop="industry_path">
            <el-cascader
              v-model="form.industry_path"
              :options="industryOptions"
              :props="{ emitPath: true, checkStrictly: false }"
              clearable
              placeholder="请选择所属行业"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="主要经营业务" prop="main_business">
            <el-input v-model="form.main_business" placeholder="请输入主要经营业务" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="联系人" prop="contact_person">
            <el-input v-model="form.contact_person" placeholder="请输入联系人" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="联系电话" prop="phone">
            <el-input v-model="form.phone" placeholder="请输入手机号" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="联系地址" prop="address">
            <el-input v-model="form.address" placeholder="请输入联系地址" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="邮政编码" prop="postal_code">
            <el-input v-model="form.postal_code" maxlength="6" placeholder="请输入邮政编码" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="传真" prop="fax">
            <el-input v-model="form.fax" placeholder="请输入传真号" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="请输入邮箱" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">提交备案</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import http from '../api/http'

interface CascaderOption {
  value: string
  label: string
  children?: CascaderOption[]
}

interface FilingForm {
  region: string
  organization_code: string
  name: string
  nature: string
  industry_path: string[]
  main_business: string
  contact_person: string
  phone: string
  address: string
  postal_code: string
  fax: string
  email: string
}

const formRef = ref<FormInstance>()
const submitting = ref(false)

const industryOptions: CascaderOption[] = [
  {
    value: '制造业',
    label: '制造业',
    children: [
      { value: '装备制造', label: '装备制造' },
      { value: '食品加工', label: '食品加工' },
    ],
  },
  {
    value: '服务业',
    label: '服务业',
    children: [
      { value: '信息服务', label: '信息服务' },
      { value: '现代物流', label: '现代物流' },
    ],
  },
  {
    value: '农业',
    label: '农业',
    children: [
      { value: '种植业', label: '种植业' },
      { value: '农产品加工', label: '农产品加工' },
    ],
  },
]

const createInitialForm = (): FilingForm => ({
  region: '',
  organization_code: '',
  name: '',
  nature: '',
  industry_path: [],
  main_business: '',
  contact_person: '',
  phone: '',
  address: '',
  postal_code: '',
  fax: '',
  email: '',
})

const form = reactive<FilingForm>(createInitialForm())

const validateOrganizationCode = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (!/^[A-Za-z0-9]{9}$/.test(value)) {
    callback(new Error('组织机构代码必须是9位字母或数字'))
    return
  }
  callback()
}

const validatePhone = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (!/^1[3-9]\d{9}$/.test(value)) {
    callback(new Error('请输入正确的手机号'))
    return
  }
  callback()
}

const rules: FormRules<FilingForm> = {
  region: [{ required: true, message: '请输入所属地区', trigger: 'blur' }],
  organization_code: [
    { required: true, message: '请输入组织机构代码', trigger: 'blur' },
    { validator: validateOrganizationCode, trigger: 'blur' },
  ],
  name: [{ required: true, message: '请输入企业名称', trigger: 'blur' }],
  nature: [{ required: true, message: '请选择企业性质', trigger: 'change' }],
  industry_path: [{ required: true, message: '请选择所属行业', trigger: 'change' }],
  main_business: [{ required: true, message: '请输入主要经营业务', trigger: 'blur' }],
  contact_person: [{ required: true, message: '请输入联系人', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { validator: validatePhone, trigger: 'blur' },
  ],
  address: [{ required: true, message: '请输入联系地址', trigger: 'blur' }],
  postal_code: [{ required: true, message: '请输入邮政编码', trigger: 'blur' }],
}

const handleSubmit = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = {
      region: form.region,
      organization_code: form.organization_code,
      name: form.name,
      nature: form.nature,
      industry: form.industry_path.join('/'),
      main_business: form.main_business,
      contact_person: form.contact_person,
      phone: form.phone,
      address: form.address,
      postal_code: form.postal_code,
      fax: form.fax || null,
      email: form.email || null,
      filing_status: 'PENDING',
    }

    await http.post('/api/enterprises/filing/submit', payload)
    ElMessage.success('备案信息提交成功')
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? '备案提交失败'
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
