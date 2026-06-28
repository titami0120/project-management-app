import { Button, Form, Select } from 'antd'
import { useEffect, useState } from 'react'
import { getProjects } from '../../api/projectApi'
import type { ProjectResponse } from '../../types/projectTypes'
import type { ForecastQueryParams } from '../../types/workloadTypes'
import { loadSettings } from '../../hooks/useSettings'

const YEARS = [2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030]
const MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

const fmt = (year: number, month: number) =>
  `${year}-${String(month).padStart(2, '0')}`

interface Props {
  onFetch: (params: ForecastQueryParams) => void
  loading: boolean
}

const ProjectWorkloadFilter = ({ onFetch, loading }: Props) => {
  const defaults = loadSettings()
  const [projects, setProjects] = useState<ProjectResponse[]>([])
  const [projectId, setProjectId] = useState<number | undefined>()
  const [fromYear, setFromYear] = useState(defaults.defaultFromYear)
  const [fromMonth, setFromMonth] = useState(defaults.defaultFromMonth)
  const [toYear, setToYear] = useState(defaults.defaultToYear)
  const [toMonth, setToMonth] = useState(defaults.defaultToMonth)

  useEffect(() => {
    getProjects().then(setProjects).catch(console.error)
  }, [])

  const handleFetch = () => {
    onFetch({
      from: fmt(fromYear, fromMonth),
      to: fmt(toYear, toMonth),
      project_id: projectId,
    })
  }

  return (
    <Form layout="inline" style={{ marginBottom: 16, rowGap: 8 }}>
      <Form.Item label="プロジェクト">
        <Select
          value={projectId}
          onChange={setProjectId}
          placeholder="プロジェクトを検索..."
          allowClear
          onClear={() => setProjectId(undefined)}
          style={{ width: 280 }}
          showSearch
          optionFilterProp="label"
          options={projects.map((p) => ({
            value: p.id,
            label: `${p.wbs_tmp} ${p.name}`,
          }))}
        />
      </Form.Item>

      <Form.Item label="開始年月">
        <Select value={fromYear} onChange={setFromYear} style={{ width: 88 }}>
          {YEARS.map((y) => (
            <Select.Option key={y} value={y}>{y}年</Select.Option>
          ))}
        </Select>
        <Select value={fromMonth} onChange={setFromMonth} style={{ width: 68, marginLeft: 4 }}>
          {MONTHS.map((m) => (
            <Select.Option key={m} value={m}>{m}月</Select.Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item label="終了年月">
        <Select value={toYear} onChange={setToYear} style={{ width: 88 }}>
          {YEARS.map((y) => (
            <Select.Option key={y} value={y}>{y}年</Select.Option>
          ))}
        </Select>
        <Select value={toMonth} onChange={setToMonth} style={{ width: 68, marginLeft: 4 }}>
          {MONTHS.map((m) => (
            <Select.Option key={m} value={m}>{m}月</Select.Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          onClick={handleFetch}
          loading={loading}
          disabled={projectId === undefined}
        >
          表示
        </Button>
      </Form.Item>
    </Form>
  )
}

export default ProjectWorkloadFilter
