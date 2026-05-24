import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { getWorkout, updateWorkout } from '../api/workouts';
import type { AppStackParamList } from '../navigation/types';
import {
  buildLocalNoonWorkoutDate,
  formatDuration,
  getWorkoutDateInputValue,
  isValidDateInput,
  parseDurationToSeconds,
  parsePositiveInteger,
  parsePositiveNumber,
} from '../utils/workoutFormat';

type Props = NativeStackScreenProps<AppStackParamList, 'EditWorkout'>;

function getErrorMessage(err: any, fallback: string): string {
  const data = err.response?.data;
  if (typeof data?.detail === 'string') return data.detail;
  if (Array.isArray(data?.detail)) return data.detail[0]?.msg || fallback;
  if (typeof data?.message === 'string') return data.message;
  return fallback;
}

export default function EditWorkoutScreen({ navigation, route }: Props) {
  const { workoutId } = route.params;
  const [workoutName, setWorkoutName] = useState('');
  const [workoutDate, setWorkoutDate] = useState('');
  const [duration, setDuration] = useState('');
  const [distance, setDistance] = useState('');
  const [strokeRate, setStrokeRate] = useState('');
  const [avgHr, setAvgHr] = useState('');
  const [watts, setWatts] = useState('');
  const [calories, setCalories] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadWorkout() {
      setLoading(true);
      setError('');
      try {
        const workout = await getWorkout(workoutId);
        if (!active) return;
        setWorkoutName(workout.workout_name ?? '');
        setWorkoutDate(getWorkoutDateInputValue(workout.workout_date));
        setDuration(workout.duration_seconds != null ? formatDuration(workout.duration_seconds) : '');
        setDistance(workout.distance_meters != null ? String(workout.distance_meters) : '');
        setStrokeRate(workout.stroke_rate != null ? String(workout.stroke_rate) : '');
        setAvgHr(workout.avg_heart_rate != null ? String(workout.avg_heart_rate) : '');
        setWatts(workout.avg_watts != null ? String(workout.avg_watts) : '');
        setCalories(workout.calories != null ? String(workout.calories) : '');
        setNotes(workout.notes ?? '');
      } catch (err: any) {
        if (!active) return;
        setError(getErrorMessage(err, 'Failed to load workout'));
      } finally {
        if (active) setLoading(false);
      }
    }

    loadWorkout();

    return () => {
      active = false;
    };
  }, [workoutId]);

  const handleSubmit = async () => {
    setError('');

    const trimmedName = workoutName.trim();
    const trimmedDate = workoutDate.trim();

    if (!trimmedDate) {
      setError('Workout date is required (YYYY-MM-DD)');
      return;
    }
    if (!isValidDateInput(trimmedDate)) {
      setError('Workout date must be a valid YYYY-MM-DD date');
      return;
    }
    const workoutDateValue = buildLocalNoonWorkoutDate(trimmedDate);
    if (!workoutDateValue) {
      setError('Workout date must be a valid YYYY-MM-DD date');
      return;
    }

    if (!duration.trim()) {
      setError('Duration is required (MM:SS)');
      return;
    }
    const durationSeconds = parseDurationToSeconds(duration.trim());
    if (durationSeconds === null) {
      setError('Duration must be MM:SS format (e.g. 30:00)');
      return;
    }

    const distanceMeters = parsePositiveNumber(distance);
    if (distanceMeters == null) {
      setError('Distance must be a positive number (meters)');
      return;
    }

    const parsedStrokeRate = parsePositiveNumber(strokeRate);
    if (parsedStrokeRate === null) {
      setError('Stroke rate must be a positive number');
      return;
    }

    const parsedAvgHr = parsePositiveInteger(avgHr);
    if (parsedAvgHr === null) {
      setError('Average heart rate must be a positive whole number');
      return;
    }

    const parsedWatts = parsePositiveNumber(watts);
    if (parsedWatts === null) {
      setError('Average watts must be a positive number');
      return;
    }

    const parsedCalories = parsePositiveInteger(calories);
    if (parsedCalories === null) {
      setError('Calories must be a positive whole number');
      return;
    }

    setSaving(true);
    try {
      await updateWorkout(workoutId, {
        workout_name: trimmedName || null,
        workout_date: workoutDateValue,
        duration_seconds: durationSeconds,
        distance_meters: distanceMeters,
        stroke_rate: parsedStrokeRate ?? null,
        avg_heart_rate: parsedAvgHr ?? null,
        avg_watts: parsedWatts ?? null,
        calories: parsedCalories ?? null,
        notes: notes.trim() || null,
      });
      navigation.goBack();
    } catch (err: any) {
      setError(getErrorMessage(err, 'Failed to update workout'));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#0D2538" />
          <Text style={styles.stateText}>Loading workout...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.inner}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <TouchableOpacity onPress={() => navigation.goBack()} activeOpacity={0.8}>
            <Text style={styles.backText}>‹ Workout Detail</Text>
          </TouchableOpacity>

          <Text style={styles.title}>Edit Workout</Text>
          <Text style={styles.subtitle}>Update your erg session details</Text>

          <View style={styles.form}>
            <TextInput
              style={styles.input}
              placeholder="Workout Name (optional)"
              placeholderTextColor="#94A3B8"
              value={workoutName}
              onChangeText={(text) => { setWorkoutName(text); setError(''); }}
              maxLength={120}
            />
            <TextInput
              style={styles.input}
              placeholder="Workout Date (YYYY-MM-DD)"
              placeholderTextColor="#94A3B8"
              value={workoutDate}
              onChangeText={(text) => { setWorkoutDate(text); setError(''); }}
              autoCapitalize="none"
              autoCorrect={false}
            />
            <TextInput
              style={styles.input}
              placeholder="Duration (MM:SS)"
              placeholderTextColor="#94A3B8"
              value={duration}
              onChangeText={(text) => { setDuration(text); setError(''); }}
              keyboardType="numbers-and-punctuation"
            />
            <TextInput
              style={styles.input}
              placeholder="Distance (meters)"
              placeholderTextColor="#94A3B8"
              value={distance}
              onChangeText={(text) => { setDistance(text); setError(''); }}
              keyboardType="numeric"
            />
            <TextInput
              style={styles.input}
              placeholder="Stroke Rate (spm, optional)"
              placeholderTextColor="#94A3B8"
              value={strokeRate}
              onChangeText={(text) => { setStrokeRate(text); setError(''); }}
              keyboardType="numeric"
            />
            <TextInput
              style={styles.input}
              placeholder="Avg Heart Rate (bpm, optional)"
              placeholderTextColor="#94A3B8"
              value={avgHr}
              onChangeText={(text) => { setAvgHr(text); setError(''); }}
              keyboardType="numeric"
            />
            <TextInput
              style={styles.input}
              placeholder="Avg Watts (optional)"
              placeholderTextColor="#94A3B8"
              value={watts}
              onChangeText={(text) => { setWatts(text); setError(''); }}
              keyboardType="numeric"
            />
            <TextInput
              style={styles.input}
              placeholder="Calories (optional)"
              placeholderTextColor="#94A3B8"
              value={calories}
              onChangeText={(text) => { setCalories(text); setError(''); }}
              keyboardType="numeric"
            />
            <TextInput
              style={[styles.input, styles.textArea]}
              placeholder="Notes (optional)"
              placeholderTextColor="#94A3B8"
              value={notes}
              onChangeText={(text) => { setNotes(text); setError(''); }}
              multiline
              numberOfLines={3}
              textAlignVertical="top"
            />

            {error ? <Text style={styles.error}>{error}</Text> : null}

            <TouchableOpacity
              style={[styles.button, saving && styles.buttonDisabled]}
              onPress={handleSubmit}
              disabled={saving}
              activeOpacity={0.8}
            >
              {saving ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.buttonText}>Save Changes</Text>}
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  inner: {
    flex: 1,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    padding: 24,
    paddingBottom: 48,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  stateText: {
    marginTop: 12,
    color: '#64748B',
    fontSize: 15,
  },
  backText: {
    color: '#0D2538',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 18,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#0D2538',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#64748B',
    marginBottom: 24,
  },
  form: {
    gap: 14,
  },
  input: {
    backgroundColor: '#F1F5F9',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#1E293B',
  },
  textArea: {
    minHeight: 80,
  },
  error: {
    color: '#DC2626',
    fontSize: 14,
    textAlign: 'center',
  },
  button: {
    backgroundColor: '#0D2538',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
