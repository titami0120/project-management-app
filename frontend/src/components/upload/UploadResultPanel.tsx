import { Alert, Table, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type { ImportSummary } from '../../types/commonTypes'
import type { CsvValidationError } from '../../types/workloadTypes'

const { Text } = Typography

interface SuccessProps {
  kind: 'success'
  summary: ImportSummary
}

interface ErrorProps {
  kind: 'error'
  errors: CsvValidationError[]
}

type Props = SuccessProps | ErrorProps

const SUMMARY_LABELS: { key: keyof ImportSummary; label: string }[] = [
  { key: 'departments', label: '部門' },
  { key: 'members', label: '要員' },
  { key: 'projects', label: 'プロジェクト' },
  { key: 'workloads', label: '工数レコード' },
]

const summaryColumns: ColumnsType<{ label: string; created: number; updated: number }> = [
  { title: 'カテゴリ', dataIndex: 'label', key: 'label' },
  { title: '新規', dataIndex: 'created', key: 'created', align: 'right' },
  { title: '更新', dataIndex: 'updated', key: 'updated', align: 'right' },
]

const errorColumns: ColumnsType<CsvValidationError> = [
  {
    title: '行番号',
    dataIndex: 'row_no',
    key: 'row_no',
    width: 90,
    render: (v: number | null) => (v == null ? 'ヘッダー' : String(v)),
  },
  { title: '列名', dataIndex: 'column', key: 'column', width: 180 },
  { title: 'エラーメッセージ', dataIndex: 'message', key: 'message' },
]

const UploadResultPanel = (props: Props) => {
  if (props.kind === 'success') {
    const rows = SUMMARY_LABELS.map(({ key, label }) => ({
      key,
      label,
      created: props.summary[key].created,
      updated: props.summary[key].updated,
    }))

    return (
      <div style={{ marginTop: 24 }}>
        <Alert
          type="success"
          message={<Text strong>アップロードが完了しました</Text>}
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Table
          columns={summaryColumns}
          dataSource={rows}
          pagination={false}
          size="small"
          bordered
        />
      </div>
    )
  }

  return (
    <div style={{ marginTop: 24 }}>
      <Alert
        type="error"
        message={`バリデーションエラーが ${props.errors.length} 件あります`}
        showIcon
        style={{ marginBottom: 16 }}
      />
      <Table
        columns={errorColumns}
        dataSource={props.errors.map((e, i) => ({ ...e, key: i }))}
        pagination={false}
        size="small"
        bordered
        scroll={{ y: 400 }}
      />
    </div>
  )
}

export default UploadResultPanel
