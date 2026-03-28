import axios from 'axios'

export function getApiErrorMessage(error: unknown, fallback = '操作失败'): string {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data as any

    if (responseData?.msg && typeof responseData.msg === 'string') {
      return responseData.msg
    }

    if (responseData?.message && typeof responseData.message === 'string') {
      return responseData.message
    }

    if (responseData?.error && typeof responseData.error === 'string') {
      return responseData.error
    }

    if (typeof responseData === 'string' && responseData.trim()) {
      return responseData.slice(0, 120)
    }

    if (error.request && !error.response) {
      return '请求未成功发送，请检查后端服务/CORS/网络'
    }

    if (error.message) {
      return error.message
    }
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return fallback
}
