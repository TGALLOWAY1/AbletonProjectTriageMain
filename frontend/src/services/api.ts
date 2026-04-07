/**
 * API client for Ableton Triage Assistant backend
 */

import axios from 'axios'
import type {
  Project,
  StudioProject,
  ScanProgress,
  ScanRequest,
  ProjectFilters,
  ProjectStats,
  MigrationPlan,
  MigrationManifest,
  TriageStatus,
  HygieneStatus,
  ProductionTag,
} from '../types/project'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Scan API
export const scanApi = {
  start: (request: ScanRequest) => 
    api.post<{ message: string }>('/scan/start', request),
  
  getStatus: () => 
    api.get<ScanProgress>('/scan/status'),
  
  getResults: () => 
    api.get<Project[]>('/scan/results'),
  
  cancel: () => 
    api.post<{ message: string }>('/scan/cancel'),
  
  reset: () => 
    api.post<{ message: string }>('/scan/reset'),
}

// Projects API
export const projectsApi = {
  list: (filters?: ProjectFilters) => 
    api.get<Project[]>('/projects', { params: filters }),
  
  get: (id: number) => 
    api.get<Project>(`/projects/${id}`),
  
  getStats: () => 
    api.get<ProjectStats>('/projects/stats'),
  
  updateTriage: (id: number, status: TriageStatus) => 
    api.put<Project>(`/projects/${id}/triage`, { status }),
  
  updateHygiene: (id: number, status: HygieneStatus) => 
    api.put<Project>(`/projects/${id}/hygiene`, { status }),
  
  delete: (id: number) => 
    api.delete<{ message: string }>(`/projects/${id}`),
}

// Audio API
export const audioApi = {
  getPreviewUrl: (projectId: number) => 
    `/api/audio/stream/${projectId}`,
  
  checkPreview: (projectId: number) => 
    api.get<{ available: boolean; path: string | null }>(`/audio/preview/${projectId}`),
}

// Migration API
export const migrationApi = {
  preview: (archivePath: string, curatedPath: string) => 
    api.post<MigrationPlan>('/migration/preview', { 
      archive_destination: archivePath,
      curated_destination: curatedPath,
    }),
  
  execute: (archivePath: string, curatedPath: string, manifestPath?: string) =>
    api.post<{ message: string; manifest_id: number }>('/migration/execute', {
      archive_destination: archivePath,
      curated_destination: curatedPath,
      ...(manifestPath && { manifest_path: manifestPath }),
    }),
  
  rollback: (manifestId: number) => 
    api.post<{ message: string }>('/migration/rollback', { 
      manifest_id: manifestId,
    }),
  
  getHistory: () => 
    api.get<MigrationManifest[]>('/migration/history'),
  
  validateDependencies: (projectId: number) => 
    api.get<{ valid: boolean; external_refs: string[] }>(`/migration/validate/${projectId}`),
}

// Studio API
export const studioApi = {
  list: () => 
    api.get<StudioProject[]>('/studio/projects'),
  
  get: (id: number) => 
    api.get<StudioProject>(`/studio/projects/${id}`),
  
  updateTags: (id: number, tags: ProductionTag[]) => 
    api.put<StudioProject>(`/studio/projects/${id}/tags`, { tags }),
  
  updatePriority: (id: number, priority: number) => 
    api.put<StudioProject>(`/studio/projects/${id}/priority`, { priority_order: priority }),
  
  updateGenre: (id: number, genre: string) => 
    api.put<StudioProject>(`/studio/projects/${id}/genre`, { genre }),
  
  updateNotes: (id: number, notes: string) => 
    api.put<StudioProject>(`/studio/projects/${id}/notes`, { notes }),
  
  reorder: (projectIds: number[]) => 
    api.post<{ message: string }>('/studio/projects/reorder', { project_ids: projectIds }),
}

// Settings API
export const settingsApi = {
  getScanPaths: () => 
    api.get<Array<{ id: number; path: string; created_at: string }>>('/settings/scan-paths'),
  
  addScanPath: (path: string) => 
    api.post<{ id: number; path: string; created_at: string }>('/settings/scan-paths', { path }),
  
  deleteScanPath: (pathId: number) => 
    api.delete<{ message: string }>(`/settings/scan-paths/${pathId}`),
  
  deleteScanPathByPath: (path: string) => 
    api.delete<{ message: string; deleted: boolean }>('/settings/scan-paths', { params: { path } }),
}

export default api

