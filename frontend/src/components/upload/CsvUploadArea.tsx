import { InboxOutlined } from '@ant-design/icons'
import { Alert, Button, Spin, Upload } from 'antd'
import type { RcFile } from 'antd/es/upload'
import axios from 'axios'
import { useState } from 'react'
import { uploadPlanCsv } from '../../api/workloadApi'
import type { CsvUploadResponse, CsvValidationError } from '../../types/workloadTypes'

interface Props {
  onSuccess?: (result: CsvUploadResponse) => void
  onError?: (errors: CsvValidationError[]) => void
}

const CsvUploadArea = ({ onSuccess, onError }: Props) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [extensionError, setExtensionError] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)

  const beforeUpload = (file: RcFile): false => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setExtensionError(true)
      setSelectedFile(null)
    } else {
      setExtensionError(false)
      setSelectedFile(file)
    }
    return false
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    setUploading(true)
    setServerError(null)
    try {
      const result = await uploadPlanCsv(selectedFile)
      onSuccess?.(result)
      setSelectedFile(null)
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (!err.response) {
          // レスポンスなし = サーバー未起動または CORS エラー
          setServerError(
            'バックエンドサーバーに接続できません（http://localhost:8000）。サーバーが起動しているか確認してください。'
          )
        } else if (err.response.status === 422) {
          // FastAPI は {"detail": {"errors": [...]}} で返す
          const body = err.response.data as { detail: { errors: CsvValidationError[] } }
          onError?.(body.detail.errors)
        } else if (err.response.status === 500) {
          setServerError(
            'サーバーエラーが発生しました。CSVのエンコーディング（UTF-8 または Shift-JIS）やフォーマットを確認してください。'
          )
        } else {
          setServerError(`アップロードに失敗しました（HTTP ${err.response.status}）`)
        }
      } else {
        setServerError('予期しないエラーが発生しました。')
      }
    } finally {
      setUploading(false)
    }
  }

  const fileList = selectedFile
    ? [{ uid: '-1', name: selectedFile.name, status: 'done' as const }]
    : []

  return (
    <Spin spinning={uploading} tip="アップロード中...">
      <Upload.Dragger
        accept=".csv"
        beforeUpload={beforeUpload}
        fileList={fileList}
        showUploadList={selectedFile !== null}
        disabled={uploading}
        onRemove={() => {
          setSelectedFile(null)
          setExtensionError(false)
        }}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">クリックまたはドラッグ&amp;ドロップでファイルを選択</p>
        <p className="ant-upload-hint">計画工数CSVファイル（.csv）のみ対応</p>
      </Upload.Dragger>

      {extensionError && (
        <Alert
          type="error"
          message="CSVファイル（.csv）を選択してください"
          showIcon
          style={{ marginTop: 8 }}
        />
      )}

      {serverError && (
        <Alert
          type="error"
          message={serverError}
          showIcon
          style={{ marginTop: 8 }}
        />
      )}

      <Button
        type="primary"
        onClick={handleUpload}
        disabled={!selectedFile || uploading}
        loading={uploading}
        block
        style={{ marginTop: 16 }}
      >
        アップロード
      </Button>
    </Spin>
  )
}

export default CsvUploadArea
