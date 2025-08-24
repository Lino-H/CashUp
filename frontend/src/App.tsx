import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, Badge, Typography, Space } from 'antd'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  BarChartOutlined,
  MonitorOutlined,
  LineChartOutlined,
  SafetyOutlined,
  BellOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined
} from '@ant-design/icons'

const { Header, Sider, Content } = Layout
const { Title } = Typography

function App() {
  const [collapsed, setCollapsed] = useState(false)

  // 菜单项配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板'
    },
    {
      key: '/strategies',
      icon: <BarChartOutlined />,
      label: '策略管理'
    },
    {
      key: '/trading',
      icon: <MonitorOutlined />,
      label: '交易监控'
    },
    {
      key: '/market',
      icon: <LineChartOutlined />,
      label: '市场分析'
    },
    {
      key: '/risk',
      icon: <SafetyOutlined />,
      label: '风险管理'
    },
    {
      key: '/notifications',
      icon: <BellOutlined />,
      label: '通知中心'
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置'
    }
  ]

  // 用户下拉菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
    },
  ]

  const navigate = useNavigate()
  const location = useLocation()

  // 处理菜单点击
  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  // 处理用户菜单点击
  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'logout') {
      localStorage.removeItem('access_token')
      navigate('/login')
    }
  }

  return (
    <Layout className="min-h-screen">
      {/* 侧边栏 */}
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        className="bg-white shadow-lg"
        width={240}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-center border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <BarChartOutlined className="text-2xl text-blue-600" />
            {!collapsed && (
              <Title level={4} className="!mb-0 !text-gray-800">
                CashUp
              </Title>
            )}
          </div>
        </div>

        {/* 导航菜单 */}
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          className="border-r-0 mt-4"
          onClick={handleMenuClick}
        />
      </Sider>

      <Layout>
        {/* 顶部导航 */}
        <Header className="bg-white px-6 flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-4">
            {/* 折叠按钮 */}
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="text-lg p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            </button>

            {/* 页面标题 */}
            <Title level={4} className="!mb-0 !text-gray-800">
              量化交易系统
            </Title>
          </div>

          {/* 右侧操作区 */}
          <div className="flex items-center space-x-4">
            {/* 通知铃铛 */}
            <Badge count={5} size="small">
              <BellOutlined className="text-lg text-gray-600 hover:text-blue-600 cursor-pointer" />
            </Badge>

            {/* 用户头像和下拉菜单 */}
            <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenuClick }} placement="bottomRight">
              <Space className="cursor-pointer hover:bg-gray-100 px-3 py-2 rounded-lg transition-colors">
                <Avatar size="small" icon={<UserOutlined />} />
                <span className="text-gray-700">交易员</span>
              </Space>
            </Dropdown>
          </div>
        </Header>

        {/* 主内容区 */}
        <Content className="m-6 p-6 bg-white rounded-lg shadow-sm overflow-auto">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default App