import { Form, Input, InputNumber, Modal } from 'antd'
import { useEffect, useState } from 'react'
import { updateProject } from '../../api/projectApi'
import type { ProjectResponse } from '../../types/projectTypes'

type EditFormValues = {
  name: string
  code?: string
  display_order?: number | null
}

interface Props {
  project: ProjectResponse | null
  onClose: () => void
  onUpdated: () => void
}

const ProjectEditModal = ({ project, onClose, onUpdated }: Props) => {
  const [form] = Form.useForm<EditFormValues>()
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (project) {
      form.setFieldsValue({
        name: project.name,
        code: project.code ?? undefined,
        display_order: project.display_order ?? undefined,
      })
    }
  }, [form, project])

  const handleOk = async () => {
    let values: EditFormValues
    try {
      values = await form.validateFields()
    } catch {
      return
    }
    if (!project) return
    setSubmitting(true)
    try {
      await updateProject(project.id, {
        name: values.name,
        code: values.code || undefined,
        display_order: values.display_order ?? undefined,
      })
      onUpdated()
    } catch (e) {
      console.error(e)
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
      title="プロジェクト編集"
      open={project !== null}
      onOk={handleOk}
      onCancel={handleCancel}
      okText="保存"
      cancelText="キャンセル"
      confirmLoading={submitting}
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item
          name="name"
          label="WBS名称"
          rules={[{ required: true, message: 'WBS名称を入力してください' }]}
        >
          <Input />
        </Form.Item>
        <Form.Item name="code" label="WBSコード">
          <Input />
        </Form.Item>
        <Form.Item name="display_order" label="表示順">
          <InputNumber<number> min={0} style={{ width: '100%' }} />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default ProjectEditModal
