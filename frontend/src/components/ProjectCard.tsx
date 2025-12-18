import { 
  Trash2, 
  AlertTriangle, 
  CheckCircle,
  Music,
  Clock,
  Zap
} from 'lucide-react'
import type { Project, TriageStatus } from '../types/project'
import clsx from 'clsx'

interface ProjectCardProps {
  project: Project
  isSelected: boolean
  onSelect: () => void
  onTriageUpdate: (status: TriageStatus) => void
}

export default function ProjectCard({ 
  project, 
  isSelected, 
  onSelect, 
  onTriageUpdate 
}: ProjectCardProps) {
  const getStatusBadge = () => {
    switch (project.triage_status) {
      case 'trash':
        return <span className="badge-trash">🛑 Trash</span>
      case 'salvage':
        return <span className="badge-salvage">⚠️ Salvage</span>
      case 'must_finish':
        return <span className="badge-must-finish">✅ Must Finish</span>
      default:
        return <span className="badge-untriaged">Untriaged</span>
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-ableton-success'
    if (score >= 40) return 'text-ableton-warning'
    return 'text-ableton-text-muted'
  }

  return (
    <div
      onClick={onSelect}
      className={clsx(
        'card cursor-pointer transition-all duration-200',
        isSelected 
          ? 'ring-2 ring-ableton-accent border-ableton-accent' 
          : 'hover:border-ableton-surface-light'
      )}
    >
      <div className="flex items-start gap-4">
        {/* Quick Actions - Moved to left */}
        <div className="flex flex-col gap-1 flex-shrink-0">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onTriageUpdate('trash')
            }}
            className={clsx(
              'p-2 rounded-lg transition-colors',
              project.triage_status === 'trash'
                ? 'bg-ableton-danger text-white'
                : 'bg-ableton-bg hover:bg-ableton-danger/20 text-ableton-text-muted hover:text-ableton-danger'
            )}
            title="Mark as Trash"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onTriageUpdate('salvage')
            }}
            className={clsx(
              'p-2 rounded-lg transition-colors',
              project.triage_status === 'salvage'
                ? 'bg-ableton-warning text-white'
                : 'bg-ableton-bg hover:bg-ableton-warning/20 text-ableton-text-muted hover:text-ableton-warning'
            )}
            title="Mark as Salvage"
          >
            <AlertTriangle className="w-4 h-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onTriageUpdate('must_finish')
            }}
            className={clsx(
              'p-2 rounded-lg transition-colors',
              project.triage_status === 'must_finish'
                ? 'bg-ableton-success text-white'
                : 'bg-ableton-bg hover:bg-ableton-success/20 text-ableton-text-muted hover:text-ableton-success'
            )}
            title="Mark as Must Finish"
          >
            <CheckCircle className="w-4 h-4" />
          </button>
        </div>

        {/* Score Circle */}
        <div className={clsx(
          'w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0',
          'border-2 font-bold text-lg',
          getScoreColor(project.signal_score),
          project.signal_score >= 70 
            ? 'border-ableton-success bg-ableton-success/10'
            : project.signal_score >= 40
            ? 'border-ableton-warning bg-ableton-warning/10'
            : 'border-ableton-border bg-ableton-bg'
        )}>
          {project.signal_score}
        </div>

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3 mb-2">
            <div className="min-w-0 flex-1">
              <h3 className="font-semibold truncate">{project.project_name}</h3>
              <p className="text-xs font-mono text-ableton-text-muted break-all line-clamp-2">
                {project.project_path}
              </p>
            </div>
            <div className="flex-shrink-0">
              {getStatusBadge()}
            </div>
          </div>

          {/* Metadata Row */}
          <div className="flex flex-wrap items-center gap-3 text-xs text-ableton-text-muted mb-3">
            {project.key_signature && (
              <span className="flex items-center gap-1">
                <Music className="w-3 h-3" />
                {project.key_signature}
              </span>
            )}
            {project.bpm && (
              <span className="flex items-center gap-1">
                <Zap className="w-3 h-3" />
                {project.bpm} BPM
              </span>
            )}
            {project.time_spent_days !== null && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {project.time_spent_days} days
              </span>
            )}
            {project.backup_count > 0 && (
              <span className="text-ableton-text-muted">
                {project.backup_count} backups
              </span>
            )}
          </div>

          {/* Keywords */}
          {(project.diamond_tier_keywords.length > 0 || 
            project.gold_tier_keywords.length > 0) && (
            <div className="flex flex-wrap gap-1 mb-3">
              {project.diamond_tier_keywords.map((kw) => (
                <span 
                  key={kw} 
                  className="px-1.5 py-0.5 bg-ableton-purple/20 text-ableton-purple text-xs rounded"
                >
                  💎 {kw}
                </span>
              ))}
              {project.gold_tier_keywords.map((kw) => (
                <span 
                  key={kw} 
                  className="px-1.5 py-0.5 bg-ableton-warning/20 text-ableton-warning text-xs rounded"
                >
                  🔥 {kw}
                </span>
              ))}
            </div>
          )}

          {/* Audio Preview Indicator */}
          {project.audio_preview_path && (
            <div className="flex items-center gap-1 text-xs text-ableton-accent">
              <Music className="w-3 h-3" />
              Audio preview available
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

