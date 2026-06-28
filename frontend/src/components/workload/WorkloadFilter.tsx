import { Button, Form, Select } from 'antd'
import { useEffect, useState } from 'react'
import { getDepartments } from '../../api/departmentApi'
import type { DepartmentResponse } from '../../types/projectTypes'
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

const WorkloadFilter = ({ onFetch, loading }: Props) => {
  const defaults = loadSettings()
  const [departments, setDepartments] = useState<DepartmentResponse[]>([])
  const [deptId, setDeptId] = useState<number | undefined>(defaults.defaultDeptId)
  const [fromYear, setFromYear] = useState(defaults.defaultFromYear)
  const [fromMonth, setFromMonth] = useState(defaults.defaultFromMonth)
  const [toYear, setToYear] = useState(defaults.defaultToYear)
  const [toMonth, setToMonth] = useState(defaults.defaultToMonth)

  useEffect(() => {
    getDepartments().then(setDepartments).catch(console.error)
  }, [])

  const handleFetch = () => {
    onFetch({ from: fmt(fromYear, fromMonth), to: fmt(toYear, toMonth), dept_id: deptId })
  }

  return (
    <Form layout="inline" style={{ marginBottom: 16, rowGap: 8 }}>
      <Form.Item label="部門">
        <Select
          value={deptId}
          onChange={setDeptId}
          placeholder="全部門"
          allowClear
          style={{ width: 150 }}
        >
          {departments.map((d) => (
            <Select.Option key={d.id} value={d.id}>
              {d.name}
            </Select.Option>
          ))}
        </Select>
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
        <Button type="primary" onClick={handleFetch} loading={loading}>
          表示
        </Button>
      </Form.Item>
    </Form>
  )
}

export default WorkloadFilter
