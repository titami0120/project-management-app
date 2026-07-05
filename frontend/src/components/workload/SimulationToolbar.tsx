import { CloudDownloadOutlined, HistoryOutlined, SaveOutlined, UndoOutlined } from '@ant-design/icons'
import { Button, Space, Switch, Typography } from 'antd'
import { useState } from 'react'
import { createForecastVersion } from '../../api/forecastVersionApi'
import { notification } from 'antd'
import SaveVersionModal from './SaveVersionModal'

interface Props {
  simMode: boolean
  onToggle: (val: boolean) => void
  onSave: () => void
  onReset: () => void
  onDownload: () => void
  saving?: boolean
  resetting?: boolean
  hasDiff?: boolean
  canDownload?: boolean
}

const SimulationToolbar = ({
  simMode,
  onToggle,
  onSave,
  onReset,
  onDownload,
  saving,
  resetting,
  hasDiff,
  canDownload,
}: Props) => {
  const [modalOpen, setModalOpen] = useState(false)
  const [versionSaving, setVersionSaving] = useState(false)

  const handleSaveVersion = async (name: string, description: string | undefined) => {
    setVersionSaving(true)
    try {
      const result = await createForecastVersion({ name, description })
      notification.success({
        message: `v${result.version_no}「${result.name}」として保存しました`,
        placement: 'topRight',
      })
      setModalOpen(false)
    } catch {
      notification.error({ message: 'バージョンの保存に失敗しました', placement: 'topRight' })
    } finally {
      setVersionSaving(false)
    }
  }

  return (
    <>
      <Space wrap style={{ marginBottom: 16 }}>
        <Typography.Text strong>シミュレーションモード</Typography.Text>
        <Switch checked={simMode} onChange={onToggle} checkedChildren="ON" unCheckedChildren="OFF" />
        {simMode && (
          <>
            <Typography.Text type="warning">セルを編集して工数をシミュレートできます</Typography.Text>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              loading={saving}
              disabled={!hasDiff}
              onClick={onSave}
            >
              保存
            </Button>
            <Button icon={<UndoOutlined />} loading={resetting} danger onClick={onReset}>
              リセット
            </Button>
          </>
        )}
        {canDownload && (
          <>
            <Button icon={<CloudDownloadOutlined />} onClick={onDownload}>
              CSVダウンロード
            </Button>
            <Button icon={<HistoryOutlined />} onClick={() => setModalOpen(true)}>
              バージョンとして保存
            </Button>
          </>
        )}
      </Space>
      <SaveVersionModal
        open={modalOpen}
        saving={versionSaving}
        onOk={handleSaveVersion}
        onCancel={() => setModalOpen(false)}
      />
    </>
  )
}

export default SimulationToolbar
