import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ForecastWorkloadResponse } from '../../types/workloadTypes'

// antd notification をモック（useSimulation が使う warning/success/error のみ）
const { mockWarning, mockSuccess, mockError } = vi.hoisted(() => ({
  mockWarning: vi.fn(),
  mockSuccess: vi.fn(),
  mockError: vi.fn(),
}))

vi.mock('antd', () => ({
  notification: {
    warning: mockWarning,
    success: mockSuccess,
    error: mockError,
    info: vi.fn(),
  },
}))

// workloadApi をモック
const { mockSaveSimulation, mockResetSimulation } = vi.hoisted(() => ({
  mockSaveSimulation: vi.fn(),
  mockResetSimulation: vi.fn(),
}))

vi.mock('../../api/workloadApi', () => ({
  getForecast: vi.fn(),
  saveSimulation: mockSaveSimulation,
  resetSimulation: mockResetSimulation,
  downloadForecastCsv: vi.fn(),
  uploadPlanCsv: vi.fn(),
}))

import useSimulation, { diffKey } from '../useSimulation'

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

describe('useSimulation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // -----------------------------------------------------------------------
  // 初期状態
  // -----------------------------------------------------------------------

  describe('初期状態', () => {
    it('simMode が false', () => {
      const { result } = renderHook(() => useSimulation(null))
      expect(result.current.simMode).toBe(false)
    })

    it('diffMap が空', () => {
      const { result } = renderHook(() => useSimulation(null))
      expect(result.current.diffMap.size).toBe(0)
    })

    it('data が null のとき computedSums は空オブジェクト', () => {
      const { result } = renderHook(() => useSimulation(null))
      expect(result.current.computedSums).toEqual({})
    })
  })

  // -----------------------------------------------------------------------
  // diffKey ユーティリティ
  // -----------------------------------------------------------------------

  describe('diffKey', () => {
    it('"memberId:projectId:month" 形式のキーを生成する', () => {
      expect(diffKey(1, 101, '2026-04')).toBe('1:101:2026-04')
    })
  })

  // -----------------------------------------------------------------------
  // updateCell
  // -----------------------------------------------------------------------

  describe('updateCell', () => {
    it('diffMap にエントリを追加する', () => {
      const { result } = renderHook(() => useSimulation(MOCK_DATA))
      act(() => {
        result.current.updateCell(1, 101, '2026-04', 0.75)
      })
      expect(result.current.diffMap.get('1:101:2026-04')).toBe(0.75)
    })

    it('null 値（クリア）も diffMap に格納できる', () => {
      const { result } = renderHook(() => useSimulation(MOCK_DATA))
      act(() => {
        result.current.updateCell(1, 101, '2026-04', null)
      })
      expect(result.current.diffMap.has('1:101:2026-04')).toBe(true)
      expect(result.current.diffMap.get('1:101:2026-04')).toBeNull()
    })

    it('computedSums が diffMap の値を反映する', () => {
      const { result } = renderHook(() => useSimulation(MOCK_DATA))
      act(() => {
        result.current.updateCell(1, 101, '2026-04', 0.75)
      })
      expect(result.current.computedSums['1']['2026-04']).toBe(0.75)
    })

    it('元の値 (original) が変わっていない月は original を使う', () => {
      const { result } = renderHook(() => useSimulation(MOCK_DATA))
      act(() => {
        result.current.updateCell(1, 101, '2026-04', 0.75)
      })
      // '2026-05' の original は 0.0（diffMap に未登録）
      expect(result.current.computedSums['1']['2026-05']).toBe(0.0)
    })

    it('合計が 1.0 超過したとき notification.warning を呼ぶ', () => {
      const { result } = renderHook(() => useSimulation(MOCK_DATA))
      act(() => {
        result.current.updateCell(1, 101, '2026-04', 1.5)
      })
      expect(mockWarning).toHaveBeenCalledTimes(1)
    })

    it('同一要員の超過は 1 回だけ通知する（重複防止）', () => {
      const { result } = renderHook(() => useSimulation(MOCK_DATA))
      act(() => {
        result.current.updateCell(1, 101, '2026-04', 1.5) // 超過→通知
        result.current.updateCell(1, 101, '2026-05', 0.5) // まだ超過中→通知しない
      })
      expect(mockWarning).toHaveBeenCalledTimes(1)
    })

    it('合計が 1.0 以下に戻ったあと再び超過したら再度通知する', () => {
      const { result } = renderHook(() => useSimulation(MOCK_DATA))
      act(() => {
        result.current.updateCell(1, 101, '2026-04', 1.5) // 超過→通知
      })
      act(() => {
        result.current.updateCell(1, 101, '2026-04', 0.5) // 回復
      })
      act(() => {
        result.current.updateCell(1, 101, '2026-04', 1.5) // 再超過→再通知
      })
      expect(mockWarning).toHaveBeenCalledTimes(2)
    })
  })

  // -----------------------------------------------------------------------
  // resetDiff
  // -----------------------------------------------------------------------

  describe('resetDiff', () => {
    it('diffMap を空にする', () => {
      const { result } = renderHook(() => useSimulation(MOCK_DATA))
      act(() => {
        result.current.updateCell(1, 101, '2026-04', 0.75)
      })
      act(() => {
        result.current.resetDiff()
      })
      expect(result.current.diffMap.size).toBe(0)
    })

    it('computedSums が original 値に戻る', () => {
      const { result } = renderHook(() => useSimulation(MOCK_DATA))
      act(() => {
        result.current.updateCell(1, 101, '2026-04', 0.9)
      })
      act(() => {
        result.current.resetDiff()
      })
      expect(result.current.computedSums['1']['2026-04']).toBe(0.5)
    })

    it('超過トラッキングもクリアされ再通知が可能になる', () => {
      const { result } = renderHook(() => useSimulation(MOCK_DATA))
      act(() => {
        result.current.updateCell(1, 101, '2026-04', 1.5)
      })
      act(() => {
        result.current.resetDiff()
      })
      act(() => {
        result.current.updateCell(1, 101, '2026-04', 1.5)
      })
      expect(mockWarning).toHaveBeenCalledTimes(2)
    })
  })

  // -----------------------------------------------------------------------
  // saveToServer
  // -----------------------------------------------------------------------

  describe('saveToServer', () => {
    it('diffMap が空のとき API を呼ばない', async () => {
      const { result } = renderHook(() => useSimulation(MOCK_DATA))
      await act(async () => {
        await result.current.saveToServer(vi.fn())
      })
      expect(mockSaveSimulation).not.toHaveBeenCalled()
    })

    it('diffMap を正しい SimulationUpdateRequest 形式で API に送る', async () => {
      mockSaveSimulation.mockResolvedValueOnce(undefined)
      const { result } = renderHook(() => useSimulation(MOCK_DATA))

      act(() => {
        result.current.updateCell(1, 101, '2026-04', 0.75)
      })
      await act(async () => {
        await result.current.saveToServer(vi.fn())
      })

      expect(mockSaveSimulation).toHaveBeenCalledWith({
        updates: [
          { member_id: 1, project_id: 101, year: 2026, month: 4, simulated_mm: 0.75 },
        ],
      })
    })

    it('成功後に refetch を呼び diffMap をクリアして success 通知を表示する', async () => {
      mockSaveSimulation.mockResolvedValueOnce(undefined)
      const { result } = renderHook(() => useSimulation(MOCK_DATA))

      act(() => {
        result.current.updateCell(1, 101, '2026-04', 0.75)
      })
      const refetch = vi.fn()
      await act(async () => {
        await result.current.saveToServer(refetch)
      })

      expect(refetch).toHaveBeenCalledTimes(1)
      expect(result.current.diffMap.size).toBe(0)
      expect(mockSuccess).toHaveBeenCalledTimes(1)
    })

    it('API 失敗時に error 通知を表示し diffMap は変化しない', async () => {
      mockSaveSimulation.mockRejectedValueOnce(new Error('fail'))
      const { result } = renderHook(() => useSimulation(MOCK_DATA))

      act(() => {
        result.current.updateCell(1, 101, '2026-04', 0.75)
      })
      const refetch = vi.fn()
      await act(async () => {
        await result.current.saveToServer(refetch)
      })

      expect(mockError).toHaveBeenCalledTimes(1)
      expect(refetch).not.toHaveBeenCalled()
      expect(result.current.diffMap.size).toBe(1)
    })
  })

  // -----------------------------------------------------------------------
  // resetFromServer
  // -----------------------------------------------------------------------

  describe('resetFromServer', () => {
    it('resetSimulation API を呼ぶ', async () => {
      mockResetSimulation.mockResolvedValueOnce(undefined)
      const { result } = renderHook(() => useSimulation(MOCK_DATA))

      await act(async () => {
        await result.current.resetFromServer(vi.fn())
      })

      expect(mockResetSimulation).toHaveBeenCalledTimes(1)
    })

    it('成功後に refetch を呼び diffMap をクリアして success 通知を表示する', async () => {
      mockResetSimulation.mockResolvedValueOnce(undefined)
      const { result } = renderHook(() => useSimulation(MOCK_DATA))

      act(() => {
        result.current.updateCell(1, 101, '2026-04', 0.75)
      })
      const refetch = vi.fn()
      await act(async () => {
        await result.current.resetFromServer(refetch)
      })

      expect(refetch).toHaveBeenCalledTimes(1)
      expect(result.current.diffMap.size).toBe(0)
      expect(mockSuccess).toHaveBeenCalledTimes(1)
    })

    it('API 失敗時に error 通知を表示し refetch は呼ばない', async () => {
      mockResetSimulation.mockRejectedValueOnce(new Error('fail'))
      const { result } = renderHook(() => useSimulation(MOCK_DATA))

      const refetch = vi.fn()
      await act(async () => {
        await result.current.resetFromServer(refetch)
      })

      expect(mockError).toHaveBeenCalledTimes(1)
      expect(refetch).not.toHaveBeenCalled()
    })
  })
})
