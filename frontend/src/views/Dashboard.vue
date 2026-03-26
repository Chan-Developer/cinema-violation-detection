<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card" v-for="item in statCards" :key="item.key">
        <div class="stat-icon" :style="{ background: item.gradient }">
          <el-icon :size="26"><component :is="item.icon" /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ item.value }}</div>
          <div class="stat-label">{{ item.label }}</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-row">
      <el-card class="chart-card">
        <template #header>
          <div class="card-head">
            <span class="card-title">报警趋势</span>
            <span class="card-sub">最近7天</span>
          </div>
        </template>
        <div ref="trendChartEl" class="chart-container"></div>
      </el-card>

      <el-card class="chart-card">
        <template #header>
          <div class="card-head">
            <span class="card-title">报警类型分布</span>
            <span class="card-sub">全部数据</span>
          </div>
        </template>
        <div ref="typeChartEl" class="chart-container"></div>
      </el-card>
    </div>

    <!-- 最近报警 -->
    <el-card class="recent-card">
      <template #header>
        <div class="card-head">
          <span class="card-title">最近报警</span>
          <el-button type="primary" text @click="$router.push('/alarms')">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table :data="recentAlarms" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="alarm_type" label="类型" width="110">
          <template #default="{ row }">
            <el-tag :type="alarmTypeTag(row.alarm_type_code)" size="small" effect="light" round>
              {{ row.alarm_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="camera_name" label="摄像头" min-width="120" />
        <el-table-column prop="location" label="位置" min-width="160" show-overflow-tooltip />
        <el-table-column prop="level_name" label="级别" width="80">
          <template #default="{ row }">
            <el-tag :color="row.level_color" effect="dark" size="small" round>
              {{ row.level_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="occurred_at" label="时间" width="180" />
        <el-table-column prop="status_text" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small" round>{{ row.status_text }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useAuthStore } from '../stores/auth'
import * as echarts from 'echarts'

const authStore = useAuthStore()

const stats = ref({
  cinemas: 0,
  cameras: { total: 0, online: 0, offline: 0 },
  alarms: { today: 0, pending: 0 }
})
const recentAlarms = ref<any[]>([])
const trendChartEl = ref<HTMLElement>()
const typeChartEl = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null
let typeChart: echarts.ECharts | null = null

const statCards = computed(() => [
  {
    key: 'cinemas', icon: 'OfficeBuilding',
    label: '影院数量', value: stats.value.cinemas,
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  },
  {
    key: 'cameras', icon: 'VideoCamera',
    label: '在线摄像头', value: `${stats.value.cameras.online}/${stats.value.cameras.total}`,
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
  },
  {
    key: 'today', icon: 'Bell',
    label: '今日报警', value: stats.value.alarms.today,
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
  },
  {
    key: 'pending', icon: 'Warning',
    label: '待处理', value: stats.value.alarms.pending,
    gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
  },
])

const alarmTypeTag = (code: string) =>
  ({ photo: 'danger', smoke: 'warning', crowd: 'success', walk: 'info' } as Record<string, string>)[code] || 'info'

const statusTag = (status: number) =>
  ({ 0: 'danger', 1: 'warning', 2: '', 3: 'success', 4: 'info' } as Record<number, string>)[status] || 'info'

const initCharts = () => {
  if (trendChartEl.value) {
    trendChart = echarts.init(trendChartEl.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,255,255,0.96)', borderColor: '#eee', textStyle: { color: '#333' } },
      grid: { left: 40, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: [], axisLine: { lineStyle: { color: '#e8e8e8' } }, axisLabel: { color: '#999' } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f0f0' } }, axisLabel: { color: '#999' } },
      series: [{
        data: [], type: 'line', smooth: true,
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(102,126,234,0.3)' },
          { offset: 1, color: 'rgba(102,126,234,0.02)' }
        ])},
        lineStyle: { color: '#667eea', width: 2.5 },
        itemStyle: { color: '#667eea' },
        symbol: 'circle', symbolSize: 6
      }]
    })
  }

  if (typeChartEl.value) {
    typeChart = echarts.init(typeChartEl.value)
    typeChart.setOption({
      tooltip: { trigger: 'item', backgroundColor: 'rgba(255,255,255,0.96)', borderColor: '#eee', textStyle: { color: '#333' } },
      legend: { bottom: 0, textStyle: { color: '#666' } },
      color: ['#f5576c', '#ffa502', '#2ed573', '#667eea'],
      series: [{
        type: 'pie', radius: ['45%', '72%'], data: [],
        label: { show: false },
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.1)' } }
      }]
    })
  }
}

const fetchData = async () => {
  try {
    const [overviewRes, alarmsRes] = await Promise.all([
      authStore.api.get('/dashboard/overview'),
      authStore.api.get('/dashboard/alarms/recent?limit=5')
    ])

    if (overviewRes.data.success) {
      stats.value = overviewRes.data.data
      const d = overviewRes.data.data
      if (trendChart && d.alarm_trend) {
        trendChart.setOption({
          xAxis: { data: d.alarm_trend.map((t: any) => t.date) },
          series: [{ data: d.alarm_trend.map((t: any) => t.count) }]
        })
      }
      if (typeChart && d.alarm_types) {
        typeChart.setOption({
          series: [{ data: d.alarm_types.map((t: any) => ({ value: t.count, name: t.name })) }]
        })
      }
    }

    if (alarmsRes.data.success) {
      recentAlarms.value = alarmsRes.data.alarms
    }
  } catch (e) {
    console.error('获取仪表盘数据失败', e)
  }
}

const handleResize = () => {
  trendChart?.resize()
  typeChart?.resize()
}

onMounted(async () => {
  initCharts()
  await fetchData()
  authStore.fetchPendingAlarms()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  typeChart?.dispose()
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 14px;
  padding: 22px 20px;
  display: flex;
  align-items: center;
  gap: 18px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s, box-shadow 0.2s;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  width: 56px;
  height: 56px;
  min-width: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: #999;
  margin-top: 2px;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-container {
  height: 300px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}
.card-sub {
  font-size: 12px;
  color: #bbb;
}
</style>
