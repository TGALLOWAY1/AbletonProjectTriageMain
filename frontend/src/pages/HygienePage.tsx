import { useState, useEffect } from 'react'
import { 
  ClipboardCheck, 
  Package,
  CheckCircle2,
  ExternalLink,
  AlertTriangle,
  Loader2
} from 'lucide-react'
import { projectsApi } from '../services/api'
import type { Project
 } from '../types/project'
import clsx from 'clsx'

export default function HygienePage() {
  const [salvageProjects, setSalvageProjects] = useState<Project[]>([])
  const [mustFinishProjects, setMustFinishProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'salvage' | 'must_finish'>('salvage')

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    setLoading(true)
    try {
      const [salvageResponse, mustFinishResponse] = await Promise.all([
        projectsApi.list({ triage_status: 'salvage', hygiene_status: 'pending' }),
        projectsApi.list({ triage_status: 'must_finish', hygiene_status: 'pending' }),
      ])
      setSalvageProjects(salvageResponse.data)
      setMustFinishProjects(mustFinishResponse.data)
    } catch (error) {
      console.error('Failed to load projects:', error)
    } finally {
      setLoading(false)
    }
  }

  const markAsHarvested = async (projectId: number) => {
    try {
      await projectsApi.updateHygiene(projectId, 'harvested')
      setSalvageProjects(salvageProjects.filter(p => p.id !== projectId))
    } catch (error) {
      console.error('Failed to mark as harvested:', error)
    }
  }

  const markAsReady = async (projectId: number) => {
    try {
      await projectsApi.updateHygiene(projectId, 'ready_for_migration')
      setMustFinishProjects(mustFinishProjects.filter(p => p.id !== projectId))
    } catch (error) {
      console.error('Failed to mark as ready:', error)
    }
  }

  const openInFinder = (path: string) => {
    // Extract directory from project path
    const dir = path.substring(0, path.lastIndexOf('/'))
    // This would need a backend endpoint to actually open Finder
    window.open(`file://${dir}`, '_blank')
  }

  return (
    <div className="max-w-5xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-ableton-warning/10">
            <ClipboardCheck className="w-6 h-6 text-ableton-warning" />
          </div>
          <div>
            <span className="text-xs font-mono text-ableton-text-muted">PHASE 3</span>
            <h1 className="text-2xl font-bold">Hygiene Loop</h1>
          </div>
        </div>
        <p className="text-ableton-text-muted ml-14">
          Process files to ensure they are safe to move. The app acts as your to-do list.
        </p>
      </div>

      {/* Instructions */}
      <div className="card bg-ableton-blue/10 border-ableton-blue/30 mb-6">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-ableton-blue flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-ableton-blue mb-1">Human Work Required</p>
            <p className="text-ableton-text-muted">
              Open each project in Ableton Live and perform the required actions. 
              Mark as complete when done.
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('salvage')}
          className={clsx(
            'flex-1 py-3 px-4 rounded-lg font-medium transition-colors',
            'flex items-center justify-center gap-2',
            activeTab === 'salvage'
              ? 'bg-ableton-warning text-white'
              : 'bg-ableton-surface hover:bg-ableton-surface-light text-ableton-text-muted'
          )}
        >
          <Package className="w-4 h-4" />
          Salvage Run ({salvageProjects.length})
        </button>
        <button
          onClick={() => setActiveTab('must_finish')}
          className={clsx(
            'flex-1 py-3 px-4 rounded-lg font-medium transition-colors',
            'flex items-center justify-center gap-2',
            activeTab === 'must_finish'
              ? 'bg-ableton-success text-white'
              : 'bg-ableton-surface hover:bg-ableton-surface-light text-ableton-text-muted'
          )}
        >
          <CheckCircle2 className="w-4 h-4" />
          Must Finish Run ({mustFinishProjects.length})
        </button>
      </div>

      {/* Salvage Tab */}
      {activeTab === 'salvage' && (
        <div>
          <div className="card mb-4">
            <h3 className="font-semibold mb-2">Salvage Workflow</h3>
            <ol className="list-decimal list-inside text-sm text-ableton-text-muted space-y-1">
              <li>Open project in Ableton Live</li>
              <li>Render any valuable loops to your User Library</li>
              <li>Save any good presets or racks</li>
              <li>Close the project</li>
              <li>Click "Mark as Harvested" below</li>
            </ol>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-ableton-text-muted" />
            </div>
          ) : salvageProjects.length === 0 ? (
            <div className="card text-center py-12">
              <Package className="w-12 h-12 text-ableton-text-muted mx-auto mb-4" />
              <h3 className="font-semibold mb-2">No Salvage Projects</h3>
              <p className="text-ableton-text-muted">
                All salvage projects have been harvested
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {salvageProjects.map((project) => (
                <div key={project.id} className="card">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium truncate">{project.project_name}</h4>
                      <p className="text-xs font-mono text-ableton-text-muted truncate">
                        {project.project_path}
                      </p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-ableton-text-muted">
                        {project.key_signature && <span>Key: {project.key_signature}</span>}
                        {project.bpm && <span>BPM: {project.bpm}</span>}
                        <span className="text-ableton-warning">Score: {project.signal_score}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => openInFinder(project.project_path)}
                        className="btn-secondary text-sm flex items-center gap-1"
                      >
                        <ExternalLink className="w-3 h-3" />
                        Open
                      </button>
                      <button
                        onClick={() => markAsHarvested(project.id)}
                        className="btn-primary text-sm flex items-center gap-1"
                      >
                        <CheckCircle2 className="w-3 h-3" />
                        Harvested
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Must Finish Tab */}
      {activeTab === 'must_finish' && (
        <div>
          <div className="card mb-4">
            <h3 className="font-semibold mb-2">Must Finish Workflow</h3>
            <ol className="list-decimal list-inside text-sm text-ableton-text-muted space-y-1">
              <li>Open project in Ableton Live</li>
              <li>Go to <span className="font-mono bg-ableton-bg px-1 rounded">File → Collect All and Save</span></li>
              <li>Export a fresh reference mix (optional but recommended)</li>
              <li>Close the project</li>
              <li>Click "Ready for Migration" below</li>
            </ol>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <Loader2 className="w-8 h-8 animate-spin mx-auto text-ableton-text-muted" />
            </div>
          ) : mustFinishProjects.length === 0 ? (
            <div className="card text-center py-12">
              <CheckCircle2 className="w-12 h-12 text-ableton-text-muted mx-auto mb-4" />
              <h3 className="font-semibold mb-2">No Pending Projects</h3>
              <p className="text-ableton-text-muted">
                All Must Finish projects are ready for migration
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {mustFinishProjects.map((project) => (
                <div key={project.id} className="card">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium truncate">{project.project_name}</h4>
                      <p className="text-xs font-mono text-ableton-text-muted truncate">
                        {project.project_path}
                      </p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-ableton-text-muted">
                        {project.key_signature && <span>Key: {project.key_signature}</span>}
                        {project.bpm && <span>BPM: {project.bpm}</span>}
                        <span className="text-ableton-success">Score: {project.signal_score}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => openInFinder(project.project_path)}
                        className="btn-secondary text-sm flex items-center gap-1"
                      >
                        <ExternalLink className="w-3 h-3" />
                        Open
                      </button>
                      <button
                        onClick={() => markAsReady(project.id)}
                        className="btn-success text-sm flex items-center gap-1"
                      >
                        <CheckCircle2 className="w-3 h-3" />
                        Ready
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

