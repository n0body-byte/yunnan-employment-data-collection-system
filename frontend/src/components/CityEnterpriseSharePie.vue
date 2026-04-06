<template>
  <div ref="chartRef" style="width: 100%; height: 360px"></div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

interface PieItem {
  city: string
  enterprise_count: number
}

const props = defineProps<{
  items: PieItem[]
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

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
    chart = echarts.init(chartRef.value)
  }

  chart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}<br/>企业数: {c}<br/>占比: {d}%'
    },
    legend: {
      bottom: 0,
    },
    series: [
      {
        name: '各市企业数量占比',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: true,
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
