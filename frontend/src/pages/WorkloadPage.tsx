import { Alert, Divider, Typography, notification } from 'antd'
import { useCallback, useState } from 'react'
import { downloadForecastCsv, getForecast } from '../api/workloadApi'
import ProjectDetailPanel from '../components/workload/ProjectDetailPanel'
import SimulationToolbar from '../components/workload/SimulationToolbar'
import WorkloadFilter from '../components/workload/WorkloadFilter'
import WorkloadMatrix from '../components/workload/WorkloadMatrix'
import useSimulation from '../hooks/useSimulation'
import useWorkloadMatrix from '../hooks/useWorkloadMatrix'
import type { ForecastWorkloadResponse } from '../types/workloadTypes'

const { Title } = Typography

const WorkloadPage = () => {
  const { data, loading, error, fetchMatrix, currentParams } = useWorkloadMatrix()
  const {
    simMode,
    setSimMode,
    diffMap,
    updateCell,
    computedSums,
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

  const [panelProject, setPanelProject] = useState<{ id: number; name: string; wbsTmp: string } | null>(null)
  const [panelData, setPanelData] = useState<ForecastWorkloadResponse | null>(null)
  const [panelLoading, setPanelLoading] = useState(false)

  const handleProjectClick = useCallback(async (projectId: number, projectName: string, wbsTmp: string) => {
    if (!currentParams) return
    setPanelProject({ id: projectId, name: projectName, wbsTmp })
    setPanelLoading(true)
    try {
      const result = await getForecast({
        from: currentParams.from,
        to: currentParams.to,
        project_id: projectId,
      })
      setPanelData(result)
    } catch {
      notification.error({ message: 'プロジェクト詳細の取得に失敗しました', placement: 'topRight' })
    } finally {
      setPanelLoading(false)
    }
  }, [currentParams])

  const handleDownload = useCallback(async () => {
    if (!currentParams) return
    try {
      const blob = await downloadForecastCsv(currentParams)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `simulation_${currentParams.from}_${currentParams.to}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      notification.error({ message: 'CSVダウンロードに失敗しました', placement: 'topRight' })
    }
  }, [currentParams])

  return (
    <div>
      <Title level={3}>要員別工数計画</Title>
      <WorkloadFilter onFetch={fetchMatrix} loading={loading} />
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
        <>
          <WorkloadMatrix
            data={data}
            loading={loading}
            simMode={simMode}
            diffMap={diffMap}
            computedSums={computedSums}
            onCellChange={updateCell}
            onProjectClick={handleProjectClick}
          />
          {panelProject && panelData && (
            <ProjectDetailPanel
              projectId={panelProject.id}
              projectName={panelProject.name}
              wbsTmp={panelProject.wbsTmp}
              data={panelData}
              loading={panelLoading}
              simMode={simMode}
              diffMap={diffMap}
              onCellChange={updateCell}
              onClose={() => { setPanelProject(null); setPanelData(null) }}
            />
          )}
        </>
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

export default WorkloadPage
