/**
 * TypeScript interfaces for Ableton Triage Assistant
 */

export type TriageStatus = 'untriaged' | 'trash' | 'salvage' | 'must_finish'
export type HygieneStatus = 'pending' | 'harvested' | 'ready_for_migration'
export type MigrationStatus = 'pending' | 'completed' | 'rolled_back'

export interface Project {
  id: number
  project_path: string
  project_name: string
  key_signature: string | null
  bpm: number | null
  signal_score: number
  triage_status: TriageStatus
  hygiene_status: HygieneStatus
  cluster_id: string | null
  time_spent_days: number | null
  diamond_tier_keywords: string[]
  gold_tier_keywords: string[]
  audio_preview_path: string | null
  backup_count: number
  created_at: string
  updated_at: string
}

export interface StudioProject {
  id: number
  project_id: number
  project: Project
  genre: string
  production_tags: ProductionTag[]
  priority_order: number
  notes: string | null
}

export type ProductionTag = 
  | 'needs_arrangement'
  | 'needs_mixing'
  | 'needs_mastering'
  | 'needs_vocal_recording'
  | 'needs_sound_design'
  | 'ready_to_release'

export interface MigrationManifest {
  id: number
  manifest_path: string
  execution_date: string
  status: MigrationStatus
}

export interface MigrationOperation {
  source: string
  destination: string
  type: 'archive' | 'curated'
  status: 'pending' | 'completed' | 'failed'
  error?: string
}

export interface MigrationPlan {
  timestamp: string
  operations: MigrationOperation[]
  archive_destination: string
  curated_destination: string
}

export interface ScanProgress {
  status: 'idle' | 'scanning' | 'completed' | 'error'
  current_path: string | null
  files_scanned: number
  projects_found: number
  errors: ScanError[]
  started_at: string | null
  completed_at: string | null
}

export interface ScanError {
  path: string
  error: string
  timestamp: string
}

export interface ScanRequest {
  paths: string[]
}

export interface ProjectFilters {
  triage_status?: TriageStatus | 'all'
  hygiene_status?: HygieneStatus | 'all'
  min_score?: number
  max_score?: number
  search?: string
  sort_by?: 'signal_score' | 'name' | 'updated_at' | 'time_spent_days'
  sort_order?: 'asc' | 'desc'
}

export interface ProjectStats {
  total: number
  untriaged: number
  trash: number
  salvage: number
  must_finish: number
  pending_harvest: number
  ready_for_migration: number
  average_score: number
}

