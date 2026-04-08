<template>
  <div ref="chartRef" style="width: 100%; height: 360px"></div>
</template>

<script setup lang="ts">
import { PieChart } from 'echarts/charts'
import { LegendComponent, TooltipComponent } from 'echarts/components'
import { init, use } from 'echarts/core'
import type { ECharts } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

interface PieItem {
  city: string
  enterprise_count: number
}

const props = defineProps<{
  items: PieItem[]
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: ECharts | null = null

use([PieChart, TooltipComponent, LegendComponent, CanvasRenderer])

const chartData = computed(() =>
  props.items.map((item) => ({
    name: item.city,
    value: item.enterprise_count,
  })),
)

const renderChart = async () => {
  await nextTick()
  if (!chartRef.value) return

  if (!chart) {
    chart = init(chartRef.value)
  }

  chart.setOption({
    color: ['#1f6feb', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#0ea5e9'],
    tooltip: {
      trigger: 'item',
      formatter: '{b}<br/>企业数: {c}<br/>占比: {d}%',
    },
    legend: {
      bottom: 0,
      icon: 'circle',
    },
    series: [
      {
        name: '各市企业数量占比',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderColor: '#ffffff',
          borderWidth: 6,
          borderRadius: 14,
        },
        data: chartData.value,
      },
    ],
  })
}

const handleResize = () => chart?.resize()

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

watch(chartData, () => {
  renderChart()
}, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>
