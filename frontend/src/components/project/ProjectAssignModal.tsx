import { Form, Modal, Select, Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type { Key } from 'react'
import { useEffect, useState } from 'react'
import { getMatters } from '../../api/matterApi'
import { assignProjectMatter, getProjects } from '../../api/projectApi'
import type { MatterResponse } from '../../types/matterTypes'
import type { ProjectResponse } from '../../types/projectTypes'

interface Props {
  open: boolean
  onClose: () => void
  onAssigned: () => void
}

const ProjectAssignModal = ({ open, onClose, onAssigned }: Props) => {
  const [unassigned, setUnassigned] = useState<ProjectResponse[]>([])
  const [matters, setMatters] = useState<MatterResponse[]>([])
  const [selectedMatterId, setSelectedMatterId] = useState<number | undefined>()
  const [selectedRowKeys, setSelectedRowKeys] = useState<Key[]>([])
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (open) {
      Promise.all([getProjects(true), getMatters()])
        .then(([projects, mattersData]) => {
          setUnassigned(projects)
          setMatters(mattersData)
          setSelectedRowKeys([])
          setSelectedMatterId(undefined)
        })
        .catch(console.error)
    }
  }, [open])

  const handleOk = async () => {
    if (!selectedMatterId || selectedRowKeys.length === 0) return
    setSubmitting(true)
    try {
      await Promise.all(
        selectedRowKeys.map((key) =>
          assignProjectMatter(Number(key), { matter_id: selectedMatterId }),
        ),
      )
      onAssigned()
    } catch (e) {
      console.error(e)
    } finally {
      setSubmitting(false)
    }
  }

  const columns: ColumnsType<ProjectResponse> = [
    { title: 'WBS仮コード', dataIndex: 'wbs_tmp', key: 'wbs_tmp', width: 120 },
    { title: 'WBS名称', dataIndex: 'name', key: 'name', ellipsis: true },
  ]

  return (
    <Modal
      title="案件紐づけ"
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      okText="紐づける"
      cancelText="キャンセル"
      confirmLoading={submitting}
      okButtonProps={{ disabled: !selectedMatterId || selectedRowKeys.length === 0 }}
      width={640}
    >
      <Form layout="vertical" style={{ marginTop: 16, marginBottom: 16 }}>
        <Form.Item label="紐づける案件" required>
          <Select
            value={selectedMatterId}
            onChange={setSelectedMatterId}
            placeholder="案件を選択してください"
            style={{ width: '100%' }}
          >
            {matters.map((m) => (
              <Select.Option key={m.id} value={m.id}>
                [{m.code}] {m.name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
      </Form>
      <Table<ProjectResponse>
        columns={columns}
        dataSource={unassigned}
        rowKey="id"
        size="small"
        pagination={false}
        rowSelection={{ selectedRowKeys, onChange: setSelectedRowKeys }}
        scroll={{ y: 280 }}
        locale={{ emptyText: '案件未紐づきのプロジェクトはありません' }}
      />
    </Modal>
  )
}

export default ProjectAssignModal
