import axios from 'axios'
import { Form, Input, Modal, Select } from 'antd'
import { useEffect, useState } from 'react'
import { createMatter } from '../../api/matterApi'
import { getMembers } from '../../api/memberApi'
import type { MatterCreateRequest } from '../../types/matterTypes'
import type { MemberResponse } from '../../types/projectTypes'

const STATUSES = ['計画中', '進行中', '完了', '中止']

interface Props {
  open: boolean
  onClose: () => void
  onCreated: () => void
}

const MatterFormModal = ({ open, onClose, onCreated }: Props) => {
  const [form] = Form.useForm<MatterCreateRequest>()
  const [members, setMembers] = useState<MemberResponse[]>([])
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (open) {
      getMembers().then(setMembers).catch(console.error)
    }
  }, [open])

  const handleOk = async () => {
    let values: MatterCreateRequest
    try {
      values = await form.validateFields()
    } catch {
      return
    }
    setSubmitting(true)
    try {
      await createMatter(values)
      form.resetFields()
      onCreated()
    } catch (e) {
      if (axios.isAxiosError(e) && e.response?.status === 409) {
        form.setFields([{ name: 'code', errors: ['案件コードが重複しています'] }])
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    onClose()
  }

  return (
    <Modal
      title="新規案件登録"
      open={open}
      onOk={handleOk}
      onCancel={handleCancel}
      okText="登録"
      cancelText="キャンセル"
      confirmLoading={submitting}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ status: '計画中' }}
        style={{ marginTop: 16 }}
      >
        <Form.Item
          name="name"
          label="案件名"
          rules={[{ required: true, message: '案件名を入力してください' }]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          name="code"
          label="案件コード"
          rules={[{ required: true, message: '案件コードを入力してください' }]}
        >
          <Input />
        </Form.Item>
        <Form.Item name="client_name" label="顧客名">
          <Input />
        </Form.Item>
        <Form.Item name="pm_member_id" label="PM">
          <Select placeholder="選択してください" allowClear>
            {members.map((m) => (
              <Select.Option key={m.id} value={m.id}>
                {m.name}（{m.employee_code}）
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
        <Form.Item name="status" label="ステータス">
          <Select>
            {STATUSES.map((s) => (
              <Select.Option key={s} value={s}>
                {s}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default MatterFormModal
