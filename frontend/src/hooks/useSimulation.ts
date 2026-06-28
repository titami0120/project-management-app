import { notification } from 'antd'
import { useCallback, useMemo, useRef, useState } from 'react'
import {
  resetSimulation as resetSimulationApi,
  saveSimulation as saveSimulationApi,
} from '../api/workloadApi'
import type { ForecastWorkloadResponse, SimulationUpdateItem } from '../types/workloadTypes'

export const diffKey = (memberId: number, projectId: number, monthStr: string) =>
  `${memberId}:${projectId}:${monthStr}`

const useSimulation = (data: ForecastWorkloadResponse | null) => {
  const [simMode, setSimMode] = useState(false)
  const [diffMap, setDiffMap] = useState<Map<string, number | null>>(new Map())
  const [saving, setSaving] = useState(false)
  const [resetting, setResetting] = useState(false)

  // 各要員の月次合計をリアルタイム計算
  const computedSums = useMemo(() => {
    if (!data) return {} as Record<string, Record<string, number>>
    const result: Record<string, Record<string, number>> = {}
    for (const member of data.rows) {
      result[String(member.member_id)] = {}
      for (const month of data.months) {
        let sum = 0
        for (const project of member.projects) {
          const key = diffKey(member.member_id, project.project_id, month)
          const original = project.cells[month]?.forecast_mm ?? null
          const eff = diffMap.has(key) ? (diffMap.get(key) ?? 0) : (original ?? 0)
          sum += eff
        }
        result[String(member.member_id)][month] = sum
      }
    }
    return result
  }, [diffMap, data])

  // 超過済みメンバーを追跡（同一要員への重複通知防止）
  const overloadedRef = useRef<Set<number>>(new Set())

  const updateCell = useCallback(
    (memberId: number, projectId: number, monthStr: string, value: number | null) => {
      if (!data) return
      const key = diffKey(memberId, projectId, monthStr)

      // 新しい diffMap で合計を先読み計算（通知判定用）
      const tempMap = new Map(diffMap)
      tempMap.set(key, value)

      const member = data.rows.find((r) => r.member_id === memberId)
      if (member) {
        let isOver = false
        for (const month of data.months) {
          let sum = 0
          for (const p of member.projects) {
            const k = diffKey(memberId, p.project_id, month)
            const original = p.cells[month]?.forecast_mm ?? null
            const eff = tempMap.has(k) ? (tempMap.get(k) ?? 0) : (original ?? 0)
            sum += eff
          }
          if (sum > 1.0) { isOver = true; break }
        }
        if (isOver && !overloadedRef.current.has(memberId)) {
          notification.warning({
            message: `${member.member_name} の月次合計が 1.0 人月を超えました`,
            placement: 'topRight',
          })
          overloadedRef.current.add(memberId)
        } else if (!isOver) {
          overloadedRef.current.delete(memberId)
        }
      }

      setDiffMap(tempMap)
    },
    [data, diffMap],
  )

  const resetDiff = useCallback(() => {
    setDiffMap(new Map())
    overloadedRef.current = new Set()
  }, [])

  const saveToServer = useCallback(
    async (refetch: () => void) => {
      if (diffMap.size === 0) return
      setSaving(true)
      const updates: SimulationUpdateItem[] = []
      for (const [key, value] of diffMap) {
        const [memberIdStr, projectIdStr, monthStr] = key.split(':')
        const [yearStr, monthPartStr] = monthStr.split('-')
        updates.push({
          member_id: Number(memberIdStr),
          project_id: Number(projectIdStr),
          year: Number(yearStr),
          month: Number(monthPartStr),
          simulated_mm: value,
        })
      }
      try {
        await saveSimulationApi({ updates })
        resetDiff()
        refetch()
        notification.success({ message: 'シミュレーション値を保存しました', placement: 'topRight' })
      } catch {
        notification.error({ message: '保存に失敗しました', placement: 'topRight' })
      } finally {
        setSaving(false)
      }
    },
    [diffMap, resetDiff],
  )

  const resetFromServer = useCallback(
    async (refetch: () => void) => {
      setResetting(true)
      try {
        await resetSimulationApi()
        resetDiff()
        refetch()
        notification.success({ message: 'シミュレーション値をリセットしました', placement: 'topRight' })
      } catch {
        notification.error({ message: 'リセットに失敗しました', placement: 'topRight' })
      } finally {
        setResetting(false)
      }
    },
    [resetDiff],
  )

  return {
    simMode, setSimMode,
    diffMap, updateCell, resetDiff,
    computedSums,
    saving, resetting,
    saveToServer, resetFromServer,
  }
}

export default useSimulation
