import { DeleteOutlined } from '@ant-design/icons'
import { Button, Divider, Modal, Typography, notification } from 'antd'
import { useState } from 'react'
import { clearMonthlyWorkloads } from '../api/workloadApi'
import CsvUploadArea from '../components/upload/CsvUploadArea'
import UploadResultPanel from '../components/upload/UploadResultPanel'
import type { CsvUploadResponse, CsvValidationError } from '../types/workloadTypes'

const { Title } = Typography

type UploadResult =
  | { kind: 'success'; versionNo: number; summary: CsvUploadResponse['summary'] }
  | { kind: 'error'; errors: CsvValidationError[] }
  | null

const PlanUploadPage = () => {
  const [result, setResult] = useState<UploadResult>(null)
  const [clearing, setClearing] = useState(false)

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

  const handleClear = () => {
    Modal.confirm({
      title: 'データをクリアしますか？',
      content: '月次工数（monthly_workloads）の全レコードを削除します。この操作は取り消せません。',
      okText: 'クリアする',
      okType: 'danger',
      cancelText: 'キャンセル',
      onOk: async () => {
        setClearing(true)
        try {
          const res = await clearMonthlyWorkloads()
          notification.success({
            message: 'データクリア完了',
            description: `${res.deleted_count.toLocaleString()} 件のレコードを削除しました。`,
            placement: 'topRight',
          })
          setResult(null)
        } catch {
          notification.error({ message: 'データクリアに失敗しました', placement: 'topRight' })
          throw new Error('clear failed')
        } finally {
          setClearing(false)
        }
      },
    })
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
          月次工数データ（monthly_workloads）の全レコードを削除します。マスタデータ（要員・プロジェクト等）は削除されません。
        </p>
        <Button
          danger
          icon={<DeleteOutlined />}
          loading={clearing}
          onClick={handleClear}
        >
          データクリア
        </Button>
      </div>
    </div>
  )
}

export default PlanUploadPage
