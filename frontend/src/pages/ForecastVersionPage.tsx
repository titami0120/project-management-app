import { Table, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useEffect, useState } from 'react'
import { getForecastVersions } from '../api/forecastVersionApi'
import type { ForecastVersionResponse } from '../types/projectTypes'

const { Title } = Typography

const TRIGGER_LABELS: Record<string, string> = {
  plan_upload: '計画工数CSVアップロード',
}

const ForecastVersionPage = () => {
  const [versions, setVersions] = useState<ForecastVersionResponse[]>([])

  useEffect(() => {
    getForecastVersions().then(setVersions).catch(console.error)
  }, [])

  const columns: ColumnsType<ForecastVersionResponse> = [
    {
      title: 'バージョン番号',
      dataIndex: 'version_no',
      key: 'version_no',
      width: 140,
      render: (v: number) => `v${v}`,
    },
    {
      title: '作成契機',
      dataIndex: 'trigger_type',
      key: 'trigger_type',
      render: (v: string) => TRIGGER_LABELS[v] ?? v,
    },
    {
      title: '作成日時',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 200,
      render: (v: string) => new Date(v).toLocaleString('ja-JP'),
    },
  ]

  return (
    <div>
      <Title level={3}>見込工数バージョン一覧</Title>
      <Table<ForecastVersionResponse>
        columns={columns}
        dataSource={versions}
        rowKey="id"
        pagination={{ pageSize: 20 }}
        size="middle"
      />
    </div>
  )
}

export default ForecastVersionPage
