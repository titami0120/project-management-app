import { CaretDownOutlined, CaretRightOutlined } from '@ant-design/icons'
import { InputNumber, Table, Tooltip } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useState } from 'react'
import type { ForecastWorkloadResponse } from '../../types/workloadTypes'
import { diffKey } from '../../hooks/useSimulation'

// -----------------------------------------------------------------------
// Flat row types
// -----------------------------------------------------------------------

type MemberRow = {
  kind: 'member'
  key: string
  member_id: number
  employee_code: string
  member_name: string
  monthly_sums: Record<string, number>
  hasProjects: boolean
}

type ProjectRow = {
  kind: 'project'
  key: string
  member_id: number
  project_id: number
  project_name: string
  wbs_tmp: string
  cells: Record<string, number>
}

type FlatRow = MemberRow | ProjectRow

const buildFlatRows = (
  data: ForecastWorkloadResponse,
  expandedIds: Set<number>,
): FlatRow[] => {
  const rows: FlatRow[] = []
  for (const r of data.rows) {
    rows.push({
      kind: 'member',
      key: `member-${r.member_id}`,
      member_id: r.member_id,
      employee_code: r.employee_code,
      member_name: r.member_name,
      monthly_sums: r.monthly_sums,
      hasProjects: r.projects.length > 0,
    })
    if (expandedIds.has(r.member_id)) {
      for (const p of r.projects) {
        const cells: Record<string, number> = {}
        for (const [month, cell] of Object.entries(p.cells)) {
          cells[month] = cell.forecast_mm
        }
        rows.push({
          kind: 'project',
          key: `proj-${r.member_id}-${p.project_id}`,
          member_id: r.member_id,
          project_id: p.project_id,
          project_name: p.project_name,
          wbs_tmp: p.wbs_tmp,
          cells,
        })
      }
    }
  }
  return rows
}

// -----------------------------------------------------------------------
// Component
// -----------------------------------------------------------------------

interface Props {
  data: ForecastWorkloadResponse
  loading?: boolean
  simMode?: boolean
  diffMap?: Map<string, number | null>
  computedSums?: Record<string, Record<string, number>>
  onCellChange?: (memberId: number, projectId: number, monthStr: string, value: number | null) => void
  onProjectClick?: (projectId: number, projectName: string, wbsTmp: string) => void
}

const OVER_BG = '#fff7e6'
const CODE_COL_W = 110
const NAME_COL_W = 120
const MONTH_COL_W = 85

const WorkloadMatrix = ({ data, loading, simMode, diffMap, computedSums, onCellChange, onProjectClick }: Props) => {
  const { months } = data
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set())

  const toggle = (memberId: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(memberId)) next.delete(memberId)
      else next.add(memberId)
      return next
    })
  }

  const flatRows = buildFlatRows(data, expandedIds)

  const labelCols: ColumnsType<FlatRow> = [
    {
      title: '要員コード',
      key: 'employee_code',
      width: CODE_COL_W,
      fixed: 'left',
      onCell: (record) => (record.kind === 'project' ? { colSpan: 2 } : {}),
      render: (_, record) => {
        if (record.kind === 'member') {
          const expanded = expandedIds.has(record.member_id)
          return (
            <span>
              {record.hasProjects ? (
                <span
                  onClick={() => toggle(record.member_id)}
                  style={{ cursor: 'pointer', marginRight: 6, color: '#1677ff' }}
                >
                  {expanded ? <CaretDownOutlined /> : <CaretRightOutlined />}
                </span>
              ) : (
                <span style={{ marginRight: 18 }} />
              )}
              {record.employee_code}
            </span>
          )
        }
        return (
          <Tooltip title={`${record.project_name} ${record.wbs_tmp}`}>
            <span
              onClick={() => onProjectClick?.(record.project_id, record.project_name, record.wbs_tmp)}
              style={{
                paddingLeft: 24,
                display: 'block',
                overflow: 'hidden',
                whiteSpace: 'nowrap',
                textOverflow: 'ellipsis',
                color: onProjectClick ? '#1677ff' : '#555',
                cursor: onProjectClick ? 'pointer' : 'default',
              }}
            >
              {record.project_name} {record.wbs_tmp}
            </span>
          </Tooltip>
        )
      },
    },
    {
      title: '要員名',
      key: 'member_name',
      width: NAME_COL_W,
      fixed: 'left',
      onCell: (record) => (record.kind === 'project' ? { colSpan: 0 } : {}),
      render: (_, record) => (record.kind === 'member' ? record.member_name : ''),
    },
  ]

  const monthCols: ColumnsType<FlatRow> = months.map((month) => ({
    title: month,
    key: month,
    width: MONTH_COL_W,
    align: 'right' as const,
    onCell: (record: FlatRow) => {
      if (record.kind !== 'member') return { style: { textAlign: 'right' as const } }
      const val = simMode && computedSums
        ? (computedSums[String(record.member_id)]?.[month] ?? 0)
        : (record.monthly_sums[month] ?? 0)
      return val > 1.0
        ? { style: { backgroundColor: OVER_BG, textAlign: 'right' as const } }
        : { style: { textAlign: 'right' as const } }
    },
    render: (_: unknown, record: FlatRow) => {
      if (record.kind === 'member') {
        const val = simMode && computedSums
          ? computedSums[String(record.member_id)]?.[month]
          : record.monthly_sums[month]
        return val !== undefined ? <strong>{val.toFixed(2)}</strong> : '-'
      }
      if (simMode && onCellChange) {
        const key = diffKey(record.member_id, record.project_id, month)
        const simVal = diffMap?.has(key) ? diffMap.get(key) : (record.cells[month] ?? null)
        return (
          <InputNumber<number>
            value={simVal ?? undefined}
            min={0}
            step={0.1}
            precision={2}
            size="small"
            style={{ width: 72 }}
            onChange={(val) => onCellChange(record.member_id, record.project_id, month, val)}
          />
        )
      }
      const val = record.cells[month]
      return val !== undefined ? val.toFixed(2) : '-'
    },
  }))

  return (
    <Table<FlatRow>
      columns={[...labelCols, ...monthCols]}
      dataSource={flatRows}
      loading={loading}
      pagination={false}
      size="small"
      bordered
      scroll={{ x: 'max-content' }}
      rowClassName={(record) =>
        record.kind === 'member' ? 'workload-member-row' : 'workload-project-row'
      }
    />
  )
}

export default WorkloadMatrix
