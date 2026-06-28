import { notification, Typography } from 'antd'
import { useState } from 'react'
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

  const handleSuccess = (res: CsvUploadResponse) => {
    notification.success({
      message: `バージョン ${res.version_no} のアップロードが完了しました`,
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

  return (
    <div style={{ maxWidth: 700, margin: '0 auto', padding: '24px 0' }}>
      <Title level={3}>計画工数CSVアップロード</Title>
      <CsvUploadArea onSuccess={handleSuccess} onError={handleError} />
      {result && <UploadResultPanel {...result} />}
    </div>
  )
}

export default PlanUploadPage
