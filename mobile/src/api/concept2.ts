import { apiClient } from './client';

export interface Concept2Status {
  connected: boolean;
  concept2_user_id: string | null;
  last_sync_at: string | null;
  token_expires_at: string | null;
}

export interface Concept2ConnectResponse {
  authorization_url: string;
}

export interface Concept2SyncResult {
  imported: number;
  updated: number;
  skipped: number;
  errors: Array<Record<string, unknown>>;
}

export async function getConcept2Status(): Promise<Concept2Status> {
  const response = await apiClient.get<Concept2Status>('/api/integrations/concept2/status');
  return response.data;
}

export async function startConcept2Connect(): Promise<Concept2ConnectResponse> {
  const response = await apiClient.post<Concept2ConnectResponse>('/api/integrations/concept2/connect');
  return response.data;
}

export async function syncConcept2Workouts(): Promise<Concept2SyncResult> {
  const response = await apiClient.post<Concept2SyncResult>('/api/integrations/concept2/sync');
  return response.data;
}

export async function disconnectConcept2(): Promise<void> {
  await apiClient.post('/api/integrations/concept2/disconnect');
}
