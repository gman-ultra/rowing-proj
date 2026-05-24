import { apiClient } from './client';

export interface WorkoutCreatePayload {
  workout_date?: string;
  workout_name?: string;
  duration_seconds: number;
  distance_meters: number;
  stroke_rate?: number;
  avg_heart_rate?: number;
  avg_watts?: number;
  calories?: number;
  notes?: string;
  visibility?: 'private' | 'team';
  team_id?: string;
}

export interface WorkoutUpdatePayload {
  workout_date?: string;
  workout_name?: string | null;
  duration_seconds?: number;
  distance_meters?: number;
  stroke_rate?: number | null;
  avg_heart_rate?: number | null;
  avg_watts?: number | null;
  calories?: number | null;
  notes?: string | null;
  visibility?: 'private' | 'team';
  team_id?: string | null;
}

export interface Workout {
  id: string;
  user_id: string;
  team_id: string | null;
  workout_date: string;
  workout_name: string | null;
  duration_seconds: number | null;
  distance_meters: number | null;
  stroke_rate: number | null;
  avg_split_500m: number | null;
  avg_heart_rate: number | null;
  avg_watts: number | null;
  calories: number | null;
  notes: string | null;
  source: string;
  source_id: string | null;
  visibility: string;
  created_at: string;
  updated_at: string;
}

export interface WorkoutListResponse {
  workouts: Workout[];
}

export async function createWorkout(data: WorkoutCreatePayload): Promise<Workout> {
  const response = await apiClient.post<Workout>('/api/workouts', data);
  return response.data;
}

export async function listWorkouts(): Promise<WorkoutListResponse> {
  const response = await apiClient.get<WorkoutListResponse>('/api/workouts');
  return response.data;
}

export async function getWorkout(workoutId: string): Promise<Workout> {
  const response = await apiClient.get<Workout>(`/api/workouts/${workoutId}`);
  return response.data;
}

export async function updateWorkout(workoutId: string, data: WorkoutUpdatePayload): Promise<Workout> {
  const response = await apiClient.patch<Workout>(`/api/workouts/${workoutId}`, data);
  return response.data;
}

export async function deleteWorkout(workoutId: string): Promise<void> {
  await apiClient.delete(`/api/workouts/${workoutId}`);
}
