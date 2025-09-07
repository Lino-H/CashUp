import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { router, AppWithAuthProvider } from './router'
import './index.css'

// 配置 dayjs 中文
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
dayjs.locale('zh-cn')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN}>
      <RouterProvider router={router} />
    </ConfigProvider>
  </React.StrictMode>,
)