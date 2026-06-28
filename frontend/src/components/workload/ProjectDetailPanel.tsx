import { CloseOutlined } from '@ant-design/icons'
import { Button, InputNumber, Table, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { diffKey } from '../../hooks/useSimulation'
import type { ForecastMemberRow, ForecastWorkloadResponse } from '../../types/workloadTypes'

interface Props {
  projectId: number
  projectName: string
  wbsTmp: string
  data: ForecastWorkloadResponse
  loading: boolean
  simMode?: boolean
  diffMap?: Map<string, number | null>
  onCellChange?: (memberId: number, projectId: number, monthStr: string, value: number | null) => void
  onClose: () => void
}

const MONTH_COL_W = 85

const ProjectDetailPanel = ({
  projectId,
  projectName,
  wbsTmp,
  data,
  loading,
  simMode,
  diffMap,
  onCellChange,
  onClose,
}: Props) => {
  const { months, rows } = data

  const columns: ColumnsType<ForecastMemberRow> = [
    {
      title: '要員コード',
      dataIndex: 'employee_code',
      key: 'employee_code',
      width: 100,
      fixed: 'left',
    },
    {
      title: '要員名',
      dataIndex: 'member_name',
      key: 'member_name',
      width: 120,
      fixed: 'left',
    },
    ...months.map((month) => ({
      title: month,
      key: month,
      width: MONTH_COL_W,
      align: 'right' as const,
      render: (_: unknown, record: ForecastMemberRow) => {
        const original = record.monthly_sums[month] ?? null
        if (simMode && onCellChange) {
          const key = diffKey(record.member_id, projectId, month)
          const simVal = diffMap?.has(key) ? diffMap.get(key) : original
          return (
            <InputNumber<number>
              value={simVal ?? undefined}
              min={0}
              step={0.1}
              precision={2}
              size="small"
              style={{ width: 72 }}
              onChange={(val) => onCellChange(record.member_id, projectId, month, val)}
            />
          )
        }
        return original !== null ? original.toFixed(2) : '-'
      },
    })),
  ]

  return (
    <div
      style={{
        marginTop: 24,
        border: '1px solid #d9d9d9',
        borderRadius: 8,
        padding: 16,
        background: '#fafafa',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
        <Typography.Text strong style={{ fontSize: 14, flex: 1 }}>
          {projectName}
          <Typography.Text type="secondary" style={{ marginLeft: 8, fontWeight: 'normal' }}>
            {wbsTmp}
          </Typography.Text>
          　参加要員一覧
        </Typography.Text>
        <Button type="text" icon={<CloseOutlined />} size="small" onClick={onClose} />
      </div>
      <Table<ForecastMemberRow>
        columns={columns}
        dataSource={rows}
        rowKey="member_id"
        loading={loading}
        pagination={false}
        size="small"
        bordered
        scroll={{ x: 'max-content' }}
        summary={(pageData) => {
          const totals: Record<string, number> = {}
          for (const month of months) {
            let sum = 0
            for (const record of pageData) {
              if (simMode && diffMap) {
                const key = diffKey(record.member_id, projectId, month)
                const val = diffMap.has(key)
                  ? (diffMap.get(key) ?? 0)
                  : (record.monthly_sums[month] ?? 0)
                sum += val
              } else {
                sum += record.monthly_sums[month] ?? 0
              }
            }
            totals[month] = sum
          }
          return (
            <Table.Summary.Row style={{ background: '#fafafa' }}>
              <Table.Summary.Cell index={0} colSpan={2}>
                <strong>合計</strong>
              </Table.Summary.Cell>
              {months.map((month, i) => (
                <Table.Summary.Cell key={month} index={i + 2} align="right">
                  <strong>{totals[month].toFixed(2)}</strong>
                </Table.Summary.Cell>
              ))}
            </Table.Summary.Row>
          )
        }}
      />
    </div>
  )
}

export default ProjectDetailPanel
