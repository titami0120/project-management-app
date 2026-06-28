import { Button, Form, Select, Typography, App } from 'antd'
import { useEffect, useState } from 'react'
import { getDepartments } from '../api/departmentApi'
import type { DepartmentResponse } from '../types/projectTypes'
import {
  type AppSettings,
  DEFAULT_SETTINGS,
  loadSettings,
  saveSettings,
} from '../hooks/useSettings'

const { Title } = Typography

const YEARS = [2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030]
const MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

const SettingsPage = () => {
  const { message } = App.useApp()
  const [departments, setDepartments] = useState<DepartmentResponse[]>([])
  const [settings, setSettings] = useState<AppSettings>(loadSettings)

  useEffect(() => {
    getDepartments().then(setDepartments).catch(console.error)
  }, [])

  const update = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  const handleSave = () => {
    saveSettings(settings)
    message.success('設定を保存しました')
  }

  const handleReset = () => {
    setSettings({ ...DEFAULT_SETTINGS })
    saveSettings({ ...DEFAULT_SETTINGS })
    message.info('設定をリセットしました')
  }

  return (
    <div style={{ maxWidth: 480 }}>
      <Title level={3}>設定</Title>

      <Form layout="vertical">
        <Form.Item label="デフォルト部門">
          <Select
            value={settings.defaultDeptId}
            onChange={(v) => update('defaultDeptId', v)}
            placeholder="全部門（指定なし）"
            allowClear
            onClear={() => update('defaultDeptId', undefined)}
            style={{ width: '100%' }}
          >
            {departments.map((d) => (
              <Select.Option key={d.id} value={d.id}>
                {d.name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item label="デフォルト開始年月">
          <Select
            value={settings.defaultFromYear}
            onChange={(v) => update('defaultFromYear', v)}
            style={{ width: 100, marginRight: 8 }}
          >
            {YEARS.map((y) => (
              <Select.Option key={y} value={y}>{y}年</Select.Option>
            ))}
          </Select>
          <Select
            value={settings.defaultFromMonth}
            onChange={(v) => update('defaultFromMonth', v)}
            style={{ width: 80 }}
          >
            {MONTHS.map((m) => (
              <Select.Option key={m} value={m}>{m}月</Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item label="デフォルト終了年月">
          <Select
            value={settings.defaultToYear}
            onChange={(v) => update('defaultToYear', v)}
            style={{ width: 100, marginRight: 8 }}
          >
            {YEARS.map((y) => (
              <Select.Option key={y} value={y}>{y}年</Select.Option>
            ))}
          </Select>
          <Select
            value={settings.defaultToMonth}
            onChange={(v) => update('defaultToMonth', v)}
            style={{ width: 80 }}
          >
            {MONTHS.map((m) => (
              <Select.Option key={m} value={m}>{m}月</Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item>
          <Button type="primary" onClick={handleSave} style={{ marginRight: 8 }}>
            保存
          </Button>
          <Button onClick={handleReset}>リセット</Button>
        </Form.Item>
      </Form>
    </div>
  )
}

export default SettingsPage
