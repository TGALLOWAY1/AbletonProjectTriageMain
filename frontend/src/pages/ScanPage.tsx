import { useState, useEffect } from 'react'
import { 
  Search, 
  FolderPlus, 
  Play, 
  Square, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  Trash2
} from 'lucide-react'
import { scanApi, settingsApi } from '../services/api'
import type { ScanProgress } from '../types/project'
import clsx from 'clsx'

interface SavedPath {
  id: number
  path: string
  created_at: string
}

export default function ScanPage() {
  const [paths, setPaths] = useState<string[]>([])
  const [savedPaths, setSavedPaths] = useState<SavedPath[]>([])
  const [newPath, setNewPath] = useState('')
  const [scanStatus, setScanStatus] = useState<ScanProgress | null>(null)
  const [polling, setPolling] = useState(false)
  const [loadingPaths, setLoadingPaths] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Load saved paths on mount
  useEffect(() => {
    loadSavedPaths()
    // Check if there's an active scan on mount
    checkScanStatus()
  }, [])

  const checkScanStatus = async () => {
    try {
      const response = await scanApi.getStatus()
      const status = response.data
      
      // If there's an active scan, start polling
      if (status.status === 'scanning') {
        setPolling(true)
        setScanStatus(status)
      } else if (status.status === 'completed' || status.status === 'error') {
        // Show completed/error status but don't poll
        setScanStatus(status)
      }
    } catch (error) {
      // Ignore errors when checking status on mount
      console.debug('No active scan found')
    }
  }

  const loadSavedPaths = async () => {
    try {
      setLoadingPaths(true)
      const response = await settingsApi.getScanPaths()
      const saved = response.data
      setSavedPaths(saved)
      setPaths(saved.map(p => p.path))
    } catch (error) {
      console.error('Failed to load saved paths:', error)
    } finally {
      setLoadingPaths(false)
    }
  }

  // Poll for scan status when scanning
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    if (polling) {
      interval = setInterval(async () => {
        try {
          const response = await scanApi.getStatus()
          setScanStatus(response.data)
          
          if (response.data.status === 'completed' || response.data.status === 'error') {
            setPolling(false)
          }
        } catch {
          setPolling(false)
        }
      }, 500)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [polling])

  const addPath = async () => {
    if (newPath && !paths.includes(newPath)) {
      try {
        // Save to database
        await settingsApi.addScanPath(newPath)
        // Update local state
        setPaths([...paths, newPath])
        setNewPath('')
        // Reload saved paths to get the ID
        await loadSavedPaths()
      } catch (error) {
        console.error('Failed to save path:', error)
        // Still add to local state even if save fails
        setPaths([...paths, newPath])
        setNewPath('')
      }
    }
  }

  const removePath = async (path: string) => {
    try {
      // Find the saved path ID
      const savedPath = savedPaths.find(p => p.path === path)
      if (savedPath) {
        await settingsApi.deleteScanPath(savedPath.id)
      } else {
        // Fallback: try deleting by path
        await settingsApi.deleteScanPathByPath(path)
      }
      // Update local state
      setPaths(paths.filter(p => p !== path))
      await loadSavedPaths()
    } catch (error) {
      console.error('Failed to delete path:', error)
      // Still remove from local state even if delete fails
      setPaths(paths.filter(p => p !== path))
    }
  }

  const startScan = async () => {
    if (paths.length === 0) return

    setErrorMessage(null)

    try {
      await scanApi.start({ paths })
      setPolling(true)
      setScanStatus({
        status: 'scanning',
        current_path: null,
        files_scanned: 0,
        projects_found: 0,
        errors: [],
        started_at: new Date().toISOString(),
        completed_at: null,
      })
    } catch (error: any) {
      // Handle 409 Conflict - scan already in progress
      if (error.response?.status === 409) {
        const message = error.response?.data?.detail || 'A scan is already in progress'
        setErrorMessage(message)
        
        // Automatically start polling to show the active scan status
        setPolling(true)
        
        // Immediately fetch the current scan status
        try {
          const statusResponse = await scanApi.getStatus()
          setScanStatus(statusResponse.data)
          
          // If the scan is already completed, stop polling
          if (statusResponse.data.status === 'completed' || statusResponse.data.status === 'error') {
            setPolling(false)
          }
        } catch (statusError) {
          console.error('Failed to fetch scan status:', statusError)
          setPolling(false)
        }
      } else {
        // Handle other errors
        const message = error.response?.data?.detail || error.message || 'Failed to start scan'
        setErrorMessage(message)
        console.error('Failed to start scan:', error)
      }
    }
  }

  const cancelScan = async () => {
    try {
      await scanApi.cancel()
      setPolling(false)
    } catch (error) {
      console.error('Failed to cancel scan:', error)
    }
  }

  const isScanning = scanStatus?.status === 'scanning'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-ableton-accent/10">
            <Search className="w-6 h-6 text-ableton-accent" />
          </div>
          <div>
            <span className="text-xs font-mono text-ableton-text-muted">PHASE 1</span>
            <h1 className="text-2xl font-bold">Deep Scan</h1>
          </div>
        </div>
        <p className="text-ableton-text-muted ml-14">
          Index every Ableton project without moving or altering files
        </p>
      </div>

      {/* Path Input */}
      <div className="card mb-6">
        <h2 className="font-semibold mb-4">Scan Directories</h2>
        
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={newPath}
            onChange={(e) => setNewPath(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addPath()}
            placeholder="/Users/you/Music"
            className="input flex-1"
            disabled={isScanning}
          />
          <button
            onClick={addPath}
            disabled={!newPath || isScanning}
            className="btn-secondary flex items-center gap-2"
          >
            <FolderPlus className="w-4 h-4" />
            Add
          </button>
        </div>

        {/* Path List */}
        {paths.length > 0 && (
          <div className="space-y-2 mb-4">
            {paths.map((path) => (
              <div
                key={path}
                className="flex items-center justify-between px-3 py-2 bg-ableton-bg rounded-lg"
              >
                <span className="font-mono text-sm truncate">{path}</span>
                <button
                  onClick={() => removePath(path)}
                  disabled={isScanning}
                  className="p-1 hover:bg-ableton-surface-light rounded transition-colors"
                >
                  <Trash2 className="w-4 h-4 text-ableton-text-muted hover:text-ableton-danger" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Loading State */}
        {loadingPaths && (
          <div className="text-sm text-ableton-text-muted text-center py-4">
            <Loader2 className="w-4 h-4 animate-spin inline-block mr-2" />
            Loading saved paths...
          </div>
        )}

        {/* Common Paths Suggestions */}
        {!loadingPaths && paths.length === 0 && (
          <div className="text-sm text-ableton-text-muted">
            <p className="mb-2">Common locations:</p>
            <div className="flex flex-wrap gap-2">
              {[
                '/Users/*/Music',
                '/Users/*/Desktop',
                '/Users/*/Documents',
                '/Volumes/External',
                '~/Library/Mobile Documents/com~apple~CloudDocs/',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setNewPath(suggestion)}
                  className="px-2 py-1 bg-ableton-surface-light rounded text-xs hover:bg-ableton-border transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {errorMessage && (
        <div className="card mb-6 border-l-4 border-ableton-warning bg-ableton-warning/10">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-ableton-warning flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-ableton-warning mb-1">Notice</p>
              <p className="text-sm text-ableton-text-muted">{errorMessage}</p>
              {errorMessage.includes('already in progress') && (
                <p className="text-xs text-ableton-text-muted mt-2">
                  The scan status will update automatically below.
                </p>
              )}
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-ableton-text-muted hover:text-ableton-text transition-colors"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Scan Controls */}
      <div className="card mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">
              {isScanning ? 'Scanning...' : 'Ready to Scan'}
            </h3>
            <p className="text-sm text-ableton-text-muted">
              {paths.length} director{paths.length === 1 ? 'y' : 'ies'} selected
            </p>
          </div>
          
          {isScanning ? (
            <button onClick={cancelScan} className="btn-danger flex items-center gap-2">
              <Square className="w-4 h-4" />
              Cancel
            </button>
          ) : (
            <button
              onClick={startScan}
              disabled={paths.length === 0}
              className="btn-primary flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Start Scan
            </button>
          )}
        </div>
      </div>

      {/* Scan Progress */}
      {scanStatus && (
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            {scanStatus.status === 'scanning' && (
              <Loader2 className="w-5 h-5 text-ableton-accent animate-spin" />
            )}
            {scanStatus.status === 'completed' && (
              <CheckCircle className="w-5 h-5 text-ableton-success" />
            )}
            {scanStatus.status === 'error' && (
              <AlertCircle className="w-5 h-5 text-ableton-danger" />
            )}
            <h3 className="font-semibold">
              {scanStatus.status === 'scanning' && 'Scanning...'}
              {scanStatus.status === 'completed' && 'Scan Complete'}
              {scanStatus.status === 'error' && 'Scan Error'}
            </h3>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="p-3 bg-ableton-bg rounded-lg">
              <p className="text-2xl font-bold">{scanStatus.files_scanned}</p>
              <p className="text-xs text-ableton-text-muted">Files Scanned</p>
            </div>
            <div className="p-3 bg-ableton-bg rounded-lg">
              <p className="text-2xl font-bold text-ableton-accent">
                {scanStatus.projects_found}
              </p>
              <p className="text-xs text-ableton-text-muted">Projects Found</p>
            </div>
          </div>

          {/* Current Path */}
          {scanStatus.current_path && (
            <div className="mb-4">
              <p className="text-xs text-ableton-text-muted mb-1">Currently scanning:</p>
              <p className="font-mono text-sm truncate bg-ableton-bg px-3 py-2 rounded-lg">
                {scanStatus.current_path}
              </p>
            </div>
          )}

          {/* Errors */}
          {scanStatus.errors.length > 0 && (
            <div>
              <p className="text-xs text-ableton-text-muted mb-2">
                Skipped {scanStatus.errors.length} path(s):
              </p>
              <div className="max-h-32 overflow-y-auto space-y-1">
                {scanStatus.errors.map((error, idx) => (
                  <div
                    key={idx}
                    className={clsx(
                      'text-xs font-mono px-2 py-1 rounded',
                      'bg-ableton-danger/10 text-ableton-danger'
                    )}
                  >
                    {error.path}: {error.error}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

