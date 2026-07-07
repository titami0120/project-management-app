import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import { Alert, Button, Form, Input, Modal, Space, Table, Typography, notification } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useState } from 'react'
import {
  createDepartment,
  deleteDepartment,
  getDepartments,
  updateDepartment,
} from '../api/departmentApi'
import type { DepartmentResponse } from '../types/projectTypes'

const { Title } = Typography

type FormValues = { code: string; name: string }

const extractError = (err: unknown): string => {
  if (err && typeof err === 'object' && 'response' in err) {
    const res = (err as { response?: { data?: { detail?: string } } }).response
    if (res?.data?.detail) return res.data.detail
  }
  if (err instanceof Error) return err.message
  return String(err)
}

const DepartmentPage = () => {
  const [departments, setDepartments] = useState<DepartmentResponse[]>([])
  const [loading, setLoading] = useState(false)

  const [modalOpen, setModalOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<DepartmentResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [modalError, setModalError] = useState<string | null>(null)
  const [form] = Form.useForm<FormValues>()

  const [deleteTarget, setDeleteTarget] = useState<DepartmentResponse | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const load = useCallback(() => {
    setLoading(true)
    getDepartments()
      .then(setDepartments)
      .catch(() => notification.error({ message: '部門一覧の取得に失敗しました', placement: 'topRight' }))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const openAdd = () => {
    setEditTarget(null)
    setModalError(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (dept: DepartmentResponse) => {
    setEditTarget(dept)
    setModalError(null)
    form.setFieldsValue({ code: dept.code, name: dept.name })
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
        await updateDepartment(editTarget.id, { name: values.name })
        notification.success({ message: '部門を更新しました', placement: 'topRight' })
      } else {
        await createDepartment({ code: values.code, name: values.name })
        notification.success({ message: '部門を追加しました', placement: 'topRight' })
      }
      setModalOpen(false)
      load()
    } catch (err) {
      setModalError(extractError(err))
    } finally {
      setSubmitting(false)
    }
  }

  const handleModalCancel = () => {
    if (submitting) return
    setModalOpen(false)
  }

  const openDelete = (dept: DepartmentResponse) => {
    setDeleteTarget(dept)
    setDeleteError(null)
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    setDeleteError(null)
    try {
      await deleteDepartment(deleteTarget.id)
      setDeleteTarget(null)
      notification.success({ message: '部門を削除しました', placement: 'topRight' })
      load()
    } catch (err) {
      setDeleteError(extractError(err))
    } finally {
      setDeleting(false)
    }
  }

  const columns: ColumnsType<DepartmentResponse> = [
    { title: '部門コード', dataIndex: 'code', key: 'code', width: 150 },
    { title: '部門名', dataIndex: 'name', key: 'name' },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: unknown, record: DepartmentResponse) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)}>
            編集
          </Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => openDelete(record)} />
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Space style={{ marginBottom: 16, justifyContent: 'space-between', width: '100%' }}>
        <Title level={3} style={{ margin: 0 }}>部門マスタ</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openAdd}>
          追加
        </Button>
      </Space>

      <Table<DepartmentResponse>
        columns={columns}
        dataSource={departments}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 25 }}
        size="middle"
      />

      {/* 追加・編集モーダル */}
      <Modal
        title={editTarget ? '部門を編集' : '部門を追加'}
        open={modalOpen}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        okText="保存"
        cancelText="キャンセル"
        confirmLoading={submitting}
        okButtonProps={{ disabled: submitting }}
        cancelButtonProps={{ disabled: submitting }}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="code"
            label="部門コード"
            rules={[{ required: true, message: '部門コードを入力してください' }]}
          >
            <Input maxLength={50} disabled={!!editTarget} placeholder="例: D01" />
          </Form.Item>
          <Form.Item
            name="name"
            label="部門名"
            rules={[{ required: true, message: '部門名を入力してください' }]}
          >
            <Input maxLength={100} placeholder="例: 開発部" />
          </Form.Item>
        </Form>
        {modalError && (
          <Alert type="error" message={modalError} showIcon style={{ marginTop: 8 }} />
        )}
      </Modal>

      {/* 削除モーダル */}
      <Modal
        title="部門を削除しますか？"
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
            <Typography.Text>
              <Typography.Text strong>{deleteTarget.code} {deleteTarget.name}</Typography.Text> を削除します。
            </Typography.Text>
            <Typography.Text type="warning">この操作は取り消せません。</Typography.Text>
            {deleteError && (
              <Alert type="error" message={deleteError} showIcon />
            )}
          </Space>
        )}
      </Modal>
    </div>
  )
}

export default DepartmentPage
