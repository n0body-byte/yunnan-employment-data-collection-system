import { createRouter, createWebHistory } from 'vue-router'

import CityReviewView from '../views/CityReviewView.vue'
import EmploymentReportView from '../views/EmploymentReportView.vue'
import EnterpriseFilingView from '../views/EnterpriseFilingView.vue'
import LoginView from '../views/LoginView.vue'
import ProvinceDashboardView from '../views/ProvinceDashboardView.vue'
import ProvinceFilingAuditView from '../views/ProvinceFilingAuditView.vue'
import SystemMaintenanceView from '../views/SystemMaintenanceView.vue'

type UserRole = 'PROVINCE' | 'CITY' | 'ENTERPRISE'

const routes = [
  {
    path: '/',
    name: 'login',
    component: LoginView,
    meta: { public: true },
  },
  {
    path: '/enterprise/filing',
    name: 'enterprise-filing',
    component: EnterpriseFilingView,
    meta: { roles: ['ENTERPRISE'] },
  },
  {
    path: '/enterprise/report',
    name: 'enterprise-report',
    component: EmploymentReportView,
    meta: { roles: ['ENTERPRISE'] },
  },
  {
    path: '/city/review',
    name: 'city-review',
    component: CityReviewView,
    meta: { roles: ['CITY'] },
  },
  {
    path: '/province/dashboard',
    name: 'province-dashboard',
    component: ProvinceDashboardView,
    meta: { roles: ['PROVINCE'] },
  },
  {
    path: '/province/filing-audit',
    name: 'province-filing-audit',
    component: ProvinceFilingAuditView,
    meta: { roles: ['PROVINCE'] },
  },
  {
    path: '/system/maintenance',
    name: 'system-maintenance',
    component: SystemMaintenanceView,
    meta: { roles: ['PROVINCE'] },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  if (to.meta.public) {
    next()
    return
  }

  const token = localStorage.getItem('access_token')
  const role = localStorage.getItem('user_role') as UserRole | null
  if (!token || !role) {
    next({ name: 'login' })
    return
  }

  const roles = to.meta.roles as UserRole[] | undefined
  if (roles && !roles.includes(role)) {
    const fallbackMap: Record<UserRole, { name: string }> = {
      ENTERPRISE: { name: 'enterprise-filing' },
      CITY: { name: 'city-review' },
      PROVINCE: { name: 'province-dashboard' },
    }
    next(fallbackMap[role])
    return
  }

  next()
})

export default router
