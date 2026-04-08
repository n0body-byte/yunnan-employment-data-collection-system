<template>
  <div class="dashboard-shell">
    <aside class="dashboard-sidebar" :class="{ 'is-open': sidebarOpen }">
      <div class="dashboard-brand">
        <div class="dashboard-brand__mark">云</div>
        <div class="dashboard-brand__copy">
          <strong>数据采集系统</strong>
          <span>Yunnan Employment</span>
        </div>
      </div>

      <nav class="dashboard-nav">
        <button
          v-for="item in navItems"
          :key="item.key"
          type="button"
          class="dashboard-nav__item"
          :class="{ 'is-active': item.key === activeKey }"
          @click="handleNavigate(item.key)"
        >
          <span class="dashboard-nav__dot" />
          <span class="dashboard-nav__label">{{ item.label }}</span>
          <span v-if="item.badge !== undefined" class="dashboard-nav__badge">{{ item.badge }}</span>
        </button>
      </nav>

      <div class="dashboard-sidebar__footer">
        <button type="button" class="dashboard-secondary-button" @click="$emit('logout')">
          退出登录
        </button>
      </div>
    </aside>

    <div v-if="sidebarOpen" class="dashboard-overlay" @click="sidebarOpen = false" />

    <div class="dashboard-main">
      <header class="dashboard-header">
        <div class="dashboard-header__title">
          <button type="button" class="dashboard-menu-toggle" @click="sidebarOpen = !sidebarOpen">
            菜单
          </button>
          <div>
            <h1>{{ title }}</h1>
            <p>{{ subtitle }}</p>
          </div>
        </div>

        <div class="dashboard-header__actions">
          <div class="dashboard-role-switch">
            <span
              v-for="item in roleItems"
              :key="item.key"
              class="dashboard-role-switch__item"
              :class="{ 'is-active': item.active }"
            >
              {{ item.label }}
            </span>
          </div>

          <slot name="header-actions" />

          <div class="dashboard-user-pill">
            <strong>{{ userName }}</strong>
            <span>{{ userRole }}</span>
          </div>
        </div>
      </header>

      <main class="dashboard-content">
        <section v-if="$slots.stats" class="dashboard-stats-grid">
          <slot name="stats" />
        </section>

        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface NavItem {
  key: string
  label: string
  badge?: string | number
}

interface RoleItem {
  key: string
  label: string
  active: boolean
}

const props = defineProps<{
  title: string
  subtitle: string
  navItems: NavItem[]
  activeKey: string
  userName: string
  userRole: string
  currentRole: 'ENTERPRISE' | 'CITY' | 'PROVINCE'
}>()

const emit = defineEmits<{
  (event: 'update:activeKey', value: string): void
  (event: 'logout'): void
}>()

const sidebarOpen = ref(false)

const roleItems = computed<RoleItem[]>(() => [
  { key: 'ENTERPRISE', label: '企业', active: props.currentRole === 'ENTERPRISE' },
  { key: 'CITY', label: '市级', active: props.currentRole === 'CITY' },
  { key: 'PROVINCE', label: '省级', active: props.currentRole === 'PROVINCE' },
])

const handleNavigate = (key: string) => {
  emit('update:activeKey', key)
  sidebarOpen.value = false
}
</script>
