<template>
  <div ref="chartRef" style="width: 100%; height: 360px"></div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

interface TrendItem {
  report_month: string
  total_job_changes: number
}

const props = defineProps<{
  items: TrendItem[]
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const months = computed(() => props.items.map((item) => item.report_month))
const values = computed(() => props.items.map((item) => item.total_job_changes))

const renderChart = async () => {
  await nextTick()
  if (!chartRef.value) return

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  chart.setOption({
    tooltip: {
      trigger: 'axis',
    },
    xAxis: {
      type: 'category',
      data: months.value,
    },
    yAxis: {
      type: 'value',
      name: '岗位变动数',
    },
    series: [
      {
        name: '岗位变动趋势',
        type: 'line',
        smooth: true,
        areaStyle: {},
        data: values.value,
      },
    ],
  })
}

const handleResize = () => chart?.resize()

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

watch([months, values], () => {
  renderChart()
}, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>
