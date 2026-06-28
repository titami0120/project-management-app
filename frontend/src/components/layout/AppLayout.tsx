import { useState } from 'react'
import { Layout, Menu } from 'antd'
import {
  BarChartOutlined,
  FileTextOutlined,
  FundProjectionScreenOutlined,
  HistoryOutlined,
  SettingOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'

const { Sider, Content } = Layout

const menuItems = [
  {
    key: '/workload',
    icon: <BarChartOutlined />,
    label: '要員別工数計画',
  },
  {
    key: '/project-workload',
    icon: <FundProjectionScreenOutlined />,
    label: 'PJ別工数計画',
  },
  {
    key: '/matters',
    icon: <FileTextOutlined />,
    label: '案件・プロジェクト',
  },
  {
    key: '/forecast-versions',
    icon: <HistoryOutlined />,
    label: '見込工数バージョン',
  },
  {
    key: '/upload/plan',
    icon: <UploadOutlined />,
    label: 'アップロード（計画工数CSV）',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '設定',
  },
]

const AppLayout = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const selectedKey =
    menuItems.find((item) => location.pathname.startsWith(item.key))?.key ?? '/workload'

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} width={240}>
        <div
          style={{
            height: 48,
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: collapsed ? 0 : '0 16px',
            color: '#fff',
            fontWeight: 600,
            fontSize: 16,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
          }}
        >
          {!collapsed && '工数管理'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Content style={{ padding: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default AppLayout
