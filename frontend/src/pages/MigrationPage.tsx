import { useState, useEffect } from 'react'
import { 
  FolderSync, 
  AlertTriangle, 
  CheckCircle, 
  FolderOpen,
  ArrowRight,
  RotateCcw,
  Play,
  Eye
} from 'lucide-react'
import { projectsApi, migrationApi } from '../services/api'
import type { Project, MigrationPlan, MigrationManifest } from '../types/project'
import clsx from 'clsx'

export default function MigrationPage() {
  const [readyProjects, setReadyProjects] = useState<Project[]>([])
  const [archiveProjects, setArchiveProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [migrationPlan, setMigrationPlan] = useState<MigrationPlan | null>(null)
  const [migrationHistory, setMigrationHistory] = useState<MigrationManifest[]>([])
  
  // Destination paths
  const [archivePath, setArchivePath] = useState('/Volumes/External/Ableton_Archive')
  const [curatedPath, setCuratedPath] = useState('~/Music/2026_Music')
  const [selectedGenre, setSelectedGenre] = useState('Dubstep')
  
  const [executing, setExecuting] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [readyResponse, archiveResponse, historyResponse] = await Promise.all([
        projectsApi.list({ hygiene_status: 'ready_for_migration' }),
        projectsApi.list({ triage_status: 'trash' }),
        migrationApi.getHistory(),
      ])
      
      // Also get harvested salvage projects
      const salvageResponse = await projectsApi.list({ 
        triage_status: 'salvage',
        hygiene_status: 'harvested',
      })
      
      setReadyProjects(readyResponse.data)
      setArchiveProjects([...archiveResponse.data, ...salvageResponse.data])
      setMigrationHistory(historyResponse.data)
    } catch (error) {
      console.error('Failed to load migration data:', error)
    } finally {
      setLoading(false)
    }
  }

  const generatePreview = async () => {
    try {
      const response = await migrationApi.preview(archivePath, curatedPath)
      setMigrationPlan(response.data)
    } catch (error) {
      console.error('Failed to generate migration preview:', error)
    }
  }

  const executeMigration = async () => {
    if (!migrationPlan) return
    
    setExecuting(true)
    try {
      // In a real implementation, we'd save the manifest first
      // then pass the path to execute
      await migrationApi.execute('/tmp/migration_manifest.json')
      await loadData()
      setMigrationPlan(null)
    } catch (error) {
      console.error('Failed to execute migration:', error)
    } finally {
      setExecuting(false)
    }
  }

  const rollbackMigration = async (manifestId: number) => {
    try {
      await migrationApi.rollback(manifestId)
      await loadData()
    } catch (error) {
      console.error('Failed to rollback migration:', error)
    }
  }

  const genres = ['Dubstep', 'House', 'Techno', 'Drum & Bass', 'Hip Hop', 'Ambient', 'Other']

  return (
    <div className="max-w-5xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-ableton-blue/10">
            <FolderSync className="w-6 h-6 text-ableton-blue" />
          </div>
          <div>
            <span className="text-xs font-mono text-ableton-text-muted">PHASE 4</span>
            <h1 className="text-2xl font-bold">Grand Migration</h1>
          </div>
        </div>
        <p className="text-ableton-text-muted ml-14">
          Physically reorganize your hard drive. Execute only when ready.
        </p>
      </div>

      {/* Warning */}
      <div className="card bg-ableton-warning/10 border-ableton-warning/30 mb-6">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-ableton-warning flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-ableton-warning mb-1">Important</h3>
            <p className="text-sm text-ableton-text-muted">
              This phase moves actual files. Always preview before executing. 
              A rollback manifest is created for safety.
            </p>
          </div>
        </div>
      </div>

      {/* Configuration */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Archive Destination */}
        <div className="card">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-ableton-text-muted" />
            Archive Destination
          </h3>
          <p className="text-xs text-ableton-text-muted mb-2">
            Trash and harvested salvage projects go here
          </p>
          <input
            type="text"
            value={archivePath}
            onChange={(e) => setArchivePath(e.target.value)}
            placeholder="/Volumes/External/Ableton_Archive"
            className="input"
          />
          <p className="text-xs text-ableton-text-muted mt-2">
            {archiveProjects.length} projects ready for archive
          </p>
        </div>

        {/* Curated Destination */}
        <div className="card">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-ableton-text-muted" />
            Curated Destination
          </h3>
          <p className="text-xs text-ableton-text-muted mb-2">
            Must Finish projects go here, organized by genre
          </p>
          <input
            type="text"
            value={curatedPath}
            onChange={(e) => setCuratedPath(e.target.value)}
            placeholder="~/Music/2026_Music"
            className="input mb-2"
          />
          <select
            value={selectedGenre}
            onChange={(e) => setSelectedGenre(e.target.value)}
            className="input"
          >
            {genres.map((genre) => (
              <option key={genre} value={genre}>{genre}</option>
            ))}
          </select>
          <p className="text-xs text-ableton-text-muted mt-2">
            {readyProjects.length} projects ready for curation
          </p>
        </div>
      </div>

      {/* Preview Button */}
      <div className="flex justify-center mb-6">
        <button
          onClick={generatePreview}
          disabled={archiveProjects.length === 0 && readyProjects.length === 0}
          className="btn-primary flex items-center gap-2"
        >
          <Eye className="w-4 h-4" />
          Preview Migration Plan
        </button>
      </div>

      {/* Migration Plan Preview */}
      {migrationPlan && (
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Migration Plan</h3>
            <span className="text-xs text-ableton-text-muted">
              {migrationPlan.operations.length} operations
            </span>
          </div>

          <div className="max-h-64 overflow-y-auto mb-4 space-y-2">
            {migrationPlan.operations.map((op, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 p-3 bg-ableton-bg rounded-lg text-sm"
              >
                <span className={clsx(
                  'px-2 py-0.5 rounded text-xs font-medium',
                  op.type === 'archive' 
                    ? 'bg-ableton-danger/20 text-ableton-danger'
                    : 'bg-ableton-success/20 text-ableton-success'
                )}>
                  {op.type}
                </span>
                <span className="font-mono truncate flex-1">{op.source}</span>
                <ArrowRight className="w-4 h-4 text-ableton-text-muted flex-shrink-0" />
                <span className="font-mono truncate flex-1">{op.destination}</span>
              </div>
            ))}
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setMigrationPlan(null)}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
            <button
              onClick={executeMigration}
              disabled={executing}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {executing ? (
                <>Processing...</>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Execute Migration
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Migration History */}
      {migrationHistory.length > 0 && (
        <div className="card">
          <h3 className="font-semibold mb-4">Migration History</h3>
          <div className="space-y-2">
            {migrationHistory.map((manifest) => (
              <div
                key={manifest.id}
                className="flex items-center justify-between p-3 bg-ableton-bg rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <CheckCircle className={clsx(
                    'w-4 h-4',
                    manifest.status === 'completed' 
                      ? 'text-ableton-success'
                      : manifest.status === 'rolled_back'
                      ? 'text-ableton-warning'
                      : 'text-ableton-text-muted'
                  )} />
                  <div>
                    <p className="text-sm font-medium">
                      {new Date(manifest.execution_date).toLocaleDateString()}
                    </p>
                    <p className="text-xs text-ableton-text-muted font-mono">
                      {manifest.manifest_path}
                    </p>
                  </div>
                </div>
                {manifest.status === 'completed' && (
                  <button
                    onClick={() => rollbackMigration(manifest.id)}
                    className="btn-secondary text-sm flex items-center gap-1"
                  >
                    <RotateCcw className="w-3 h-3" />
                    Rollback
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && archiveProjects.length === 0 && readyProjects.length === 0 && (
        <div className="card text-center py-12">
          <FolderSync className="w-12 h-12 text-ableton-text-muted mx-auto mb-4" />
          <h3 className="font-semibold mb-2">No Projects Ready</h3>
          <p className="text-ableton-text-muted">
            Complete the Triage and Hygiene phases first
          </p>
        </div>
      )}
    </div>
  )
}

