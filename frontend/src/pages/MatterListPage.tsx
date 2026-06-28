import { PlusOutlined } from '@ant-design/icons'
import { Button, Space, Table, Tag, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useState } from 'react'
import { getMatters } from '../api/matterApi'
import { getMembers } from '../api/memberApi'
import MatterFormModal from '../components/matter/MatterFormModal'
import type { MatterResponse } from '../types/matterTypes'

const { Title } = Typography

const STATUS_COLORS: Record<string, string> = {
  計画中: 'blue',
  進行中: 'green',
  完了: 'default',
  中止: 'red',
}

const MatterListPage = () => {
  const [matters, setMatters] = useState<MatterResponse[]>([])
  const [memberMap, setMemberMap] = useState<Map<number, string>>(new Map())
  const [refreshKey, setRefreshKey] = useState(0)
  const [modalOpen, setModalOpen] = useState(false)

  useEffect(() => {
    Promise.all([getMatters(), getMembers()])
      .then(([mattersData, membersData]) => {
        setMatters(mattersData)
        setMemberMap(new Map(membersData.map((m) => [m.id, m.name])))
      })
      .catch(console.error)
  }, [refreshKey])

  const handleCreated = useCallback(() => {
    setModalOpen(false)
    setRefreshKey((k) => k + 1)
  }, [])

  const columns: ColumnsType<MatterResponse> = [
    { title: '案件名', dataIndex: 'name', key: 'name', ellipsis: true },
    { title: '案件コード', dataIndex: 'code', key: 'code', width: 130 },
    {
      title: '顧客名',
      dataIndex: 'client_name',
      key: 'client_name',
      ellipsis: true,
      render: (v: string | null) => v ?? '-',
    },
    {
      title: 'PM',
      key: 'pm',
      width: 150,
      render: (_: unknown, r: MatterResponse) =>
        r.pm_member_id ? (memberMap.get(r.pm_member_id) ?? '-') : '-',
    },
    {
      title: 'ステータス',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (v: string) => <Tag color={STATUS_COLORS[v] ?? 'default'}>{v}</Tag>,
    },
    {
      title: 'PJ数',
      dataIndex: 'project_count',
      key: 'project_count',
      width: 70,
      align: 'right' as const,
    },
    {
      title: '作成日時',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v: string) => new Date(v).toLocaleString('ja-JP'),
    },
  ]

  return (
    <div>
      <Space style={{ marginBottom: 16, justifyContent: 'space-between', width: '100%' }}>
        <Title level={3} style={{ margin: 0 }}>
          案件一覧
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          新規案件登録
        </Button>
      </Space>
      <Table<MatterResponse>
        columns={columns}
        dataSource={matters}
        rowKey="id"
        pagination={{ pageSize: 20 }}
        size="middle"
      />
      <MatterFormModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={handleCreated}
      />
    </div>
  )
}

export default MatterListPage
