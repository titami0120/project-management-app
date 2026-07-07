import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import {
  Alert,
  Button,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  notification,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useState } from 'react'
import { getMatters } from '../api/matterApi'
import { createProject, deleteProject, getProjects, updateProject } from '../api/projectApi'
import type { MatterResponse } from '../types/matterTypes'
import type { ProjectResponse } from '../types/projectTypes'

const { Title, Text } = Typography

type FormValues = {
  wbs_tmp: string
  name: string
  code?: string
  display_order?: number
  matter_id?: number
}

const extractError = (err: unknown): string => {
  if (err && typeof err === 'object' && 'response' in err) {
    const res = (err as { response?: { data?: { detail?: string } } }).response
    if (res?.data?.detail) return res.data.detail
  }
  if (err instanceof Error) return err.message
  return String(err)
}

const ProjectMasterPage = () => {
  const [projects, setProjects] = useState<ProjectResponse[]>([])
  const [matters, setMatters] = useState<MatterResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')

  const [modalOpen, setModalOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<ProjectResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [modalError, setModalError] = useState<string | null>(null)
  const [form] = Form.useForm<FormValues>()

  const [deleteTarget, setDeleteTarget] = useState<ProjectResponse | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const load = useCallback(() => {
    setLoading(true)
    getProjects()
      .then(setProjects)
      .catch(() => notification.error({ message: 'プロジェクト一覧の取得に失敗しました', placement: 'topRight' }))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    load()
    getMatters().then(setMatters).catch(console.error)
  }, [load])

  const filtered = search.trim()
    ? projects.filter(
        (p) =>
          p.name.includes(search) ||
          p.wbs_tmp.includes(search) ||
          (p.code ?? '').includes(search),
      )
    : projects

  const openAdd = () => {
    setEditTarget(null)
    setModalError(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (p: ProjectResponse) => {
    setEditTarget(p)
    setModalError(null)
    form.setFieldsValue({
      wbs_tmp: p.wbs_tmp,
      name: p.name,
      code: p.code ?? undefined,
      display_order: p.display_order ?? undefined,
      matter_id: p.matter_id ?? undefined,
    })
    setModalOpen(true)
  }

  const handleModalOk = async () => {
    let values: FormValues
    try {
      values = await form.validateFields()
    } catch {
      return
    }
    setSubmitting(true)
    setModalError(null)
    try {
      if (editTarget) {
        await updateProject(editTarget.id, {
          name: values.name,
          code: values.code || undefined,
          display_order: values.display_order ?? undefined,
          matter_id: values.matter_id ?? null,
        })
        notification.success({ message: 'プロジェクトを更新しました', placement: 'topRight' })
      } else {
        await createProject({
          wbs_tmp: values.wbs_tmp,
          name: values.name,
          code: values.code || undefined,
          display_order: values.display_order ?? undefined,
          matter_id: values.matter_id ?? null,
        })
        notification.success({ message: 'プロジェクトを追加しました', placement: 'topRight' })
      }
      setModalOpen(false)
      load()
    } catch (err) {
      setModalError(extractError(err))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    setDeleteError(null)
    try {
      await deleteProject(deleteTarget.id)
      setDeleteTarget(null)
      notification.success({ message: 'プロジェクトを削除しました', placement: 'topRight' })
      load()
    } catch (err) {
      setDeleteError(extractError(err))
    } finally {
      setDeleting(false)
    }
  }

  const columns: ColumnsType<ProjectResponse> = [
    { title: 'WBS仮コード', dataIndex: 'wbs_tmp', key: 'wbs_tmp', width: 130 },
    { title: 'WBS名称', dataIndex: 'name', key: 'name', ellipsis: true },
    {
      title: 'WBSコード',
      dataIndex: 'code',
      key: 'code',
      width: 130,
      render: (v: string | null) => v ?? <Text type="secondary">—</Text>,
    },
    {
      title: '表示順',
      dataIndex: 'display_order',
      key: 'display_order',
      width: 80,
      align: 'right',
      render: (v: number | null) => v ?? <Text type="secondary">—</Text>,
    },
    {
      title: '案件',
      dataIndex: 'matter_name',
      key: 'matter_name',
      ellipsis: true,
      render: (v: string | null) =>
        v ? <Tag color="geekblue">{v}</Tag> : <Text type="secondary">未紐づき</Text>,
    },
    {
      title: '登録日時',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v: string) => new Date(v).toLocaleString('ja-JP'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 110,
      render: (_: unknown, record: ProjectResponse) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)}>
            編集
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
      <Space style={{ marginBottom: 16, justifyContent: 'space-between', width: '100%' }}>
        <Title level={3} style={{ margin: 0 }}>プロジェクトマスタ</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openAdd}>
          追加
        </Button>
      </Space>

      <Input.Search
        placeholder="WBS仮コード・名称・WBSコードで絞り込み"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        allowClear
        style={{ width: 360, marginBottom: 12 }}
      />

      <Table<ProjectResponse>
        columns={columns}
        dataSource={filtered}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 25 }}
        size="middle"
      />

      {/* 追加・編集モーダル */}
      <Modal
        title={editTarget ? 'プロジェクトを編集' : 'プロジェクトを追加'}
        open={modalOpen}
        onOk={handleModalOk}
        onCancel={() => { if (!submitting) setModalOpen(false) }}
        okText="保存"
        cancelText="キャンセル"
        confirmLoading={submitting}
        okButtonProps={{ disabled: submitting }}
        cancelButtonProps={{ disabled: submitting }}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="wbs_tmp"
            label="WBS仮コード"
            rules={[{ required: true, message: 'WBS仮コードを入力してください' }]}
          >
            <Input maxLength={50} disabled={!!editTarget} placeholder="例: WBS-001" />
          </Form.Item>
          <Form.Item
            name="name"
            label="WBS名称"
            rules={[{ required: true, message: 'WBS名称を入力してください' }]}
          >
            <Input maxLength={200} placeholder="例: システム開発" />
          </Form.Item>
          <Form.Item name="code" label="WBSコード">
            <Input maxLength={50} placeholder="例: WBS-001-REAL（任意）" />
          </Form.Item>
          <Form.Item name="display_order" label="表示順">
            <InputNumber<number> min={0} style={{ width: '100%' }} placeholder="数値が小さいほど上に表示（任意）" />
          </Form.Item>
          <Form.Item name="matter_id" label="紐づく案件">
            <Select
              placeholder="案件を選択（任意）"
              allowClear
              showSearch
              optionFilterProp="label"
              options={matters.map((m) => ({ value: m.id, label: `${m.code} ${m.name}` }))}
            />
          </Form.Item>
        </Form>
        {modalError && (
          <Alert type="error" message={modalError} showIcon style={{ marginTop: 8 }} />
        )}
      </Modal>

      {/* 削除モーダル */}
      <Modal
        title="プロジェクトを削除しますか？"
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
              <Text strong>{deleteTarget.wbs_tmp}</Text>「{deleteTarget.name}」を削除します。
            </Text>
            <Text type="secondary">
              関連する工数データは削除されませんが、このプロジェクトは一覧に表示されなくなります。
            </Text>
            <Text type="warning">この操作は取り消せません。</Text>
            {deleteError && <Alert type="error" message={deleteError} showIcon />}
          </Space>
        )}
      </Modal>
    </div>
  )
}

export default ProjectMasterPage
