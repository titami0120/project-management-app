import { useCallback, useState } from 'react'
import { getForecast } from '../api/workloadApi'
import type { ForecastQueryParams, ForecastWorkloadResponse } from '../types/workloadTypes'

interface WorkloadMatrixState {
  data: ForecastWorkloadResponse | null
  loading: boolean
  error: string | null
}

const useWorkloadMatrix = () => {
  const [state, setState] = useState<WorkloadMatrixState>({
    data: null,
    loading: false,
    error: null,
  })
  const [currentParams, setCurrentParams] = useState<ForecastQueryParams | null>(null)

  const fetchMatrix = useCallback(async (params: ForecastQueryParams) => {
    setCurrentParams(params)
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const data = await getForecast(params)
      setState({ data, loading: false, error: null })
    } catch {
      setState({ data: null, loading: false, error: 'データの取得に失敗しました' })
    }
  }, [])

  return { ...state, fetchMatrix, currentParams }
}

export default useWorkloadMatrix
