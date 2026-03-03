import { getToken } from '@/utils/auth.js'

const BASE_URL = 'http://127.0.0.1:8000/api'

function getErrorMessage(payload, fallback = '请求失败') {
  if (!payload) return fallback
  if (typeof payload === 'string') return payload
  if (typeof payload.message === 'string') return payload.message
  if (typeof payload.detail === 'string') return payload.detail
  if (Array.isArray(payload.detail) && payload.detail.length > 0) {
    const first = payload.detail[0]
    if (typeof first === 'string') return first
    if (first && typeof first.msg === 'string') return first.msg
  }
  return fallback
}

export function request({ url, method = 'GET', data = {}, header = {}, showLoading = true }) {
  const token = getToken()
  const finalHeader = Object.assign({ 'Content-Type': 'application/json' }, header)
  if (token) {
    finalHeader.Authorization = `Bearer ${token}`
  }
  if (showLoading) {
    uni.showLoading({ title: '加载中...' })
  }
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: finalHeader,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          if (res.data && typeof res.data === 'object' && 'code' in res.data && res.data.code !== 200) {
            uni.showToast({ title: getErrorMessage(res.data, '请求失败'), icon: 'none' })
            reject(res.data)
            return
          }
          resolve(res.data)
        } else {
          uni.showToast({ title: getErrorMessage(res.data, '请求失败'), icon: 'none' })
          reject(res)
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络异常', icon: 'none' })
        reject(err)
      },
      complete: () => {
        if (showLoading) {
          uni.hideLoading()
        }
      }
    })
  })
}

export function uploadFile({ url, filePath, name = 'file', formData = {} }) {
  const token = getToken()
  const header = token ? { Authorization: `Bearer ${token}` } : {}
  uni.showLoading({ title: '上传中...' })
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: BASE_URL + url,
      filePath,
      name,
      formData,
      header,
      success: (res) => {
        let parsed = null
        try {
          parsed = JSON.parse(res.data)
        } catch (error) {
          uni.showToast({ title: '上传响应解析失败', icon: 'none' })
          reject(error)
          return
        }
        if (res.statusCode < 200 || res.statusCode >= 300) {
          uni.showToast({ title: getErrorMessage(parsed, '上传失败'), icon: 'none' })
          reject(parsed)
          return
        }
        if (parsed && typeof parsed === 'object' && 'code' in parsed && parsed.code !== 200) {
          uni.showToast({ title: getErrorMessage(parsed, '上传失败'), icon: 'none' })
          reject(parsed)
          return
        }
        resolve(parsed)
      },
      fail: (err) => {
        uni.showToast({ title: '上传失败', icon: 'none' })
        reject(err)
      },
      complete: () => uni.hideLoading()
    })
  })
}
