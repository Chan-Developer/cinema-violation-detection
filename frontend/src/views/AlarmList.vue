<template>
  <div class="alarm-page">
    <!-- 筛选区 -->
    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="影院">
          <el-select v-model="filters.cinema_id" placeholder="全部影院" clearable @change="loadAlarms" style="width: 160px">
            <el-option v-for="c in cinemas" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.type" placeholder="全部类型" clearable @change="loadAlarms" style="width: 140px">
            <el-option v-for="t in alarmTypes" :key="t.code" :label="t.name" :value="t.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="filters.level" placeholder="全部级别" clearable @change="loadAlarms" style="width: 120px">
            <el-option v-for="l in alarmLevels" :key="l.code" :label="l.name" :value="l.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable @change="loadAlarms" style="width: 120px">
            <el-option label="待处理" :value="0" />
            <el-option label="已确认" :value="1" />
            <el-option label="处理中" :value="2" />
            <el-option label="已处理" :value="3" />
            <el-option label="已忽略" :value="4" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadAlarms">
            <el-icon><Search /></el-icon> 查询
          </el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 报警列表 -->
    <el-card>
      <el-table :data="alarms" stripe v-loading="loading" style="width: 100%" :default-sort="{ prop: 'id', order: 'descending' }">
        <el-table-column prop="id" label="ID" width="50" align="center" />
        <el-table-column prop="alarm_type" label="类型" min-width="85">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.alarm_type_code)" size="small" effect="light" round>
              {{ row.alarm_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="150" show-overflow-tooltip />
        <el-table-column prop="camera_name" label="摄像头" min-width="100" show-overflow-tooltip />
        <el-table-column prop="location" label="位置" min-width="100" show-overflow-tooltip />
        <el-table-column prop="level_name" label="级别" width="80" align="center">
          <template #default="{ row }">
            <el-tag :color="row.level_color" effect="dark" size="small" round>
              {{ row.level_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="confidence" label="置信度" width="85" align="center">
          <template #default="{ row }">
            {{ row.confidence ? (row.confidence * 100).toFixed(1) + '%' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="occurred_at" label="发生时间" min-width="145" show-overflow-tooltip />
        <el-table-column prop="status_text" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)" size="small" round>
              {{ row.status_text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right" align="center">
          <template #default="{ row }">
            <el-dropdown trigger="click">
              <el-button type="primary" link size="small">
                操作 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="viewDetail(row)">详情</el-dropdown-item>
                  <el-dropdown-item v-if="row.status === 0" @click="handleAlarm(row, 'confirm')">确认</el-dropdown-item>
                  <el-dropdown-item v-if="row.status === 1" @click="handleAlarm(row, 'process')">处理中</el-dropdown-item>
                  <el-dropdown-item v-if="row.status === 1 || row.status === 2" @click="handleAlarm(row, 'resolve')">处理完成</el-dropdown-item>
                  <el-dropdown-item v-if="row.status <= 2" @click="handleAlarm(row, 'ignore')">忽略</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.per_page"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadAlarms"
          @current-change="loadAlarms"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="报警详情" width="640px" top="6vh">
      <div v-if="currentAlarm" class="alarm-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="类型">
            <el-tag :type="getTypeTag(currentAlarm.alarm_type_code)" round>{{ currentAlarm.alarm_type }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="级别">
            <el-tag :color="currentAlarm.level_color" effect="dark" round>{{ currentAlarm.level_name }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="摄像头">{{ currentAlarm.camera_name }}</el-descriptions-item>
          <el-descriptions-item label="位置">{{ currentAlarm.location }}</el-descriptions-item>
          <el-descriptions-item label="置信度">
            {{ currentAlarm.confidence ? (currentAlarm.confidence * 100).toFixed(1) + '%' : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTag(currentAlarm.status)" round>{{ currentAlarm.status_text }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="发生时间" :span="2">{{ currentAlarm.occurred_at }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ currentAlarm.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="处理人" v-if="currentAlarm.handler_name">{{ currentAlarm.handler_name }}</el-descriptions-item>
          <el-descriptions-item label="处理备注" v-if="currentAlarm.handler_note">{{ currentAlarm.handler_note }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="currentAlarm.image_url" class="detail-image">
          <h4>报警截图</h4>
          <el-image
            :src="currentAlarm.image_url"
            :zoom-rate="1.2"
            :preview-src-list="[currentAlarm.image_url]"
            fit="contain"
            style="max-width: 100%; max-height: 300px; border-radius: 8px;"
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, ArrowDown } from '@element-plus/icons-vue'

const authStore = useAuthStore()

const loading = ref(false)
const alarms = ref<any[]>([])
const cinemas = ref<any[]>([])
const alarmTypes = ref<any[]>([])
const alarmLevels = ref<any[]>([])

const filters = reactive({
  cinema_id: null as number | null,
  type: '',
  level: '',
  status: null as number | null
})
const pagination = reactive({ page: 1, per_page: 20, total: 0 })

const detailVisible = ref(false)
const currentAlarm = ref<any>(null)

const loadCinemas = async () => {
  try {
    const res = await authStore.api.get('/cinemas?per_page=100')
    if (res.data.success) cinemas.value = res.data.cinemas
  } catch (e) { console.error('获取影院失败', e) }
}

const loadAlarmTypes = async () => {
  try {
    const res = await authStore.api.get('/alarms/types')
    if (res.data.success) alarmTypes.value = res.data.types
  } catch (e) { console.error('获取报警类型失败', e) }
}

const loadAlarmLevels = async () => {
  try {
    const res = await authStore.api.get('/alarms/levels')
    if (res.data.success) alarmLevels.value = res.data.levels
  } catch (e) { console.error('获取报警级别失败', e) }
}

const loadAlarms = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', String(pagination.page))
    params.append('per_page', String(pagination.per_page))
    if (filters.cinema_id) params.append('cinema_id', String(filters.cinema_id))
    if (filters.type) params.append('type', filters.type)
    if (filters.level) params.append('level', filters.level)
    if (filters.status !== null && filters.status !== ('' as any)) params.append('status', String(filters.status))

    const res = await authStore.api.get(`/alarms?${params}`)
    if (res.data.success) {
      alarms.value = res.data.alarms
      pagination.total = res.data.total
    }
  } catch (e) { console.error('获取报警列表失败', e) }
  finally { loading.value = false }
}

const resetFilters = () => {
  filters.cinema_id = null
  filters.type = ''
  filters.level = ''
  filters.status = null
  pagination.page = 1
  loadAlarms()
}

const viewDetail = (alarm: any) => {
  currentAlarm.value = alarm
  detailVisible.value = true
}

const handleAlarm = async (alarm: any, action: string) => {
  try {
    if (action === 'confirm') {
      await ElMessageBox.confirm('确认此报警?', '提示', { type: 'info' })
      await authStore.api.post(`/alarms/${alarm.id}/confirm`)
      ElMessage.success('已确认')
    } else if (action === 'process') {
      const { value } = await ElMessageBox.prompt('请输入处理备注', '处理报警', {
        confirmButtonText: '确定', cancelButtonText: '取消'
      })
      await authStore.api.post(`/alarms/${alarm.id}/process`, { note: value })
      ElMessage.success('已进入处理中')
    } else if (action === 'resolve') {
      const { value } = await ElMessageBox.prompt('请输入处理备注', '处理报警', {
        confirmButtonText: '确定', cancelButtonText: '取消'
      })
      await authStore.api.post(`/alarms/${alarm.id}/resolve`, { note: value })
      ElMessage.success('已处理')
    } else if (action === 'ignore') {
      await ElMessageBox.confirm('忽略此报警?', '提示', { type: 'warning' })
      await authStore.api.post(`/alarms/${alarm.id}/ignore`)
      ElMessage.success('已忽略')
    }
    loadAlarms()
    authStore.fetchPendingAlarms()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.message || '操作失败')
  }
}

const getTypeTag = (code: string) =>
  ({ photo: 'danger', smoke: 'warning', crowd: 'success', walk: 'info' } as Record<string, string>)[code] || 'info'

const getStatusTag = (status: number) =>
  ({ 0: 'danger', 1: 'warning', 2: '', 3: 'success', 4: 'info' } as Record<number, string>)[status] || 'info'

onMounted(() => {
  loadCinemas()
  loadAlarmTypes()
  loadAlarmLevels()
  loadAlarms()
})
</script>

<style scoped>
.alarm-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-card :deep(.el-card__body) {
  padding: 16px 20px 4px;
}

.table-footer {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.alarm-detail {
  padding: 4px;
}

.detail-image {
  margin-top: 20px;
}
.detail-image h4 {
  margin-bottom: 10px;
  font-size: 14px;
  color: #666;
}
</style>
