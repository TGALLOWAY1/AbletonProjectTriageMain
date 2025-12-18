import { useState, useEffect, useCallback } from 'react'
import { projectsApi } from '../services/api'
import type { Project, ProjectFilters, ProjectStats } from '../types/project'

export function useProjects(initialFilters?: ProjectFilters) {
  const [projects, setProjects] = useState<Project[]>([])
  const [stats, setStats] = useState<ProjectStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<ProjectFilters>(initialFilters || {})

  const loadProjects = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await projectsApi.list(filters)
      setProjects(response.data)
    } catch (err) {
      setError('Failed to load projects')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [filters])

  const loadStats = useCallback(async () => {
    try {
      const response = await projectsApi.getStats()
      setStats(response.data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }, [])

  useEffect(() => {
    loadProjects()
  }, [loadProjects])

  useEffect(() => {
    loadStats()
  }, [loadStats])

  const updateFilters = useCallback((newFilters: Partial<ProjectFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }))
  }, [])

  const refresh = useCallback(() => {
    loadProjects()
    loadStats()
  }, [loadProjects, loadStats])

  return {
    projects,
    stats,
    loading,
    error,
    filters,
    updateFilters,
    refresh,
  }
}

