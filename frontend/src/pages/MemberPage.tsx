import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import { Alert, Button, Form, Input, Modal, Select, Space, Table, Typography, notification } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useState } from 'react'
import { getDepartments } from '../api/departmentApi'
import { createMember, deleteMember, getMembers, updateMember } from '../api/memberApi'
import type { DepartmentResponse, MemberResponse } from '../types/projectTypes'

const { Title, Text } = Typography

type FormValues = { employee_code: string; name: string; department_id: number }

const extractError = (err: unknown): string => {
  if (err && typeof err === 'object' && 'response' in err) {
    const res = (err as { response?: { data?: { detail?: string } } }).response
    if (res?.data?.detail) return res.data.detail
  }
  if (err instanceof Error) return err.message
  return String(err)
}

const MemberPage = () => {
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [departments, setDepartments] = useState<DepartmentResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [filterDeptId, setFilterDeptId] = useState<number | undefined>(undefined)

  const [modalOpen, setModalOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<MemberResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [modalError, setModalError] = useState<string | null>(null)
  const [form] = Form.useForm<FormValues>()

  const [deleteTarget, setDeleteTarget] = useState<MemberResponse | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const loadMembers = useCallback((deptId?: number) => {
    setLoading(true)
    getMembers(deptId)
      .then(setMembers)
      .catch(() => notification.error({ message: '要員一覧の取得に失敗しました', placement: 'topRight' }))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    getDepartments().then(setDepartments).catch(console.error)
  }, [])

  useEffect(() => {
    loadMembers(filterDeptId)
  }, [loadMembers, filterDeptId])

  const openAdd = () => {
    setEditTarget(null)
    setModalError(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (member: MemberResponse) => {
    setEditTarget(member)
    setModalError(null)
    form.setFieldsValue({
      employee_code: member.employee_code,
      name: member.name,
      department_id: member.department_id,
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
        await updateMember(editTarget.id, { name: values.name, department_id: values.department_id })
        notification.success({ message: '要員を更新しました', placement: 'topRight' })
      } else {
        await createMember({
          employee_code: values.employee_code,
          name: values.name,
          department_id: values.department_id,
        })
        notification.success({ message: '要員を追加しました', placement: 'topRight' })
      }
      setModalOpen(false)
      loadMembers(filterDeptId)
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

  const openDelete = (member: MemberResponse) => {
    setDeleteTarget(member)
    setDeleteError(null)
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    setDeleteError(null)
    try {
      await deleteMember(deleteTarget.id)
      setDeleteTarget(null)
      notification.success({ message: '要員を削除しました', placement: 'topRight' })
      loadMembers(filterDeptId)
    } catch (err) {
      setDeleteError(extractError(err))
    } finally {
      setDeleting(false)
    }
  }

  const columns: ColumnsType<MemberResponse> = [
    { title: '社員コード', dataIndex: 'employee_code', key: 'employee_code', width: 130 },
    { title: '氏名', dataIndex: 'name', key: 'name', width: 180 },
    { title: '部門', dataIndex: 'department_name', key: 'department_name' },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: unknown, record: MemberResponse) => (
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
        <Title level={3} style={{ margin: 0 }}>要員マスタ</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openAdd}>
          追加
        </Button>
      </Space>

      <div style={{ marginBottom: 16 }}>
        <Select
          placeholder="部門で絞り込み"
          allowClear
          style={{ width: 240 }}
          value={filterDeptId}
          onChange={(v) => setFilterDeptId(v)}
          onClear={() => setFilterDeptId(undefined)}
        >
          {departments.map((d) => (
            <Select.Option key={d.id} value={d.id}>{d.code} {d.name}</Select.Option>
          ))}
        </Select>
      </div>

      <Table<MemberResponse>
        columns={columns}
        dataSource={members}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 25 }}
        size="middle"
      />

      {/* 追加・編集モーダル */}
      <Modal
        title={editTarget ? '要員を編集' : '要員を追加'}
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
            name="employee_code"
            label="社員コード"
            rules={[{ required: true, message: '社員コードを入力してください' }]}
          >
            <Input maxLength={50} disabled={!!editTarget} placeholder="例: E001" />
          </Form.Item>
          <Form.Item
            name="name"
            label="氏名"
            rules={[{ required: true, message: '氏名を入力してください' }]}
          >
            <Input maxLength={100} placeholder="例: 山田 太郎" />
          </Form.Item>
          <Form.Item
            name="department_id"
            label="部門"
            rules={[{ required: true, message: '部門を選択してください' }]}
          >
            <Select placeholder="部門を選択">
              {departments.map((d) => (
                <Select.Option key={d.id} value={d.id}>{d.code} {d.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
        {modalError && (
          <Alert type="error" message={modalError} showIcon style={{ marginTop: 8 }} />
        )}
      </Modal>

      {/* 削除モーダル */}
      <Modal
        title="要員を削除しますか？"
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
              <Text strong>{deleteTarget.employee_code} {deleteTarget.name}</Text>（{deleteTarget.department_name}）を削除します。
            </Text>
            <Text type="warning">この操作は取り消せません。</Text>
            {deleteError && (
              <Alert type="error" message={deleteError} showIcon />
            )}
          </Space>
        )}
      </Modal>
    </div>
  )
}

export default MemberPage
