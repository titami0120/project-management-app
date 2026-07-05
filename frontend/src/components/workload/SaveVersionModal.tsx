import { Form, Input, Modal } from 'antd'
import { useState } from 'react'

interface FormValues {
  name: string
  description?: string
}

interface Props {
  open: boolean
  saving: boolean
  onOk: (name: string, description: string | undefined) => void
  onCancel: () => void
}

const SaveVersionModal = ({ open, saving, onOk, onCancel }: Props) => {
  const [form] = Form.useForm<FormValues>()
  const [submitting, setSubmitting] = useState(false)

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      setSubmitting(true)
      await onOk(values.name, values.description || undefined)
      form.resetFields()
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    onCancel()
  }

  return (
    <Modal
      title="バージョンとして保存"
      open={open}
      onOk={handleOk}
      onCancel={handleCancel}
      okText="保存"
      cancelText="キャンセル"
      confirmLoading={saving || submitting}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item
          name="name"
          label="バージョン名"
          rules={[{ required: true, message: 'バージョン名を入力してください' }]}
        >
          <Input placeholder="例: 2026年度 初版" maxLength={100} />
        </Form.Item>
        <Form.Item name="description" label="詳細">
          <Input.TextArea
            placeholder="変更内容や備考を入力（任意）"
            rows={4}
            maxLength={500}
            showCount
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default SaveVersionModal
