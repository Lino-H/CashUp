import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

// 扩展dayjs插件
dayjs.extend(relativeTime)
import { message } from 'antd'

// 数字格式化
export const formatNumber = {
  // 格式化货币
  currency: (value: number, currency = 'USD', decimals = 2): string => {
    if (isNaN(value)) return '--'
    
    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    })
    
    return formatter.format(value)
  },
  
  // 格式化百分比
  percentage: (value: number, decimals = 2): string => {
    if (isNaN(value)) return '--'
    return `${(value * 100).toFixed(decimals)}%`
  },
  
  // 格式化大数字（K, M, B）
  compact: (value: number, decimals = 1): string => {
    if (isNaN(value)) return '--'
    
    const formatter = new Intl.NumberFormat('en-US', {
      notation: 'compact',
      maximumFractionDigits: decimals
    })
    
    return formatter.format(value)
  },
  
  // 格式化普通数字
  decimal: (value: number, decimals = 2): string => {
    if (isNaN(value)) return '--'
    return value.toFixed(decimals)
  },
  
  // 格式化带千分位分隔符的数字
  withCommas: (value: number, decimals = 2): string => {
    if (isNaN(value)) return '--'
    return value.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    })
  }
}

// 日期时间格式化
export const formatDate = {
  // 标准日期时间格式
  datetime: (date: string | Date, format = 'YYYY-MM-DD HH:mm:ss'): string => {
    if (!date) return '--'
    return dayjs(date).format(format)
  },
  
  // 日期格式
  date: (date: string | Date): string => {
    if (!date) return '--'
    return dayjs(date).format('YYYY-MM-DD')
  },
  
  // 时间格式
  time: (date: string | Date): string => {
    if (!date) return '--'
    return dayjs(date).format('HH:mm:ss')
  },
  
  // 相对时间（多久前）
  relative: (date: string | Date): string => {
    if (!date) return '--'
    return dayjs(date).fromNow()
  },
  
  // 友好的日期时间格式
  friendly: (date: string | Date): string => {
    if (!date) return '--'
    
    const now = dayjs()
    const target = dayjs(date)
    const diffDays = now.diff(target, 'day')
    
    if (diffDays === 0) {
      return `今天 ${target.format('HH:mm')}`
    } else if (diffDays === 1) {
      return `昨天 ${target.format('HH:mm')}`
    } else if (diffDays < 7) {
      return `${diffDays}天前`
    } else {
      return target.format('MM-DD HH:mm')
    }
  }
}

// 颜色工具
export const colorUtils = {
  // 根据盈亏获取颜色
  getPnlColor: (value: number): string => {
    if (value > 0) return '#52c41a' // 绿色
    if (value < 0) return '#ff4d4f' // 红色
    return '#8c8c8c' // 灰色
  },
  
  // 根据变化获取颜色
  getChangeColor: (value: number): string => {
    if (value > 0) return '#52c41a'
    if (value < 0) return '#ff4d4f'
    return '#8c8c8c'
  },
  
  // 根据风险等级获取颜色
  getRiskColor: (level: string): string => {
    const colors = {
      low: '#52c41a',
      medium: '#faad14',
      high: '#ff4d4f',
      critical: '#a8071a'
    }
    return colors[level as keyof typeof colors] || '#8c8c8c'
  },
  
  // 根据状态获取颜色
  getStatusColor: (status: string): string => {
    const colors = {
      active: '#52c41a',
      inactive: '#8c8c8c',
      pending: '#faad14',
      error: '#ff4d4f',
      success: '#52c41a',
      warning: '#faad14',
      danger: '#ff4d4f'
    }
    return colors[status as keyof typeof colors] || '#8c8c8c'
  }
}

// 验证工具
export const validators = {
  // 邮箱验证
  email: (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  },
  
  // 手机号验证（中国）
  phone: (phone: string): boolean => {
    const phoneRegex = /^1[3-9]\d{9}$/
    return phoneRegex.test(phone)
  },
  
  // 密码强度验证
  password: (password: string): { valid: boolean; strength: string; message: string } => {
    if (password.length < 8) {
      return { valid: false, strength: 'weak', message: '密码长度至少8位' }
    }
    
    let score = 0
    const checks = [
      /[a-z]/.test(password), // 小写字母
      /[A-Z]/.test(password), // 大写字母
      /\d/.test(password),    // 数字
      /[^\w\s]/.test(password) // 特殊字符
    ]
    
    score = checks.filter(Boolean).length
    
    if (score < 2) {
      return { valid: false, strength: 'weak', message: '密码强度太弱' }
    } else if (score < 3) {
      return { valid: true, strength: 'medium', message: '密码强度中等' }
    } else {
      return { valid: true, strength: 'strong', message: '密码强度很强' }
    }
  },
  
  // 数字验证
  number: (value: any): boolean => {
    return !isNaN(parseFloat(value)) && isFinite(value)
  },
  
  // 正数验证
  positiveNumber: (value: any): boolean => {
    return validators.number(value) && parseFloat(value) > 0
  }
}

// 字符串工具
export const stringUtils = {
  // 截断字符串
  truncate: (str: string, length: number, suffix = '...'): string => {
    if (!str || str.length <= length) return str
    return str.substring(0, length) + suffix
  },
  
  // 首字母大写
  capitalize: (str: string): string => {
    if (!str) return str
    return str.charAt(0).toUpperCase() + str.slice(1)
  },
  
  // 驼峰转下划线
  camelToSnake: (str: string): string => {
    return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)
  },
  
  // 下划线转驼峰
  snakeToCamel: (str: string): string => {
    return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
  },
  
  // 生成随机字符串
  random: (length = 8): string => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    let result = ''
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
  },
  
  // 掩码处理（如手机号、邮箱）
  mask: (str: string, start = 3, end = 4, maskChar = '*'): string => {
    if (!str || str.length <= start + end) return str
    const masked = maskChar.repeat(str.length - start - end)
    return str.substring(0, start) + masked + str.substring(str.length - end)
  }
}

// 数组工具
export const arrayUtils = {
  // 数组去重
  unique: <T>(arr: T[]): T[] => {
    return [...new Set(arr)]
  },
  
  // 根据属性去重
  uniqueBy: <T>(arr: T[], key: keyof T): T[] => {
    const seen = new Set()
    return arr.filter(item => {
      const value = item[key]
      if (seen.has(value)) {
        return false
      }
      seen.add(value)
      return true
    })
  },
  
  // 数组分组
  groupBy: <T>(arr: T[], key: keyof T): Record<string, T[]> => {
    return arr.reduce((groups, item) => {
      const group = String(item[key])
      groups[group] = groups[group] || []
      groups[group].push(item)
      return groups
    }, {} as Record<string, T[]>)
  },
  
  // 数组排序
  sortBy: <T>(arr: T[], key: keyof T, order: 'asc' | 'desc' = 'asc'): T[] => {
    return [...arr].sort((a, b) => {
      const aVal = a[key]
      const bVal = b[key]
      
      if (aVal < bVal) return order === 'asc' ? -1 : 1
      if (aVal > bVal) return order === 'asc' ? 1 : -1
      return 0
    })
  },
  
  // 数组分页
  paginate: <T>(arr: T[], page: number, size: number): T[] => {
    const start = (page - 1) * size
    return arr.slice(start, start + size)
  }
}

// 对象工具
export const objectUtils = {
  // 深拷贝
  deepClone: <T>(obj: T): T => {
    if (obj === null || typeof obj !== 'object') return obj
    if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T
    if (obj instanceof Array) return obj.map(item => objectUtils.deepClone(item)) as unknown as T
    
    const cloned = {} as T
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        cloned[key] = objectUtils.deepClone(obj[key])
      }
    }
    return cloned
  },
  
  // 对象合并
  merge: <T extends Record<string, any>>(...objects: Partial<T>[]): T => {
    return Object.assign({}, ...objects) as T
  },
  
  // 获取嵌套属性值
  get: (obj: any, path: string, defaultValue?: any): any => {
    const keys = path.split('.')
    let result = obj
    
    for (const key of keys) {
      if (result === null || result === undefined) {
        return defaultValue
      }
      result = result[key]
    }
    
    return result !== undefined ? result : defaultValue
  },
  
  // 设置嵌套属性值
  set: (obj: any, path: string, value: any): void => {
    const keys = path.split('.')
    let current = obj
    
    for (let i = 0; i < keys.length - 1; i++) {
      const key = keys[i]
      if (!(key in current) || typeof current[key] !== 'object') {
        current[key] = {}
      }
      current = current[key]
    }
    
    current[keys[keys.length - 1]] = value
  },
  
  // 删除空值属性
  removeEmpty: (obj: Record<string, any>): Record<string, any> => {
    const result: Record<string, any> = {}
    
    for (const [key, value] of Object.entries(obj)) {
      if (value !== null && value !== undefined && value !== '') {
        result[key] = value
      }
    }
    
    return result
  }
}

// 本地存储工具
export const storage = {
  // 设置本地存储
  set: (key: string, value: any): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error('Failed to set localStorage:', error)
    }
  },
  
  // 获取本地存储
  get: <T = any>(key: string, defaultValue?: T): T | null => {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue || null
    } catch (error) {
      console.error('Failed to get localStorage:', error)
      return defaultValue || null
    }
  },
  
  // 删除本地存储
  remove: (key: string): void => {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error('Failed to remove localStorage:', error)
    }
  },
  
  // 清空本地存储
  clear: (): void => {
    try {
      localStorage.clear()
    } catch (error) {
      console.error('Failed to clear localStorage:', error)
    }
  }
}

// 文件工具
export const fileUtils = {
  // 格式化文件大小
  formatSize: (bytes: number): string => {
    if (bytes === 0) return '0 B'
    
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  },
  
  // 获取文件扩展名
  getExtension: (filename: string): string => {
    return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2)
  },
  
  // 验证文件类型
  validateType: (file: File, allowedTypes: string[]): boolean => {
    return allowedTypes.includes(file.type)
  },
  
  // 验证文件大小
  validateSize: (file: File, maxSize: number): boolean => {
    return file.size <= maxSize
  },
  
  // 读取文件为Base64
  readAsBase64: (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = reject
      reader.readAsDataURL(file)
    })
  },
  
  // 读取文件为文本
  readAsText: (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = reject
      reader.readAsText(file)
    })
  }
}

// URL工具
export const urlUtils = {
  // 构建查询字符串
  buildQuery: (params: Record<string, any>): string => {
    const query = new URLSearchParams()
    
    for (const [key, value] of Object.entries(params)) {
      if (value !== null && value !== undefined && value !== '') {
        query.append(key, String(value))
      }
    }
    
    return query.toString()
  },
  
  // 解析查询字符串
  parseQuery: (search: string): Record<string, string> => {
    const params = new URLSearchParams(search)
    const result: Record<string, string> = {}
    
    for (const [key, value] of params.entries()) {
      result[key] = value
    }
    
    return result
  },
  
  // 获取当前页面URL参数
  getQueryParams: (): Record<string, string> => {
    return urlUtils.parseQuery(window.location.search)
  }
}

// 防抖和节流
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let lastTime = 0
  
  return (...args: Parameters<T>) => {
    const now = Date.now()
    if (now - lastTime >= wait) {
      lastTime = now
      func(...args)
    }
  }
}

// 复制到剪贴板
export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text)
    } else {
      // 兼容旧浏览器
      const textArea = document.createElement('textarea')
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
    }
    
    message.success('复制成功')
    return true
  } catch (error) {
    console.error('复制失败:', error)
    message.error('复制失败')
    return false
  }
}

// 下载文件
export const downloadFile = (url: string, filename?: string): void => {
  const link = document.createElement('a')
  link.href = url
  if (filename) {
    link.download = filename
  }
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 生成UUID
export const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

// 错误处理
export const handleError = (error: any, defaultMessage = '操作失败'): void => {
  console.error('Error:', error)
  
  let errorMessage = defaultMessage
  
  if (error?.response?.data?.message) {
    errorMessage = error.response.data.message
  } else if (error?.message) {
    errorMessage = error.message
  }
  
  message.error(errorMessage)
}

// 重试机制
export const retry = async <T>(
  fn: () => Promise<T>,
  maxAttempts = 3,
  delay = 1000
): Promise<T> => {
  let lastError: any
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error
      
      if (attempt === maxAttempts) {
        throw lastError
      }
      
      // 等待指定时间后重试
      await new Promise(resolve => setTimeout(resolve, delay * attempt))
    }
  }
  
  throw lastError
}