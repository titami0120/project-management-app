import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  TeamOutlined,
  UserDeleteOutlined,
} from '@ant-design/icons'
import {
  Alert,
  Button,
  Drawer,
  Form,
  Input,
  List,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  notification,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { getDepartments } from '../api/departmentApi'
import { getMembers } from '../api/memberApi'
import {
  addTeamMember,
  createTeam,
  deleteTeam,
  getTeamMembers,
  getTeams,
  removeTeamMember,
  updateTeam,
} from '../api/teamApi'
import type { DepartmentResponse, MemberResponse, TeamMemberResponse, TeamResponse } from '../types/projectTypes'

const { Title, Text } = Typography

type FormValues = { name: string; department_id: number }

const extractError = (err: unknown): string => {
  if (err && typeof err === 'object' && 'response' in err) {
    const res = (err as { response?: { data?: { detail?: string } } }).response
    if (res?.data?.detail) return res.data.detail
  }
  if (err instanceof Error) return err.message
  return String(err)
}

const TeamPage = () => {
  // ----- master data -----
  const [teams, setTeams] = useState<TeamResponse[]>([])
  const [departments, setDepartments] = useState<DepartmentResponse[]>([])
  const [allMembers, setAllMembers] = useState<MemberResponse[]>([])
  const [loading, setLoading] = useState(false)

  // ----- add / edit modal -----
  const [modalOpen, setModalOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<TeamResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [modalError, setModalError] = useState<string | null>(null)
  const [form] = Form.useForm<FormValues>()

  // ----- delete modal -----
  const [deleteTarget, setDeleteTarget] = useState<TeamResponse | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  // ----- member drawer -----
  const [drawerTeam, setDrawerTeam] = useState<TeamResponse | null>(null)
  const [teamMembers, setTeamMembers] = useState<TeamMemberResponse[]>([])
  const [membersLoading, setMembersLoading] = useState(false)
  const [addMemberId, setAddMemberId] = useState<number | undefined>(undefined)
  const [addingMember, setAddingMember] = useState(false)
  const [addMemberError, setAddMemberError] = useState<string | null>(null)

  // ----- load -----
  const loadTeams = useCallback(() => {
    setLoading(true)
    getTeams()
      .then(setTeams)
      .catch(() => notification.error({ message: 'チーム一覧の取得に失敗しました', placement: 'topRight' }))
      .finally(() => setLoading(false))
  }, [])

  const loadTeamMembers = useCallback((teamId: number) => {
    setMembersLoading(true)
    getTeamMembers(teamId)
      .then(setTeamMembers)
      .catch(() => notification.error({ message: 'メンバー一覧の取得に失敗しました', placement: 'topRight' }))
      .finally(() => setMembersLoading(false))
  }, [])

  useEffect(() => {
    loadTeams()
    getDepartments().then(setDepartments).catch(console.error)
    getMembers().then(setAllMembers).catch(console.error)
  }, [loadTeams])

  // ----- add / edit modal handlers -----
  const openAdd = () => {
    setEditTarget(null)
    setModalError(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (team: TeamResponse) => {
    setEditTarget(team)
    setModalError(null)
    form.setFieldsValue({ name: team.name, department_id: team.department_id })
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
        await updateTeam(editTarget.id, { name: values.name, department_id: values.department_id })
        notification.success({ message: 'チームを更新しました', placement: 'topRight' })
      } else {
        await createTeam({ name: values.name, department_id: values.department_id })
        notification.success({ message: 'チームを追加しました', placement: 'topRight' })
      }
      setModalOpen(false)
      loadTeams()
    } catch (err) {
      setModalError(extractError(err))
    } finally {
      setSubmitting(false)
    }
  }

  // ----- delete modal handlers -----
  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    setDeleteError(null)
    try {
      await deleteTeam(deleteTarget.id)
      setDeleteTarget(null)
      notification.success({ message: 'チームを削除しました', placement: 'topRight' })
      loadTeams()
    } catch (err) {
      setDeleteError(extractError(err))
    } finally {
      setDeleting(false)
    }
  }

  // ----- drawer handlers -----
  const openDrawer = (team: TeamResponse) => {
    setDrawerTeam(team)
    setAddMemberId(undefined)
    setAddMemberError(null)
    loadTeamMembers(team.id)
  }

  const handleRemoveMember = async (memberId: number) => {
    if (!drawerTeam) return
    try {
      await removeTeamMember(drawerTeam.id, memberId)
      loadTeamMembers(drawerTeam.id)
      loadTeams()
    } catch (err) {
      notification.error({ message: extractError(err), placement: 'topRight' })
    }
  }

  const handleAddMember = async () => {
    if (!drawerTeam || addMemberId === undefined) return
    setAddingMember(true)
    setAddMemberError(null)
    try {
      await addTeamMember(drawerTeam.id, addMemberId)
      setAddMemberId(undefined)
      loadTeamMembers(drawerTeam.id)
      loadTeams()
    } catch (err) {
      setAddMemberError(extractError(err))
    } finally {
      setAddingMember(false)
    }
  }

  // members not yet in the team
  const currentMemberIds = useMemo(
    () => new Set(teamMembers.map((m) => m.member_id)),
    [teamMembers],
  )
  const addableMemebers = useMemo(
    () => allMembers.filter((m) => !currentMemberIds.has(m.id)),
    [allMembers, currentMemberIds],
  )

  // ----- table columns -----
  const columns: ColumnsType<TeamResponse> = [
    { title: 'チーム名', dataIndex: 'name', key: 'name' },
    { title: '部門', dataIndex: 'department_name', key: 'department_name', width: 180 },
    {
      title: 'メンバー数',
      dataIndex: 'member_count',
      key: 'member_count',
      width: 110,
      align: 'right',
      render: (v: number) => <Tag color="blue">{v} 名</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_: unknown, record: TeamResponse) => (
        <Space>
          <Button size="small" icon={<TeamOutlined />} onClick={() => openDrawer(record)}>
            メンバー
          </Button>
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
        <Title level={3} style={{ margin: 0 }}>チームマスタ</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openAdd}>
          追加
        </Button>
      </Space>

      <Table<TeamResponse>
        columns={columns}
        dataSource={teams}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 25 }}
        size="middle"
      />

      {/* 追加・編集モーダル */}
      <Modal
        title={editTarget ? 'チームを編集' : 'チームを追加'}
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
            name="name"
            label="チーム名"
            rules={[{ required: true, message: 'チーム名を入力してください' }]}
          >
            <Input maxLength={100} placeholder="例: フロントエンドチーム" />
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
        title="チームを削除しますか？"
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
              <Text strong>{deleteTarget.name}</Text>（{deleteTarget.department_name}）を削除します。
            </Text>
            <Text type="secondary">チームを削除してもメンバーの要員データは削除されません。</Text>
            <Text type="warning">この操作は取り消せません。</Text>
            {deleteError && <Alert type="error" message={deleteError} showIcon />}
          </Space>
        )}
      </Modal>

      {/* メンバー管理ドロワー */}
      <Drawer
        title={
          drawerTeam ? (
            <Space>
              <TeamOutlined />
              <span>{drawerTeam.name}</span>
              <Text type="secondary" style={{ fontSize: 13 }}>メンバー管理</Text>
            </Space>
          ) : 'メンバー管理'
        }
        open={!!drawerTeam}
        onClose={() => setDrawerTeam(null)}
        width={480}
        extra={
          <Text type="secondary">{drawerTeam?.department_name}</Text>
        }
      >
        {/* 追加フォーム */}
        <div style={{ marginBottom: 16 }}>
          <Text strong>メンバーを追加</Text>
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <Select
              style={{ flex: 1 }}
              placeholder="追加する要員を選択"
              value={addMemberId}
              onChange={(v) => { setAddMemberId(v); setAddMemberError(null) }}
              showSearch
              optionFilterProp="label"
              options={addableMemebers.map((m) => ({
                value: m.id,
                label: `${m.employee_code} ${m.name}（${m.department_name}）`,
              }))}
              notFoundContent="追加できる要員がいません"
            />
            <Button
              type="primary"
              icon={<PlusOutlined />}
              loading={addingMember}
              disabled={addMemberId === undefined}
              onClick={handleAddMember}
            >
              追加
            </Button>
          </div>
          {addMemberError && (
            <Alert type="error" message={addMemberError} showIcon style={{ marginTop: 8 }} />
          )}
        </div>

        {/* 現在のメンバー一覧 */}
        <Text strong>現在のメンバー（{teamMembers.length} 名）</Text>
        <List
          style={{ marginTop: 8 }}
          loading={membersLoading}
          dataSource={teamMembers}
          locale={{ emptyText: 'メンバーがいません' }}
          renderItem={(member) => (
            <List.Item
              actions={[
                <Button
                  key="remove"
                  size="small"
                  danger
                  icon={<UserDeleteOutlined />}
                  onClick={() => handleRemoveMember(member.member_id)}
                >
                  削除
                </Button>,
              ]}
            >
              <List.Item.Meta
                title={`${member.employee_code} ${member.name}`}
                description={member.department_name}
              />
            </List.Item>
          )}
        />
      </Drawer>
    </div>
  )
}

export default TeamPage
