<template>
  <div ref="chartRef" style="width: 100%; height: 360px"></div>
</template>

<script setup lang="ts">
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { init, use } from 'echarts/core'
import type { ECharts } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

interface TrendItem {
  report_month: string
  total_job_changes: number
}

const props = defineProps<{
  items: TrendItem[]
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: ECharts | null = null

use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const months = computed(() => props.items.map((item) => item.report_month))
const values = computed(() => props.items.map((item) => item.total_job_changes))

const renderChart = async () => {
  await nextTick()
  if (!chartRef.value) return

  if (!chart) {
    chart = init(chartRef.value)
  }

  chart.setOption({
    tooltip: {
      trigger: 'axis',
    },
    xAxis: {
      type: 'category',
      data: months.value,
      boundaryGap: false,
      axisLine: {
        lineStyle: {
          color: '#cbd5e1',
        },
      },
    },
    yAxis: {
      type: 'value',
      name: '岗位变动数',
      splitLine: {
        lineStyle: {
          color: '#e2e8f0',
          type: 'dashed',
        },
      },
    },
    series: [
      {
        name: '岗位变动趋势',
        type: 'line',
        smooth: true,
        symbolSize: 10,
        lineStyle: {
          width: 3,
          color: '#1f6feb',
        },
        itemStyle: {
          color: '#1f6feb',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(31, 111, 235, 0.28)' },
              { offset: 1, color: 'rgba(31, 111, 235, 0.02)' },
            ],
          },
        },
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
