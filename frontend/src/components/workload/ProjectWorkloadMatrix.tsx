import { CaretDownOutlined, CaretRightOutlined } from '@ant-design/icons'
import { InputNumber, Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useMemo, useState } from 'react'
import { diffKey } from '../../hooks/useSimulation'
import type { ForecastWorkloadResponse } from '../../types/workloadTypes'

// -----------------------------------------------------------------------
// Project-centric data model
// -----------------------------------------------------------------------

type MemberEntry = {
  member_id: number
  employee_code: string
  member_name: string
  /** month key (YYYY-MM) → forecast_mm */
  cells: Record<string, number>
}

type ProjectEntry = {
  project_id: number
  wbs_tmp: string
  project_name: string
  monthly_totals: Record<string, number>
  members: MemberEntry[]
}

function buildProjectEntries(data: ForecastWorkloadResponse): ProjectEntry[] {
  const projectMap = new Map<number, ProjectEntry>()

  for (const memberRow of data.rows) {
    for (const proj of memberRow.projects) {
      if (!projectMap.has(proj.project_id)) {
        projectMap.set(proj.project_id, {
          project_id: proj.project_id,
          wbs_tmp: proj.wbs_tmp,
          project_name: proj.project_name,
          monthly_totals: {},
          members: [],
        })
      }
      const pe = projectMap.get(proj.project_id)!
      const cells: Record<string, number> = {}
      for (const [month, cell] of Object.entries(proj.cells)) {
        cells[month] = cell.forecast_mm
        pe.monthly_totals[month] = (pe.monthly_totals[month] ?? 0) + cell.forecast_mm
      }
      pe.members.push({
        member_id: memberRow.member_id,
        employee_code: memberRow.employee_code,
        member_name: memberRow.member_name,
        cells,
      })
    }
  }

  return Array.from(projectMap.values()).sort((a, b) =>
    a.wbs_tmp.localeCompare(b.wbs_tmp)
  )
}

// -----------------------------------------------------------------------
// Flat row types for the Ant Design Table
// -----------------------------------------------------------------------

type ProjectRow = {
  kind: 'project'
  key: string
  project_id: number
  wbs_tmp: string
  project_name: string
  monthly_totals: Record<string, number>
  hasMembers: boolean
}

type MemberRow = {
  kind: 'member'
  key: string
  project_id: number
  member_id: number
  employee_code: string
  member_name: string
  cells: Record<string, number>
}

type FlatRow = ProjectRow | MemberRow

function buildFlatRows(
  entries: ProjectEntry[],
  expandedIds: Set<number>,
): FlatRow[] {
  const rows: FlatRow[] = []
  for (const pe of entries) {
    rows.push({
      kind: 'project',
      key: `proj-${pe.project_id}`,
      project_id: pe.project_id,
      wbs_tmp: pe.wbs_tmp,
      project_name: pe.project_name,
      monthly_totals: pe.monthly_totals,
      hasMembers: pe.members.length > 0,
    })
    if (expandedIds.has(pe.project_id)) {
      for (const m of pe.members) {
        rows.push({
          kind: 'member',
          key: `member-${pe.project_id}-${m.member_id}`,
          project_id: pe.project_id,
          member_id: m.member_id,
          employee_code: m.employee_code,
          member_name: m.member_name,
          cells: m.cells,
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
  onCellChange?: (memberId: number, projectId: number, monthStr: string, value: number | null) => void
}

const OVER_BG = '#fff7e6'
const WBS_COL_W = 130
const NAME_COL_W = 160
const MONTH_COL_W = 85

const ProjectWorkloadMatrix = ({ data, loading, simMode, diffMap, onCellChange }: Props) => {
  const { months } = data
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set())

  const toggle = (projectId: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(projectId)) next.delete(projectId)
      else next.add(projectId)
      return next
    })
  }

  const projectEntries = useMemo(() => buildProjectEntries(data), [data])

  // シミュレーションモード時のプロジェクト月次合計を動的計算
  const computedProjectSums = useMemo<Record<string, Record<string, number>> | null>(() => {
    if (!simMode || !diffMap) return null
    const result: Record<string, Record<string, number>> = {}
    for (const pe of projectEntries) {
      const projKey = String(pe.project_id)
      result[projKey] = {}
      for (const month of months) {
        let total = 0
        for (const m of pe.members) {
          const key = diffKey(m.member_id, pe.project_id, month)
          const original = m.cells[month] ?? 0
          const eff = diffMap.has(key) ? (diffMap.get(key) ?? 0) : original
          total += eff
        }
        result[projKey][month] = total
      }
    }
    return result
  }, [simMode, diffMap, projectEntries, months])

  const flatRows = buildFlatRows(projectEntries, expandedIds)

  const labelCols: ColumnsType<FlatRow> = [
    {
      title: 'WBS仮コード',
      key: 'wbs_tmp',
      width: WBS_COL_W,
      fixed: 'left',
      onCell: (record) => (record.kind === 'member' ? { colSpan: 2 } : {}),
      render: (_, record) => {
        if (record.kind === 'project') {
          const expanded = expandedIds.has(record.project_id)
          return (
            <span>
              {record.hasMembers ? (
                <span
                  onClick={() => toggle(record.project_id)}
                  style={{ cursor: 'pointer', marginRight: 6, color: '#1677ff' }}
                >
                  {expanded ? <CaretDownOutlined /> : <CaretRightOutlined />}
                </span>
              ) : (
                <span style={{ marginRight: 18 }} />
              )}
              {record.wbs_tmp}
            </span>
          )
        }
        return (
          <span style={{ paddingLeft: 24, color: '#555' }}>
            {record.employee_code} {record.member_name}
          </span>
        )
      },
    },
    {
      title: 'プロジェクト名',
      key: 'project_name',
      width: NAME_COL_W,
      fixed: 'left',
      onCell: (record) => (record.kind === 'member' ? { colSpan: 0 } : {}),
      render: (_, record) => (record.kind === 'project' ? record.project_name : ''),
    },
  ]

  const monthCols: ColumnsType<FlatRow> = months.map((month) => ({
    title: month,
    key: month,
    width: MONTH_COL_W,
    align: 'right' as const,
    onCell: (record: FlatRow) => {
      if (record.kind !== 'project') return { style: { textAlign: 'right' as const } }
      const val = computedProjectSums
        ? (computedProjectSums[String(record.project_id)]?.[month] ?? 0)
        : (record.monthly_totals[month] ?? 0)
      return val > 1.0
        ? { style: { backgroundColor: OVER_BG, textAlign: 'right' as const } }
        : { style: { textAlign: 'right' as const } }
    },
    render: (_: unknown, record: FlatRow) => {
      if (record.kind === 'project') {
        const val = computedProjectSums
          ? computedProjectSums[String(record.project_id)]?.[month]
          : record.monthly_totals[month]
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
        record.kind === 'project' ? 'workload-member-row' : 'workload-project-row'
      }
    />
  )
}

export default ProjectWorkloadMatrix
