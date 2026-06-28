export type AppSettings = {
  defaultDeptId: number | undefined
  defaultFromYear: number
  defaultFromMonth: number
  defaultToYear: number
  defaultToMonth: number
}

const STORAGE_KEY = 'workload_settings'

export const DEFAULT_SETTINGS: AppSettings = {
  defaultDeptId: undefined,
  defaultFromYear: 2026,
  defaultFromMonth: 4,
  defaultToYear: 2027,
  defaultToMonth: 3,
}

export const loadSettings = (): AppSettings => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { ...DEFAULT_SETTINGS }
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  } catch {
    return { ...DEFAULT_SETTINGS }
  }
}

export const saveSettings = (settings: AppSettings): void => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
}
