export const ROLE_ADMIN = 'admin'
export const ROLE_MANAGER = 'manager'
export const ROLE_OPERATOR = 'operator'
export const ROLE_MAINTENANCE = 'maintenance'

export const SYSTEM_ROLES = [
  ROLE_ADMIN,
  ROLE_MANAGER,
  ROLE_OPERATOR,
  ROLE_MAINTENANCE
] as const

export type SystemRole = typeof SYSTEM_ROLES[number]

export const ROLE_LABEL_MAP: Record<string, string> = {
  [ROLE_ADMIN]: '管理员',
  [ROLE_MANAGER]: '影院经理',
  [ROLE_OPERATOR]: '监控员',
  [ROLE_MAINTENANCE]: '运维'
}

export const ROLE_TAG_MAP: Record<string, string> = {
  [ROLE_ADMIN]: 'danger',
  [ROLE_MANAGER]: 'success',
  [ROLE_OPERATOR]: 'warning',
  [ROLE_MAINTENANCE]: 'info'
}

export const ROLE_SCOPE_MAP: Record<string, string> = {
  [ROLE_ADMIN]: '全局',
  [ROLE_MANAGER]: '所属影院',
  [ROLE_OPERATOR]: '全局告警',
  [ROLE_MAINTENANCE]: '全局运维'
}

export const ROLE_CAPABILITIES_MAP: Record<string, string[]> = {
  [ROLE_ADMIN]: ['用户/角色管理', '影院与影厅管理', '摄像头管理', '告警处置'],
  [ROLE_MANAGER]: ['所属影院配置', '所属影院摄像头管理', '所属影院告警处置'],
  [ROLE_OPERATOR]: ['告警查看', '告警确认/处理/忽略'],
  [ROLE_MAINTENANCE]: ['摄像头状态维护', '视频流启停', '设备运行排障']
}

export const roleLabel = (role?: string) => ROLE_LABEL_MAP[role || ''] || (role || '')
export const roleTag = (role?: string) => ROLE_TAG_MAP[role || ''] || 'info'
