import { apiClient } from './client';

export interface StravaStatus {
  connected: boolean;
  strava_athlete_id: string | null;
  last_sync_at: string | null;
  token_expires_at: string | null;
}

export interface StravaConnectResponse {
  authorization_url: string;
}

export interface StravaSyncResult {
  imported: number;
  updated: number;
  skipped: number;
  errors: Array<Record<string, unknown>>;
}

export async function getStravaStatus(): Promise<StravaStatus> {
  const response = await apiClient.get<StravaStatus>('/api/integrations/strava/status');
  return response.data;
}

export async function startStravaConnect(): Promise<StravaConnectResponse> {
  const response = await apiClient.post<StravaConnectResponse>('/api/integrations/strava/connect');
  return response.data;
}

export async function syncStravaWorkouts(): Promise<StravaSyncResult> {
  const response = await apiClient.post<StravaSyncResult>('/api/integrations/strava/sync');
  return response.data;
}

export async function disconnectStrava(): Promise<void> {
  await apiClient.post('/api/integrations/strava/disconnect');
}
