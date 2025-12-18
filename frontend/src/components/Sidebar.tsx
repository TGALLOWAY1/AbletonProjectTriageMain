import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Search, 
  ListTodo, 
  ClipboardCheck,
  FolderSync, 
  Music2,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import clsx from 'clsx'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard', phase: null },
  { path: '/scan', icon: Search, label: 'Deep Scan', phase: 1 },
  { path: '/triage', icon: ListTodo, label: 'Triage', phase: 2 },
  { path: '/hygiene', icon: ClipboardCheck, label: 'Hygiene', phase: 3 },
  { path: '/migration', icon: FolderSync, label: 'Migration', phase: 4 },
  { path: '/studio', icon: Music2, label: 'Studio', phase: 5 },
]

export default function Sidebar({ isOpen, onToggle }: SidebarProps) {
  return (
    <aside
      className={clsx(
        'fixed left-0 top-0 h-screen bg-ableton-surface border-r border-ableton-border',
        'flex flex-col transition-all duration-300 z-50',
        isOpen ? 'w-64' : 'w-16'
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-ableton-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-ableton-accent flex items-center justify-center">
            <Music2 className="w-5 h-5 text-white" />
          </div>
          {isOpen && (
            <div className="animate-fade-in">
              <h1 className="font-semibold text-sm">Ableton Triage</h1>
              <p className="text-xs text-ableton-text-muted">Assistant</p>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
                'hover:bg-ableton-surface-light group',
                isActive 
                  ? 'bg-ableton-accent/10 text-ableton-accent border border-ableton-accent/30' 
                  : 'text-ableton-text-muted hover:text-ableton-text'
              )
            }
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            {isOpen && (
              <span className="animate-fade-in text-sm font-medium flex-1">
                {item.label}
              </span>
            )}
            {isOpen && item.phase && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-ableton-surface-light text-ableton-text-muted">
                P{item.phase}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Toggle Button */}
      <div className="p-3 border-t border-ableton-border">
        <button
          onClick={onToggle}
          className={clsx(
            'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg',
            'text-ableton-text-muted hover:text-ableton-text',
            'hover:bg-ableton-surface-light transition-all duration-200'
          )}
        >
          {isOpen ? (
            <>
              <ChevronLeft className="w-5 h-5" />
              <span className="text-sm">Collapse</span>
            </>
          ) : (
            <ChevronRight className="w-5 h-5" />
          )}
        </button>
      </div>
    </aside>
  )
}

