import { LinkOutlined } from '@ant-design/icons'
import { Button, Space, Table, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useState } from 'react'
import { getProjects } from '../api/projectApi'
import ProjectAssignModal from '../components/project/ProjectAssignModal'
import ProjectEditModal from '../components/project/ProjectEditModal'
import type { ProjectResponse } from '../types/projectTypes'

const { Title } = Typography

const ProjectManagementPage = () => {
  const [projects, setProjects] = useState<ProjectResponse[]>([])
  const [editTarget, setEditTarget] = useState<ProjectResponse | null>(null)
  const [assignOpen, setAssignOpen] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    getProjects().then(setProjects).catch(console.error)
  }, [refreshKey])

  const handleUpdated = useCallback(() => {
    setEditTarget(null)
    setRefreshKey((k) => k + 1)
  }, [])

  const handleAssigned = useCallback(() => {
    setAssignOpen(false)
    setRefreshKey((k) => k + 1)
  }, [])

  const columns: ColumnsType<ProjectResponse> = [
    { title: 'WBS仮コード', dataIndex: 'wbs_tmp', key: 'wbs_tmp', width: 120 },
    { title: 'WBS名称', dataIndex: 'name', key: 'name', ellipsis: true },
    {
      title: 'WBSコード',
      dataIndex: 'code',
      key: 'code',
      width: 130,
      render: (v: string | null) => v ?? '-',
    },
    {
      title: '表示順',
      dataIndex: 'display_order',
      key: 'display_order',
      width: 80,
      align: 'right' as const,
      render: (v: number | null) => v ?? '-',
    },
    {
      title: '案件',
      key: 'matter',
      ellipsis: true,
      render: (_: unknown, r: ProjectResponse) =>
        r.matter_name ?? <span style={{ color: '#999' }}>未紐づき</span>,
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, r: ProjectResponse) => (
        <Button size="small" onClick={() => setEditTarget(r)}>
          編集
        </Button>
      ),
    },
  ]

  return (
    <div>
      <Space style={{ marginBottom: 16, justifyContent: 'space-between', width: '100%' }}>
        <Title level={3} style={{ margin: 0 }}>
          プロジェクト管理
        </Title>
        <Button icon={<LinkOutlined />} onClick={() => setAssignOpen(true)}>
          案件紐づけ
        </Button>
      </Space>
      <Table<ProjectResponse>
        columns={columns}
        dataSource={projects}
        rowKey="id"
        pagination={{ pageSize: 25 }}
        size="middle"
      />
      <ProjectEditModal
        project={editTarget}
        onClose={() => setEditTarget(null)}
        onUpdated={handleUpdated}
      />
      <ProjectAssignModal
        open={assignOpen}
        onClose={() => setAssignOpen(false)}
        onAssigned={handleAssigned}
      />
    </div>
  )
}

export default ProjectManagementPage
