import { useState, useEffect } from 'react'
import { 
  Music2, 
  GripVertical,
  Tag,
  Plus,
  X,
  Edit2,
  Save
} from 'lucide-react'
import { studioApi } from '../services/api'
import type { StudioProject, ProductionTag } from '../types/project'
import clsx from 'clsx'

const PRODUCTION_TAGS: { value: ProductionTag; label: string; color: string }[] = [
  { value: 'needs_arrangement', label: 'Needs Arrangement', color: 'ableton-purple' },
  { value: 'needs_mixing', label: 'Needs Mixing', color: 'ableton-blue' },
  { value: 'needs_mastering', label: 'Needs Mastering', color: 'ableton-accent' },
  { value: 'needs_vocal_recording', label: 'Needs Vocals', color: 'ableton-warning' },
  { value: 'needs_sound_design', label: 'Needs Sound Design', color: 'ableton-text-muted' },
  { value: 'ready_to_release', label: 'Ready to Release', color: 'ableton-success' },
]

const GENRES = ['Dubstep', 'House', 'Techno', 'Drum & Bass', 'Hip Hop', 'Ambient', 'Other']

export default function StudioPage() {
  const [projects, setProjects] = useState<StudioProject[]>([])
  const [loading, setLoading] = useState(true)
  const [editingNotes, setEditingNotes] = useState<number | null>(null)
  const [notesDraft, setNotesDraft] = useState('')
  const [genreFilter, setGenreFilter] = useState<string | 'all'>('all')

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    setLoading(true)
    try {
      const response = await studioApi.list()
      setProjects(response.data.sort((a, b) => a.priority_order - b.priority_order))
    } catch (error) {
      console.error('Failed to load studio projects:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTagToggle = async (projectId: number, tag: ProductionTag) => {
    const project = projects.find(p => p.id === projectId)
    if (!project) return

    const currentTags = project.production_tags
    const newTags = currentTags.includes(tag)
      ? currentTags.filter(t => t !== tag)
      : [...currentTags, tag]

    try {
      await studioApi.updateTags(projectId, newTags)
      setProjects(projects.map(p => 
        p.id === projectId ? { ...p, production_tags: newTags } : p
      ))
    } catch (error) {
      console.error('Failed to update tags:', error)
    }
  }

  const handleGenreChange = async (projectId: number, genre: string) => {
    try {
      await studioApi.updateGenre(projectId, genre)
      setProjects(projects.map(p => 
        p.id === projectId ? { ...p, genre } : p
      ))
    } catch (error) {
      console.error('Failed to update genre:', error)
    }
  }

  const handleSaveNotes = async (projectId: number) => {
    try {
      await studioApi.updateNotes(projectId, notesDraft)
      setProjects(projects.map(p => 
        p.id === projectId ? { ...p, notes: notesDraft } : p
      ))
      setEditingNotes(null)
    } catch (error) {
      console.error('Failed to save notes:', error)
    }
  }

  const startEditingNotes = (project: StudioProject) => {
    setEditingNotes(project.id)
    setNotesDraft(project.notes || '')
  }

  const filteredProjects = genreFilter === 'all'
    ? projects
    : projects.filter(p => p.genre === genreFilter)

  const uniqueGenres = [...new Set(projects.map(p => p.genre).filter(Boolean))]

  return (
    <div className="max-w-5xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-ableton-success/10">
            <Music2 className="w-6 h-6 text-ableton-success" />
          </div>
          <div>
            <span className="text-xs font-mono text-ableton-text-muted">PHASE 5</span>
            <h1 className="text-2xl font-bold">Studio Manager</h1>
          </div>
        </div>
        <p className="text-ableton-text-muted ml-14">
          Track and prioritize your active projects
        </p>
      </div>

      {/* Genre Filter */}
      {uniqueGenres.length > 0 && (
        <div className="card mb-6">
          <div className="flex items-center gap-3">
            <Tag className="w-4 h-4 text-ableton-text-muted" />
            <span className="text-sm text-ableton-text-muted">Filter by genre:</span>
            <div className="flex gap-2">
              <button
                onClick={() => setGenreFilter('all')}
                className={clsx(
                  'px-3 py-1 rounded-lg text-sm transition-colors',
                  genreFilter === 'all'
                    ? 'bg-ableton-accent text-white'
                    : 'bg-ableton-bg hover:bg-ableton-surface-light'
                )}
              >
                All
              </button>
              {uniqueGenres.map((genre) => (
                <button
                  key={genre}
                  onClick={() => setGenreFilter(genre)}
                  className={clsx(
                    'px-3 py-1 rounded-lg text-sm transition-colors',
                    genreFilter === genre
                      ? 'bg-ableton-accent text-white'
                      : 'bg-ableton-bg hover:bg-ableton-surface-light'
                  )}
                >
                  {genre}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Project List */}
      {loading ? (
        <div className="text-center py-12 text-ableton-text-muted">
          Loading projects...
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="card text-center py-12">
          <Music2 className="w-12 h-12 text-ableton-text-muted mx-auto mb-4" />
          <h3 className="font-semibold mb-2">No Studio Projects</h3>
          <p className="text-ableton-text-muted">
            Complete the Migration phase to populate your studio
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredProjects.map((project, index) => (
            <div key={project.id} className="card">
              <div className="flex gap-4">
                {/* Drag Handle */}
                <div className="flex-shrink-0 cursor-grab active:cursor-grabbing">
                  <GripVertical className="w-5 h-5 text-ableton-text-muted" />
                </div>

                {/* Priority Number */}
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-ableton-accent/10 flex items-center justify-center">
                  <span className="text-sm font-bold text-ableton-accent">
                    {index + 1}
                  </span>
                </div>

                {/* Main Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div>
                      <h3 className="font-semibold">{project.project.project_name}</h3>
                      <p className="text-xs font-mono text-ableton-text-muted truncate">
                        {project.project.project_path}
                      </p>
                    </div>

                    {/* Genre Selector */}
                    <select
                      value={project.genre}
                      onChange={(e) => handleGenreChange(project.id, e.target.value)}
                      className="input w-32 text-sm"
                    >
                      {GENRES.map((genre) => (
                        <option key={genre} value={genre}>{genre}</option>
                      ))}
                    </select>
                  </div>

                  {/* Metadata */}
                  <div className="flex gap-4 mb-3 text-sm">
                    {project.project.key_signature && (
                      <span className="text-ableton-text-muted">
                        Key: <span className="text-ableton-text">{project.project.key_signature}</span>
                      </span>
                    )}
                    {project.project.bpm && (
                      <span className="text-ableton-text-muted">
                        BPM: <span className="text-ableton-text">{project.project.bpm}</span>
                      </span>
                    )}
                    <span className="text-ableton-text-muted">
                      Score: <span className="text-ableton-accent">{project.project.signal_score}</span>
                    </span>
                  </div>

                  {/* Production Tags */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    {PRODUCTION_TAGS.map((tag) => {
                      const isActive = project.production_tags.includes(tag.value)
                      return (
                        <button
                          key={tag.value}
                          onClick={() => handleTagToggle(project.id, tag.value)}
                          className={clsx(
                            'px-2 py-1 rounded-lg text-xs font-medium transition-all',
                            'flex items-center gap-1',
                            isActive
                              ? `bg-${tag.color}/20 text-${tag.color} border border-${tag.color}/30`
                              : 'bg-ableton-bg text-ableton-text-muted hover:bg-ableton-surface-light'
                          )}
                        >
                          {isActive ? <X className="w-3 h-3" /> : <Plus className="w-3 h-3" />}
                          {tag.label}
                        </button>
                      )
                    })}
                  </div>

                  {/* Notes */}
                  {editingNotes === project.id ? (
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={notesDraft}
                        onChange={(e) => setNotesDraft(e.target.value)}
                        placeholder="Add notes..."
                        className="input flex-1 text-sm"
                        autoFocus
                      />
                      <button
                        onClick={() => handleSaveNotes(project.id)}
                        className="btn-primary px-3"
                      >
                        <Save className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setEditingNotes(null)}
                        className="btn-secondary px-3"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => startEditingNotes(project)}
                      className="text-sm text-ableton-text-muted hover:text-ableton-text flex items-center gap-1"
                    >
                      <Edit2 className="w-3 h-3" />
                      {project.notes || 'Add notes...'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

