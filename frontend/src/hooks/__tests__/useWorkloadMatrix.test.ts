import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ForecastQueryParams, ForecastWorkloadResponse } from '../../types/workloadTypes'

const { mockGetForecast } = vi.hoisted(() => ({ mockGetForecast: vi.fn() }))

vi.mock('../../api/workloadApi', () => ({
  getForecast: mockGetForecast,
  saveSimulation: vi.fn(),
  resetSimulation: vi.fn(),
  downloadForecastCsv: vi.fn(),
  uploadPlanCsv: vi.fn(),
}))

import useWorkloadMatrix from '../useWorkloadMatrix'

const MOCK_DATA: ForecastWorkloadResponse = {
  months: ['2026-04', '2026-05'],
  rows: [
    {
      member_id: 1,
      member_name: '山田太郎',
      employee_code: 'E001',
      monthly_sums: { '2026-04': 0.5, '2026-05': 0.0 },
      projects: [
        {
          project_id: 101,
          project_name: 'プロジェクトA',
          wbs_tmp: 'WBS-001',
          matter_id: null,
          matter_name: null,
          cells: {
            '2026-04': { planned_mm: 0.5, simulated_mm: null, forecast_mm: 0.5 },
            '2026-05': { planned_mm: 0.0, simulated_mm: null, forecast_mm: 0.0 },
          },
        },
      ],
    },
  ],
}

const PARAMS: ForecastQueryParams = { from: '2026-04', to: '2027-03' }

describe('useWorkloadMatrix', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('初期状態: data/error が null で currentParams も null', () => {
    const { result } = renderHook(() => useWorkloadMatrix())
    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.currentParams).toBeNull()
  })

  it('fetchMatrix 成功: data・currentParams が設定され loading が false になる', async () => {
    mockGetForecast.mockResolvedValueOnce(MOCK_DATA)
    const { result } = renderHook(() => useWorkloadMatrix())

    await act(async () => {
      await result.current.fetchMatrix(PARAMS)
    })

    expect(result.current.data).toEqual(MOCK_DATA)
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.currentParams).toEqual(PARAMS)
  })

  it('fetchMatrix 成功: getForecast を正しいパラメータで呼ぶ', async () => {
    mockGetForecast.mockResolvedValueOnce(MOCK_DATA)
    const { result } = renderHook(() => useWorkloadMatrix())

    await act(async () => {
      await result.current.fetchMatrix(PARAMS)
    })

    expect(mockGetForecast).toHaveBeenCalledWith(PARAMS)
    expect(mockGetForecast).toHaveBeenCalledTimes(1)
  })

  it('fetchMatrix 失敗: error メッセージが設定され data は null のまま', async () => {
    mockGetForecast.mockRejectedValueOnce(new Error('Network error'))
    const { result } = renderHook(() => useWorkloadMatrix())

    await act(async () => {
      await result.current.fetchMatrix(PARAMS)
    })

    expect(result.current.data).toBeNull()
    expect(result.current.error).toBe('データの取得に失敗しました')
    expect(result.current.loading).toBe(false)
  })

  it('fetchMatrix 失敗時も currentParams は更新される', async () => {
    mockGetForecast.mockRejectedValueOnce(new Error('fail'))
    const { result } = renderHook(() => useWorkloadMatrix())

    await act(async () => {
      await result.current.fetchMatrix(PARAMS)
    })

    expect(result.current.currentParams).toEqual(PARAMS)
  })

  it('月次合計が 1.0 を超えるセルが月次サマリに含まれる', async () => {
    const overData: ForecastWorkloadResponse = {
      ...MOCK_DATA,
      rows: [
        {
          ...MOCK_DATA.rows[0],
          monthly_sums: { '2026-04': 1.5, '2026-05': 0.0 },
        },
      ],
    }
    mockGetForecast.mockResolvedValueOnce(overData)
    const { result } = renderHook(() => useWorkloadMatrix())

    await act(async () => {
      await result.current.fetchMatrix(PARAMS)
    })

    expect(result.current.data?.rows[0].monthly_sums['2026-04']).toBe(1.5)
  })
})
