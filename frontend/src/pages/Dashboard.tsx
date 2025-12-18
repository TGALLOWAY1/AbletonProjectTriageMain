import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { 
  Search, 
  ListTodo, 
  ClipboardCheck,
  FolderSync, 
  Music2,
  TrendingUp,
  Clock,
  FolderOpen,
  Zap
} from 'lucide-react'
import { projectsApi } from '../services/api'
import type { ProjectStats } from '../types/project'

export default function Dashboard() {
  const [stats, setStats] = useState<ProjectStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const response = await projectsApi.getStats()
      setStats(response.data)
    } catch {
      // Stats not available yet - likely no projects scanned
      setStats(null)
    } finally {
      setLoading(false)
    }
  }

  const phases = [
    {
      number: 1,
      title: 'Deep Scan',
      description: 'Index your Ableton projects without moving files',
      icon: Search,
      path: '/scan',
      color: 'ableton-accent',
      ready: true,
    },
    {
      number: 2,
      title: 'Virtual Triage',
      description: 'Review and tag your projects',
      icon: ListTodo,
      path: '/triage',
      color: 'ableton-purple',
      ready: stats ? stats.total > 0 : false,
    },
    {
      number: 3,
      title: 'Hygiene Loop',
      description: 'Prepare files for safe migration',
      icon: ClipboardCheck,
      path: '/hygiene',
      color: 'ableton-warning',
      ready: stats ? (stats.salvage > 0 || stats.must_finish > 0) : false,
    },
    {
      number: 4,
      title: 'Grand Migration',
      description: 'Organize your files safely',
      icon: FolderSync,
      path: '/migration',
      color: 'ableton-blue',
      ready: stats ? stats.ready_for_migration > 0 : false,
    },
    {
      number: 5,
      title: 'Studio Manager',
      description: 'Track your active projects',
      icon: Music2,
      path: '/studio',
      color: 'ableton-success',
      ready: stats ? stats.must_finish > 0 : false,
    },
  ]

  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Welcome Back</h1>
        <p className="text-ableton-text-muted">
          Your Ableton project organization hub
        </p>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={FolderOpen}
            label="Total Projects"
            value={stats.total}
            color="ableton-accent"
          />
          <StatCard
            icon={Clock}
            label="Untriaged"
            value={stats.untriaged}
            color="ableton-text-muted"
          />
          <StatCard
            icon={Zap}
            label="Must Finish"
            value={stats.must_finish}
            color="ableton-success"
          />
          <StatCard
            icon={TrendingUp}
            label="Avg. Score"
            value={Math.round(stats.average_score)}
            color="ableton-purple"
          />
        </div>
      )}

      {/* Phase Cards */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">Workflow Phases</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {phases.map((phase) => (
            <Link
              key={phase.number}
              to={phase.path}
              className={`card group ${!phase.ready && 'opacity-50'}`}
            >
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-xl bg-${phase.color}/10`}>
                  <phase.icon className={`w-6 h-6 text-${phase.color}`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-ableton-text-muted">
                      PHASE {phase.number}
                    </span>
                    {!phase.ready && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-ableton-surface-light text-ableton-text-muted">
                        Locked
                      </span>
                    )}
                  </div>
                  <h3 className="font-semibold mb-1 group-hover:text-ableton-accent transition-colors">
                    {phase.title}
                  </h3>
                  <p className="text-sm text-ableton-text-muted">
                    {phase.description}
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Quick Start */}
      {(!stats || stats.total === 0) && !loading && (
        <div className="card border-dashed border-2 border-ableton-border bg-transparent">
          <div className="text-center py-8">
            <Search className="w-12 h-12 text-ableton-accent mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Get Started</h3>
            <p className="text-ableton-text-muted mb-4">
              Scan your directories to discover Ableton projects
            </p>
            <Link to="/scan" className="btn-primary inline-flex items-center gap-2">
              <Search className="w-4 h-4" />
              Start Deep Scan
            </Link>
          </div>
        </div>
      )}

      {/* Progress Overview */}
      {stats && stats.total > 0 && (
        <div className="card">
          <h3 className="font-semibold mb-4">Triage Progress</h3>
          <div className="space-y-3">
            <ProgressBar
              label="Trash"
              value={stats.trash}
              total={stats.total}
              color="bg-ableton-danger"
            />
            <ProgressBar
              label="Salvage"
              value={stats.salvage}
              total={stats.total}
              color="bg-ableton-warning"
            />
            <ProgressBar
              label="Must Finish"
              value={stats.must_finish}
              total={stats.total}
              color="bg-ableton-success"
            />
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ 
  icon: Icon, 
  label, 
  value, 
  color 
}: { 
  icon: React.ElementType
  label: string
  value: number
  color: string 
}) {
  return (
    <div className="card">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg bg-${color}/10`}>
          <Icon className={`w-5 h-5 text-${color}`} />
        </div>
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-xs text-ableton-text-muted">{label}</p>
        </div>
      </div>
    </div>
  )
}

function ProgressBar({ 
  label, 
  value, 
  total, 
  color 
}: { 
  label: string
  value: number
  total: number
  color: string 
}) {
  const percentage = total > 0 ? (value / total) * 100 : 0

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-ableton-text-muted">{label}</span>
        <span>{value} / {total}</span>
      </div>
      <div className="h-2 bg-ableton-bg rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

