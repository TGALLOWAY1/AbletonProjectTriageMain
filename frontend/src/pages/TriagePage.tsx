import { useState, useEffect } from 'react'
import { 
  ListTodo, 
  Filter,
  SortAsc,
  Search,
  Trash2,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'
import { projectsApi } from '../services/api'
import type { Project, TriageStatus, ProjectFilters } from '../types/project'
import ProjectCard from '../components/ProjectCard'
import AudioPlayer from '../components/AudioPlayer'
import clsx from 'clsx'

const TRIAGE_FILTERS: { value: TriageStatus | 'all'; label: string; icon: React.ElementType }[] = [
  { value: 'all', label: 'All', icon: ListTodo },
  { value: 'untriaged', label: 'Untriaged', icon: Search },
  { value: 'trash', label: 'Trash', icon: Trash2 },
  { value: 'salvage', label: 'Salvage', icon: AlertTriangle },
  { value: 'must_finish', label: 'Must Finish', icon: CheckCircle },
]

const SORT_OPTIONS = [
  { value: 'signal_score', label: 'Signal Score' },
  { value: 'name', label: 'Name' },
  { value: 'updated_at', label: 'Last Updated' },
  { value: 'time_spent_days', label: 'Time Spent' },
]

export default function TriagePage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [filters, setFilters] = useState<ProjectFilters>({
    triage_status: 'all',
    sort_by: 'signal_score',
    sort_order: 'desc',
  })
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadProjects()
  }, [filters])

  const loadProjects = async () => {
    setLoading(true)
    try {
      const response = await projectsApi.list({
        ...filters,
        search: searchQuery || undefined,
      })
      setProjects(response.data)
    } catch (error) {
      console.error('Failed to load projects:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTriageUpdate = async (projectId: number, status: TriageStatus) => {
    try {
      await projectsApi.updateTriage(projectId, status)
      setProjects(projects.map(p => 
        p.id === projectId ? { ...p, triage_status: status } : p
      ))
      if (selectedProject?.id === projectId) {
        setSelectedProject({ ...selectedProject, triage_status: status })
      }
    } catch (error) {
      console.error('Failed to update triage status:', error)
    }
  }

  const filteredProjects = projects.filter(p => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        p.project_name.toLowerCase().includes(query) ||
        p.project_path.toLowerCase().includes(query)
      )
    }
    return true
  })

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-ableton-purple/10">
            <ListTodo className="w-6 h-6 text-ableton-purple" />
          </div>
          <div>
            <span className="text-xs font-mono text-ableton-text-muted">PHASE 2</span>
            <h1 className="text-2xl font-bold">Virtual Triage</h1>
          </div>
        </div>
        <p className="text-ableton-text-muted ml-14">
          Review and tag your projects. No files move yet.
        </p>
      </div>

      {/* Filters Bar */}
      <div className="card mb-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-ableton-text-muted" />
            <div className="flex gap-1">
              {TRIAGE_FILTERS.map((filter) => (
                <button
                  key={filter.value}
                  onClick={() => setFilters({ ...filters, triage_status: filter.value })}
                  className={clsx(
                    'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                    'flex items-center gap-1.5',
                    filters.triage_status === filter.value
                      ? 'bg-ableton-accent text-white'
                      : 'bg-ableton-bg hover:bg-ableton-surface-light text-ableton-text-muted'
                  )}
                >
                  <filter.icon className="w-3.5 h-3.5" />
                  {filter.label}
                </button>
              ))}
            </div>
          </div>

          {/* Sort */}
          <div className="flex items-center gap-2 ml-auto">
            <SortAsc className="w-4 h-4 text-ableton-text-muted" />
            <select
              value={filters.sort_by}
              onChange={(e) => setFilters({ ...filters, sort_by: e.target.value as ProjectFilters['sort_by'] })}
              className="input w-40"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <button
              onClick={() => setFilters({ 
                ...filters, 
                sort_order: filters.sort_order === 'asc' ? 'desc' : 'asc' 
              })}
              className="btn-secondary px-2"
            >
              {filters.sort_order === 'asc' ? '↑' : '↓'}
            </button>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ableton-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search projects..."
              className="input pl-9 w-64"
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex gap-6">
        {/* Project List */}
        <div className="flex-1">
          {loading ? (
            <div className="text-center py-12 text-ableton-text-muted">
              Loading projects...
            </div>
          ) : filteredProjects.length === 0 ? (
            <div className="card text-center py-12">
              <ListTodo className="w-12 h-12 text-ableton-text-muted mx-auto mb-4" />
              <h3 className="font-semibold mb-2">No Projects Found</h3>
              <p className="text-ableton-text-muted">
                {projects.length === 0 
                  ? 'Run a Deep Scan to discover projects'
                  : 'No projects match your filters'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredProjects.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  isSelected={selectedProject?.id === project.id}
                  onSelect={() => setSelectedProject(project)}
                  onTriageUpdate={(status) => handleTriageUpdate(project.id, status)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Preview Panel */}
        {selectedProject && (
          <div className="w-96 flex-shrink-0">
            <div className="card sticky top-6">
              <h3 className="font-semibold mb-4">Preview</h3>
              
              {/* Project Info */}
              <div className="mb-4">
                <h4 className="text-lg font-medium mb-1">{selectedProject.project_name}</h4>
                <p className="text-xs font-mono text-ableton-text-muted truncate">
                  {selectedProject.project_path}
                </p>
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                {selectedProject.key_signature && (
                  <div className="p-2 bg-ableton-bg rounded-lg">
                    <p className="text-xs text-ableton-text-muted">Key</p>
                    <p className="font-mono font-medium">{selectedProject.key_signature}</p>
                  </div>
                )}
                {selectedProject.bpm && (
                  <div className="p-2 bg-ableton-bg rounded-lg">
                    <p className="text-xs text-ableton-text-muted">BPM</p>
                    <p className="font-mono font-medium">{selectedProject.bpm}</p>
                  </div>
                )}
                <div className="p-2 bg-ableton-bg rounded-lg">
                  <p className="text-xs text-ableton-text-muted">Signal Score</p>
                  <p className="font-mono font-medium text-ableton-accent">
                    {selectedProject.signal_score}
                  </p>
                </div>
                {selectedProject.time_spent_days !== null && (
                  <div className="p-2 bg-ableton-bg rounded-lg">
                    <p className="text-xs text-ableton-text-muted">Time Spent</p>
                    <p className="font-mono font-medium">
                      {selectedProject.time_spent_days} days
                    </p>
                  </div>
                )}
              </div>

              {/* Keywords */}
              {(selectedProject.diamond_tier_keywords.length > 0 || 
                selectedProject.gold_tier_keywords.length > 0) && (
                <div className="mb-4">
                  <p className="text-xs text-ableton-text-muted mb-2">Keywords</p>
                  <div className="flex flex-wrap gap-1">
                    {selectedProject.diamond_tier_keywords.map((kw) => (
                      <span key={kw} className="px-2 py-0.5 bg-ableton-purple/20 text-ableton-purple text-xs rounded">
                        💎 {kw}
                      </span>
                    ))}
                    {selectedProject.gold_tier_keywords.map((kw) => (
                      <span key={kw} className="px-2 py-0.5 bg-ableton-warning/20 text-ableton-warning text-xs rounded">
                        🔥 {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Audio Player */}
              {selectedProject.audio_preview_path && (
                <AudioPlayer projectId={selectedProject.id} />
              )}

              {/* Triage Actions */}
              <div className="border-t border-ableton-border pt-4 mt-4">
                <p className="text-xs text-ableton-text-muted mb-2">Triage Action</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleTriageUpdate(selectedProject.id, 'trash')}
                    className={clsx(
                      'flex-1 py-2 rounded-lg font-medium transition-colors',
                      selectedProject.triage_status === 'trash'
                        ? 'bg-ableton-danger text-white'
                        : 'bg-ableton-bg hover:bg-ableton-danger/20 text-ableton-text-muted'
                    )}
                  >
                    🛑 Trash
                  </button>
                  <button
                    onClick={() => handleTriageUpdate(selectedProject.id, 'salvage')}
                    className={clsx(
                      'flex-1 py-2 rounded-lg font-medium transition-colors',
                      selectedProject.triage_status === 'salvage'
                        ? 'bg-ableton-warning text-white'
                        : 'bg-ableton-bg hover:bg-ableton-warning/20 text-ableton-text-muted'
                    )}
                  >
                    ⚠️ Salvage
                  </button>
                  <button
                    onClick={() => handleTriageUpdate(selectedProject.id, 'must_finish')}
                    className={clsx(
                      'flex-1 py-2 rounded-lg font-medium transition-colors',
                      selectedProject.triage_status === 'must_finish'
                        ? 'bg-ableton-success text-white'
                        : 'bg-ableton-bg hover:bg-ableton-success/20 text-ableton-text-muted'
                    )}
                  >
                    ✅ Finish
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

