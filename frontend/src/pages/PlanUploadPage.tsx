import { DeleteOutlined } from '@ant-design/icons'
import { Alert, Button, Divider, Modal, Space, Typography, notification } from 'antd'
import { useState } from 'react'
import { clearMonthlyWorkloads } from '../api/workloadApi'
import CsvUploadArea from '../components/upload/CsvUploadArea'
import UploadResultPanel from '../components/upload/UploadResultPanel'
import type { CsvUploadResponse, CsvValidationError } from '../types/workloadTypes'

const { Title, Text } = Typography

type UploadResult =
  | { kind: 'success'; versionNo: number; summary: CsvUploadResponse['summary'] }
  | { kind: 'error'; errors: CsvValidationError[] }
  | null

const PlanUploadPage = () => {
  const [result, setResult] = useState<UploadResult>(null)
  const [clearModalOpen, setClearModalOpen] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [clearError, setClearError] = useState<string | null>(null)

  const handleSuccess = (res: CsvUploadResponse) => {
    notification.success({
      message: `v${res.version_no} のアップロードが完了しました`,
      placement: 'topRight',
    })
    setResult({ kind: 'success', versionNo: res.version_no, summary: res.summary })
  }

  const handleError = (errors: CsvValidationError[]) => {
    notification.error({
      message: `バリデーションエラーが ${errors.length} 件あります`,
      placement: 'topRight',
    })
    setResult({ kind: 'error', errors })
  }

  const handleClearConfirm = async () => {
    setClearing(true)
    setClearError(null)
    try {
      const res = await clearMonthlyWorkloads()
      setClearModalOpen(false)
      setResult(null)
      notification.success({
        message: 'データクリア完了',
        description: `${res.deleted_count.toLocaleString()} 件のレコードを削除しました。`,
        placement: 'topRight',
        duration: 5,
      })
    } catch {
      setClearError('データクリアに失敗しました。サーバーログを確認してください。')
    } finally {
      setClearing(false)
    }
  }

  return (
    <div style={{ maxWidth: 700, margin: '0 auto', padding: '24px 0' }}>
      <Title level={3}>計画工数CSVアップロード</Title>
      <CsvUploadArea onSuccess={handleSuccess} onError={handleError} />
      {result && <UploadResultPanel {...result} />}

      <Divider />

      <div>
        <Title level={5} style={{ color: '#cf1322', marginBottom: 8 }}>データクリア</Title>
        <p style={{ color: '#666', marginBottom: 12 }}>
          月次工数データの全レコードを削除します。マスタデータ（要員・プロジェクト等）は削除されません。
        </p>
        <Button
          danger
          icon={<DeleteOutlined />}
          onClick={() => { setClearError(null); setClearModalOpen(true) }}
        >
          データクリア
        </Button>
      </div>

      <Modal
        title="データをクリアしますか？"
        open={clearModalOpen}
        onOk={handleClearConfirm}
        onCancel={() => { setClearModalOpen(false); setClearError(null) }}
        okText="クリアする"
        okButtonProps={{ danger: true, loading: clearing }}
        cancelButtonProps={{ disabled: clearing }}
        cancelText="キャンセル"
        closable={!clearing}
        maskClosable={!clearing}
        destroyOnHidden
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>月次工数（monthly_workloads）の全レコードを削除します。</Text>
          <Text type="warning">この操作は取り消せません。</Text>
          {clearError && (
            <Alert type="error" message={clearError} showIcon />
          )}
        </Space>
      </Modal>
    </div>
  )
}

export default PlanUploadPage
