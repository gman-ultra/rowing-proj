import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../navigation/types';
import { createWorkout } from '../api/workouts';
import {
  buildLocalNoonWorkoutDate,
  getTodayLocalDateInput,
  isValidDateInput,
  parseDurationToSeconds,
  parsePositiveInteger,
  parsePositiveNumber,
} from '../utils/workoutFormat';

type Props = NativeStackScreenProps<AppStackParamList, 'LogWorkout'>;

export default function LogWorkoutScreen({ navigation }: Props) {
  const [workoutName, setWorkoutName] = useState('');
  const [workoutDate, setWorkoutDate] = useState(getTodayLocalDateInput());
  const [duration, setDuration] = useState('');
  const [distance, setDistance] = useState('');
  const [strokeRate, setStrokeRate] = useState('');
  const [avgHr, setAvgHr] = useState('');
  const [watts, setWatts] = useState('');
  const [calories, setCalories] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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

    setLoading(true);
    try {
      await createWorkout({
        workout_name: trimmedName || undefined,
        workout_date: workoutDateValue,
        duration_seconds: durationSeconds,
        distance_meters: distanceMeters,
        stroke_rate: parsedStrokeRate,
        avg_heart_rate: parsedAvgHr,
        avg_watts: parsedWatts,
        calories: parsedCalories,
        notes: notes.trim() || undefined,
      });
      navigation.goBack();
    } catch (err: any) {
      const data = err.response?.data;
      let message = 'Failed to log workout';
      if (typeof data?.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data?.detail)) {
        message = data.detail[0]?.msg || message;
      } else if (data?.message) {
        message = data.message;
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  };

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
          <Text style={styles.title}>Log Erg Workout</Text>
          <Text style={styles.subtitle}>Enter your erg session details</Text>

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
              style={[styles.button, loading && styles.buttonDisabled]}
              onPress={handleSubmit}
              disabled={loading}
              activeOpacity={0.8}
            >
              {loading ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.buttonText}>Log Workout</Text>
              )}
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
