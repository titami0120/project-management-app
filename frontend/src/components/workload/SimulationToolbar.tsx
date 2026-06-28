import { CloudDownloadOutlined, SaveOutlined, UndoOutlined } from '@ant-design/icons'
import { Button, Space, Switch, Typography } from 'antd'

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
}: Props) => (
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
      <Button icon={<CloudDownloadOutlined />} onClick={onDownload}>
        CSVダウンロード
      </Button>
    )}
  </Space>
)

export default SimulationToolbar
