import { useState } from 'react'
import { Layout, Menu } from 'antd'
import {
  BarChartOutlined,
  ClusterOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  FundProjectionScreenOutlined,
  HistoryOutlined,
  ProjectOutlined,
  SettingOutlined,
  TeamOutlined,
  UploadOutlined,
  UserOutlined,
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
    key: 'master',
    icon: <DatabaseOutlined />,
    label: 'マスタ管理',
    children: [
      { key: '/master/departments', icon: <TeamOutlined />, label: '部門マスタ' },
      { key: '/master/members', icon: <UserOutlined />, label: '要員マスタ' },
      { key: '/master/teams', icon: <ClusterOutlined />, label: 'チームマスタ' },
      { key: '/master/projects', icon: <ProjectOutlined />, label: 'プロジェクトマスタ' },
    ],
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

  const isMasterRoute = location.pathname.startsWith('/master')
  const [openKeys, setOpenKeys] = useState<string[]>(isMasterRoute ? ['master'] : [])

  const selectedKey = location.pathname

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={(c) => {
          setCollapsed(c)
          if (c) setOpenKeys([])
        }}
        width={240}
      >
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
          openKeys={collapsed ? [] : openKeys}
          onOpenChange={setOpenKeys}
          items={menuItems}
          onClick={({ key }) => {
            if (!key.startsWith('/')) return
            navigate(key)
          }}
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
