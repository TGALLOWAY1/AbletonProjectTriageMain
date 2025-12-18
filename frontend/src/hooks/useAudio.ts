import { useState, useCallback } from 'react'
import { audioApi } from '../services/api'

export function useAudio() {
  const [currentlyPlaying, setCurrentlyPlaying] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)

  const checkPreview = useCallback(async (projectId: number) => {
    try {
      const response = await audioApi.checkPreview(projectId)
      return response.data
    } catch {
      return { available: false, path: null }
    }
  }, [])

  const getPreviewUrl = useCallback((projectId: number) => {
    return audioApi.getPreviewUrl(projectId)
  }, [])

  const play = useCallback((projectId: number) => {
    setCurrentlyPlaying(projectId)
  }, [])

  const stop = useCallback(() => {
    setCurrentlyPlaying(null)
  }, [])

  return {
    currentlyPlaying,
    loading,
    checkPreview,
    getPreviewUrl,
    play,
    stop,
  }
}

