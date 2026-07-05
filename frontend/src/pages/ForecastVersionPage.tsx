import { DeleteOutlined, RollbackOutlined } from '@ant-design/icons'
import { Alert, Button, Modal, Space, Table, Tag, Typography, notification } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useState } from 'react'
import {
  deleteForecastVersion,
  getForecastVersions,
  restoreForecastVersion,
} from '../api/forecastVersionApi'
import type { ForecastVersionResponse } from '../types/projectTypes'

const { Title, Text } = Typography

const extractErrorMessage = (err: unknown): string => {
  if (err && typeof err === 'object' && 'response' in err) {
    const res = (err as { response?: { data?: { detail?: string } } }).response
    if (res?.data?.detail) return res.data.detail
  }
  if (err instanceof Error) return err.message
  return String(err)
}

const ForecastVersionPage = () => {
  const [versions, setVersions] = useState<ForecastVersionResponse[]>([])
  const [loading, setLoading] = useState(false)

  const [restoreTarget, setRestoreTarget] = useState<ForecastVersionResponse | null>(null)
  const [restoring, setRestoring] = useState(false)
  const [restoreError, setRestoreError] = useState<string | null>(null)

  const [deleteTarget, setDeleteTarget] = useState<ForecastVersionResponse | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const load = useCallback(() => {
    setLoading(true)
    getForecastVersions()
      .then(setVersions)
      .catch(() => notification.error({ message: 'バージョン一覧の取得に失敗しました', placement: 'topRight' }))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const handleRestoreConfirm = useCallback(async () => {
    if (!restoreTarget) return
    setRestoring(true)
    setRestoreError(null)
    try {
      const res = await restoreForecastVersion(restoreTarget.id)
      setRestoreTarget(null)
      notification.success({
        message: '復元完了',
        description: `v${restoreTarget.version_no}「${restoreTarget.name}」から ${res.restored_count.toLocaleString()} 件のレコードを復元しました。`,
        placement: 'topRight',
        duration: 5,
      })
    } catch (err) {
      setRestoreError(extractErrorMessage(err))
    } finally {
      setRestoring(false)
    }
  }, [restoreTarget])

  const handleDeleteConfirm = useCallback(async () => {
    if (!deleteTarget) return
    setDeleting(true)
    setDeleteError(null)
    try {
      await deleteForecastVersion(deleteTarget.id)
      setDeleteTarget(null)
      notification.success({ message: 'バージョンを削除しました', placement: 'topRight' })
      load()
    } catch (err) {
      setDeleteError(extractErrorMessage(err))
    } finally {
      setDeleting(false)
    }
  }, [deleteTarget, load])

  const columns: ColumnsType<ForecastVersionResponse> = [
    {
      title: 'バージョン',
      dataIndex: 'version_no',
      key: 'version_no',
      width: 100,
      render: (v: number) => <Tag color="blue">v{v}</Tag>,
    },
    {
      title: 'バージョン名',
      dataIndex: 'name',
      key: 'name',
      width: 200,
    },
    {
      title: '詳細',
      dataIndex: 'description',
      key: 'description',
      render: (v: string | null) => v ?? <span style={{ color: '#bbb' }}>—</span>,
    },
    {
      title: 'スナップショット件数',
      dataIndex: 'snapshot_count',
      key: 'snapshot_count',
      width: 160,
      align: 'right',
      render: (v: number) => `${v.toLocaleString()} 件`,
    },
    {
      title: '保存日時',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (v: string) => new Date(v).toLocaleString('ja-JP'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 160,
      render: (_: unknown, record: ForecastVersionResponse) => (
        <Space>
          <Button
            size="small"
            icon={<RollbackOutlined />}
            onClick={() => { setRestoreTarget(record); setRestoreError(null) }}
          >
            復元
          </Button>
          <Button
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => { setDeleteTarget(record); setDeleteError(null) }}
          />
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={3}>工数バージョン一覧</Title>
      <Table<ForecastVersionResponse>
        columns={columns}
        dataSource={versions}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20 }}
        size="middle"
      />

      {/* 復元モーダル */}
      <Modal
        title="バージョンを復元しますか？"
        open={!!restoreTarget}
        onOk={handleRestoreConfirm}
        onCancel={() => { setRestoreTarget(null); setRestoreError(null) }}
        okText="復元する"
        okButtonProps={{ danger: true, loading: restoring }}
        cancelButtonProps={{ disabled: restoring }}
        cancelText="キャンセル"
        closable={!restoring}
        maskClosable={!restoring}
        destroyOnHidden
      >
        {restoreTarget && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text>
              <Tag color="blue">v{restoreTarget.version_no}</Tag>
              <Text strong>{restoreTarget.name}</Text> のスナップショットから現在の計画工数を上書きします。
            </Text>
            <Text type="secondary">
              スナップショット件数: {restoreTarget.snapshot_count.toLocaleString()} 件
            </Text>
            <Text type="warning">この操作は取り消せません。</Text>
            {restoreError && (
              <Alert type="error" message="復元に失敗しました" description={restoreError} showIcon />
            )}
          </Space>
        )}
      </Modal>

      {/* 削除モーダル */}
      <Modal
        title="バージョンを削除しますか？"
        open={!!deleteTarget}
        onOk={handleDeleteConfirm}
        onCancel={() => { setDeleteTarget(null); setDeleteError(null) }}
        okText="削除する"
        okButtonProps={{ danger: true, loading: deleting }}
        cancelButtonProps={{ disabled: deleting }}
        cancelText="キャンセル"
        closable={!deleting}
        maskClosable={!deleting}
        destroyOnHidden
      >
        {deleteTarget && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text>
              <Tag color="blue">v{deleteTarget.version_no}</Tag>
              <Text strong>{deleteTarget.name}</Text> を削除します。
            </Text>
            <Text type="secondary">
              スナップショット件数: {deleteTarget.snapshot_count.toLocaleString()} 件
            </Text>
            <Text type="warning">スナップショットデータもすべて削除されます。この操作は取り消せません。</Text>
            {deleteError && (
              <Alert type="error" message="削除に失敗しました" description={deleteError} showIcon />
            )}
          </Space>
        )}
      </Modal>
    </div>
  )
}

export default ForecastVersionPage
