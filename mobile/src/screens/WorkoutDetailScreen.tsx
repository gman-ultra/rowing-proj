import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { deleteWorkout, getWorkout, type Workout } from '../api/workouts';
import type { AppStackParamList } from '../navigation/types';
import {
  formatDistance,
  formatDuration,
  formatSplit,
  formatWorkoutDate,
  formatWorkoutDateTime,
  getWorkoutDisplayName,
} from '../utils/workoutFormat';

type Props = NativeStackScreenProps<AppStackParamList, 'WorkoutDetail'>;

function getErrorMessage(err: any, fallback: string): string {
  const data = err.response?.data;
  if (typeof data?.detail === 'string') return data.detail;
  if (Array.isArray(data?.detail)) return data.detail[0]?.msg || fallback;
  if (typeof data?.message === 'string') return data.message;
  return fallback;
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.detailRow}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={styles.detailValue}>{value}</Text>
    </View>
  );
}

export default function WorkoutDetailScreen({ navigation, route }: Props) {
  const { workoutId } = route.params;
  const [workout, setWorkout] = useState<Workout | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);

  const loadWorkout = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getWorkout(workoutId);
      setWorkout(data);
    } catch (err: any) {
      setWorkout(null);
      setError(getErrorMessage(err, 'Failed to load workout'));
    } finally {
      setLoading(false);
    }
  }, [workoutId]);

  useFocusEffect(
    useCallback(() => {
      loadWorkout();
    }, [loadWorkout])
  );

  const confirmDelete = () => {
    Alert.alert('Delete workout?', 'This will permanently remove this workout log.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          setDeleting(true);
          setError('');
          try {
            await deleteWorkout(workoutId);
            navigation.goBack();
          } catch (err: any) {
            setError(getErrorMessage(err, 'Failed to delete workout'));
            setDeleting(false);
          }
        },
      },
    ]);
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

  if (!workout) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centered}>
          <Text style={styles.errorTitle}>Workout unavailable</Text>
          <Text style={styles.errorText}>{error || 'This workout could not be found.'}</Text>
          <TouchableOpacity style={styles.secondaryButton} onPress={loadWorkout} activeOpacity={0.8}>
            <Text style={styles.secondaryButtonText}>Try Again</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.linkButton} onPress={() => navigation.goBack()} activeOpacity={0.8}>
            <Text style={styles.linkButtonText}>Back to log</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.headerRow}>
          <TouchableOpacity onPress={() => navigation.goBack()} activeOpacity={0.8}>
            <Text style={styles.backText}>‹ Workout Log</Text>
          </TouchableOpacity>
          <Text style={styles.dateText}>{formatWorkoutDateTime(workout.workout_date)}</Text>
        </View>

        <Text style={styles.title}>{getWorkoutDisplayName(workout.workout_name)}</Text>
        <Text style={styles.subtitle}>{formatWorkoutDate(workout.workout_date)}</Text>

        <View style={styles.section}>
          <DetailRow label="Workout name" value={getWorkoutDisplayName(workout.workout_name)} />
          <DetailRow label="Workout date" value={formatWorkoutDate(workout.workout_date)} />
          <DetailRow label="Duration" value={formatDuration(workout.duration_seconds)} />
          <DetailRow label="Distance" value={formatDistance(workout.distance_meters)} />
          <DetailRow label="Avg split /500m" value={formatSplit(workout.avg_split_500m)} />
          <DetailRow label="Stroke rate" value={workout.stroke_rate != null ? `${workout.stroke_rate} spm` : '—'} />
          <DetailRow label="Average heart rate" value={workout.avg_heart_rate != null ? `${workout.avg_heart_rate} bpm` : '—'} />
          <DetailRow label="Average watts" value={workout.avg_watts != null ? `${workout.avg_watts}` : '—'} />
          <DetailRow label="Calories" value={workout.calories != null ? `${workout.calories}` : '—'} />
          <DetailRow label="Visibility" value={workout.visibility === 'team' ? 'Team' : 'Private'} />
          <DetailRow label="Source" value={workout.source} />
          <DetailRow label="Notes" value={workout.notes?.trim() ? workout.notes : '—'} />
        </View>

        {error ? <Text style={styles.errorText}>{error}</Text> : null}

        <TouchableOpacity
          style={styles.primaryButton}
          onPress={() => navigation.navigate('EditWorkout', { workoutId })}
          activeOpacity={0.8}
        >
          <Text style={styles.primaryButtonText}>Edit Workout</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.deleteButton, deleting && styles.buttonDisabled]}
          onPress={confirmDelete}
          disabled={deleting}
          activeOpacity={0.8}
        >
          <Text style={styles.deleteButtonText}>{deleting ? 'Deleting...' : 'Delete Workout'}</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  content: {
    padding: 24,
    paddingBottom: 48,
    gap: 16,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  stateText: {
    marginTop: 12,
    fontSize: 15,
    color: '#64748B',
  },
  headerRow: {
    gap: 8,
  },
  backText: {
    color: '#0D2538',
    fontSize: 16,
    fontWeight: '600',
  },
  dateText: {
    color: '#64748B',
    fontSize: 14,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#0D2538',
  },
  subtitle: {
    fontSize: 16,
    color: '#64748B',
    marginTop: -10,
  },
  section: {
    backgroundColor: '#F8FAFC',
    borderRadius: 16,
    padding: 16,
    gap: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  detailRow: {
    gap: 4,
  },
  detailLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  detailValue: {
    fontSize: 16,
    color: '#0F172A',
    lineHeight: 22,
  },
  primaryButton: {
    backgroundColor: '#0D2538',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  deleteButton: {
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
  },
  deleteButtonText: {
    color: '#B91C1C',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    marginTop: 16,
    backgroundColor: '#0D2538',
    borderRadius: 12,
    paddingHorizontal: 18,
    paddingVertical: 12,
  },
  secondaryButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  linkButton: {
    marginTop: 12,
  },
  linkButtonText: {
    color: '#0D2538',
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  errorTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 8,
  },
  errorText: {
    color: '#B91C1C',
    fontSize: 14,
    lineHeight: 20,
  },
});
