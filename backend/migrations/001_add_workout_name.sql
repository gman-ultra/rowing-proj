-- Migration: 001_add_workout_name
-- Adds workout_name VARCHAR(120) to the workouts table for existing
-- PostgreSQL / Neon databases created before the column was added to
-- the Workout model.
--
-- Idempotent: safe to run multiple times.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'workouts'
      AND column_name = 'workout_name'
  ) THEN
    ALTER TABLE workouts ADD COLUMN workout_name VARCHAR(120);
  END IF;
END $$;
