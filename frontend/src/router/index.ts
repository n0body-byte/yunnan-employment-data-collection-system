import { createRouter, createWebHistory } from 'vue-router'

import CityWorkspaceView from '../views/CityWorkspaceView.vue'
import EnterpriseWorkspaceView from '../views/EnterpriseWorkspaceView.vue'
import LoginView from '../views/LoginView.vue'
import ProvinceDashboardView from '../views/ProvinceDashboardView.vue'
import ProvinceManagementView from '../views/ProvinceManagementView.vue'

type UserRole = 'PROVINCE' | 'CITY' | 'ENTERPRISE'

const routes = [
  {
    path: '/',
    name: 'login',
    component: LoginView,
    meta: { public: true },
  },
  {
    path: '/enterprise',
    name: 'enterprise-workspace',
    component: EnterpriseWorkspaceView,
    meta: { roles: ['ENTERPRISE'] },
  },
  {
    path: '/city',
    name: 'city-workspace',
    component: CityWorkspaceView,
    meta: { roles: ['CITY'] },
  },
  {
    path: '/province/dashboard',
    name: 'province-dashboard',
    component: ProvinceDashboardView,
    meta: { roles: ['PROVINCE'] },
  },
  {
    path: '/province/management',
    name: 'province-management',
    component: ProvinceManagementView,
    meta: { roles: ['PROVINCE'] },
  },
  { path: '/enterprise/filing', redirect: { name: 'enterprise-workspace' } },
  { path: '/enterprise/report', redirect: { name: 'enterprise-workspace' } },
  { path: '/city/review', redirect: { name: 'city-workspace' } },
  { path: '/province/filing-audit', redirect: { name: 'province-management' } },
  { path: '/system/maintenance', redirect: { name: 'province-management' } },
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
      ENTERPRISE: { name: 'enterprise-workspace' },
      CITY: { name: 'city-workspace' },
      PROVINCE: { name: 'province-dashboard' },
    }
    next(fallbackMap[role])
    return
  }

  next()
})

export default router
