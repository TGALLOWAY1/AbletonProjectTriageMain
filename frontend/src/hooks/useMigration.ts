import { useState, useCallback } from 'react'
import { migrationApi } from '../services/api'
import type { MigrationPlan, MigrationManifest } from '../types/project'

export function useMigration() {
  const [plan, setPlan] = useState<MigrationPlan | null>(null)
  const [history, setHistory] = useState<MigrationManifest[]>([])
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadHistory = useCallback(async () => {
    try {
      const response = await migrationApi.getHistory()
      setHistory(response.data)
    } catch (err) {
      console.error('Failed to load migration history:', err)
    }
  }, [])

  const generatePreview = useCallback(async (archivePath: string, curatedPath: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await migrationApi.preview(archivePath, curatedPath)
      setPlan(response.data)
    } catch (err) {
      setError('Failed to generate migration preview')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [])

  const execute = useCallback(async (archivePath: string, curatedPath: string, manifestPath?: string) => {
    setExecuting(true)
    setError(null)
    try {
      await migrationApi.execute(archivePath, curatedPath, manifestPath)
      setPlan(null)
      await loadHistory()
    } catch (err) {
      setError('Migration failed')
      console.error(err)
    } finally {
      setExecuting(false)
    }
  }, [loadHistory])

  const rollback = useCallback(async (manifestId: number) => {
    setLoading(true)
    setError(null)
    try {
      await migrationApi.rollback(manifestId)
      await loadHistory()
    } catch (err) {
      setError('Rollback failed')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [loadHistory])

  const clearPlan = useCallback(() => {
    setPlan(null)
  }, [])

  return {
    plan,
    history,
    loading,
    executing,
    error,
    loadHistory,
    generatePreview,
    execute,
    rollback,
    clearPlan,
  }
}

