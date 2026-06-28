import { Alert, Divider, Typography, notification } from 'antd'
import { useCallback } from 'react'
import { downloadForecastCsv } from '../api/workloadApi'
import SimulationToolbar from '../components/workload/SimulationToolbar'
import ProjectWorkloadFilter from '../components/workload/ProjectWorkloadFilter'
import ProjectWorkloadMatrix from '../components/workload/ProjectWorkloadMatrix'
import useSimulation from '../hooks/useSimulation'
import useWorkloadMatrix from '../hooks/useWorkloadMatrix'

const { Title } = Typography

const ProjectWorkloadPage = () => {
  const { data, loading, error, fetchMatrix, currentParams } = useWorkloadMatrix()
  const {
    simMode,
    setSimMode,
    diffMap,
    updateCell,
    saving,
    resetting,
    saveToServer,
    resetFromServer,
  } = useSimulation(data)

  const handleSave = useCallback(() => {
    if (!currentParams) return
    saveToServer(() => fetchMatrix(currentParams))
  }, [saveToServer, fetchMatrix, currentParams])

  const handleReset = useCallback(() => {
    if (!currentParams) return
    resetFromServer(() => fetchMatrix(currentParams))
  }, [resetFromServer, fetchMatrix, currentParams])

  const handleDownload = useCallback(async () => {
    if (!currentParams) return
    try {
      const blob = await downloadForecastCsv(currentParams)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `workload_${currentParams.from}_${currentParams.to}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      notification.error({ message: 'CSVダウンロードに失敗しました', placement: 'topRight' })
    }
  }, [currentParams])

  return (
    <div>
      <Title level={3}>PJ別工数計画</Title>
      <ProjectWorkloadFilter onFetch={fetchMatrix} loading={loading} />
      <Divider style={{ margin: '12px 0' }} />
      {data && (
        <SimulationToolbar
          simMode={simMode}
          onToggle={setSimMode}
          onSave={handleSave}
          onReset={handleReset}
          onDownload={handleDownload}
          saving={saving}
          resetting={resetting}
          hasDiff={diffMap.size > 0}
          canDownload={!!currentParams}
        />
      )}
      {error && (
        <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />
      )}
      {data ? (
        <ProjectWorkloadMatrix
          data={data}
          loading={loading}
          simMode={simMode}
          diffMap={diffMap}
          onCellChange={updateCell}
        />
      ) : (
        !loading && !error && (
          <div style={{ color: '#999', textAlign: 'center', padding: 40 }}>
            フィルタを設定して「表示」を押してください
          </div>
        )
      )}
    </div>
  )
}

export default ProjectWorkloadPage
