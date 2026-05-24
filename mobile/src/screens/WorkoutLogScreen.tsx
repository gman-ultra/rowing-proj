import React, { useCallback, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  SafeAreaView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../navigation/types';
import { listWorkouts, type Workout } from '../api/workouts';
import {
  formatDistance,
  formatDuration,
  formatSplit,
  formatWorkoutDate,
  getWorkoutDisplayName,
  getWorkoutTimeValue,
  isWorkoutInLastLocalDays,
} from '../utils/workoutFormat';

type Props = NativeStackScreenProps<AppStackParamList, 'WorkoutLog'>;
type SortOption = 'date_desc' | 'date_asc' | 'meters_desc' | 'meters_asc';
type FilterOption = 'all' | 'last_7_days' | 'last_30_days' | 'meters_2k_plus' | 'meters_5k_plus';

type SortChoice = {
  key: SortOption;
  label: string;
};

type FilterChoice = {
  key: FilterOption;
  label: string;
};

const SORT_OPTIONS: SortChoice[] = [
  { key: 'date_desc', label: 'Date newest' },
  { key: 'date_asc', label: 'Date oldest' },
  { key: 'meters_desc', label: 'Meters high-low' },
  { key: 'meters_asc', label: 'Meters low-high' },
];

const FILTER_OPTIONS: FilterChoice[] = [
  { key: 'all', label: 'All logs' },
  { key: 'last_7_days', label: 'Last 7 days' },
  { key: 'last_30_days', label: 'Last 30 days' },
  { key: 'meters_2k_plus', label: '2k+ meters' },
  { key: 'meters_5k_plus', label: '5k+ meters' },
];

function getErrorMessage(err: any, fallback: string): string {
  const data = err.response?.data;
  if (typeof data?.detail === 'string') return data.detail;
  if (Array.isArray(data?.detail)) return data.detail[0]?.msg || fallback;
  if (typeof data?.message === 'string') return data.message;
  return fallback;
}

function filterWorkouts(workouts: Workout[], filter: FilterOption): Workout[] {
  return workouts.filter((workout) => {
    if (filter === 'all') return true;
    if (filter === 'last_7_days') return isWorkoutInLastLocalDays(workout.workout_date, 7);
    if (filter === 'last_30_days') return isWorkoutInLastLocalDays(workout.workout_date, 30);

    const meters = workout.distance_meters ?? 0;
    return filter === 'meters_2k_plus' ? meters >= 2000 : meters >= 5000;
  });
}

function sortWorkouts(workouts: Workout[], sort: SortOption): Workout[] {
  const sorted = [...workouts];
  sorted.sort((a, b) => {
    if (sort === 'date_desc') {
      return getWorkoutTimeValue(b.workout_date) - getWorkoutTimeValue(a.workout_date);
    }
    if (sort === 'date_asc') {
      return getWorkoutTimeValue(a.workout_date) - getWorkoutTimeValue(b.workout_date);
    }
    const aMeters = a.distance_meters ?? 0;
    const bMeters = b.distance_meters ?? 0;
    return sort === 'meters_desc' ? bMeters - aMeters : aMeters - bMeters;
  });
  return sorted;
}

export default function WorkoutLogScreen({ navigation }: Props) {
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sort, setSort] = useState<SortOption>('date_desc');
  const [filter, setFilter] = useState<FilterOption>('all');

  const loadWorkouts = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await listWorkouts();
      setWorkouts(data.workouts);
    } catch (err: any) {
      setWorkouts([]);
      setError(getErrorMessage(err, 'Failed to load workouts'));
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadWorkouts();
    }, [loadWorkouts])
  );

  const visibleWorkouts = useMemo(
    () => sortWorkouts(filterWorkouts(workouts, filter), sort),
    [filter, sort, workouts]
  );
  const activeSortLabel = SORT_OPTIONS.find((option) => option.key === sort)?.label ?? 'Date newest';
  const activeFilterLabel = FILTER_OPTIONS.find((option) => option.key === filter)?.label ?? 'All logs';

  const renderWorkout = ({ item }: { item: Workout }) => (
    <TouchableOpacity
      style={styles.row}
      onPress={() => navigation.navigate('WorkoutDetail', { workoutId: item.id })}
      activeOpacity={0.8}
    >
      <View style={styles.rowTop}>
        <Text style={styles.rowDate}>{formatWorkoutDate(item.workout_date)}</Text>
        <Text style={styles.rowName} numberOfLines={1} ellipsizeMode="tail">
          {getWorkoutDisplayName(item.workout_name)}
        </Text>
      </View>
      <View style={styles.metricsRow}>
        <View style={styles.metricPill}>
          <Text style={styles.metricLabel}>Time</Text>
          <Text style={styles.metricValue}>{formatDuration(item.duration_seconds)}</Text>
        </View>
        <View style={styles.metricPill}>
          <Text style={styles.metricLabel}>Distance</Text>
          <Text style={styles.metricValue}>{formatDistance(item.distance_meters)}</Text>
        </View>
        <View style={styles.metricPill}>
          <Text style={styles.metricLabel}>Split</Text>
          <Text style={styles.metricValue}>{formatSplit(item.avg_split_500m)}</Text>
        </View>
        <View style={styles.metricPill}>
          <Text style={styles.metricLabel}>Rate</Text>
          <Text style={styles.metricValue}>{item.stroke_rate != null ? `${item.stroke_rate}` : '—'}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerTextWrap}>
          <Text style={styles.title}>Workout Log</Text>
          <Text style={styles.subtitle}>Tap any row to view, edit, or delete</Text>
        </View>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => navigation.navigate('LogWorkout')}
          activeOpacity={0.8}
        >
          <Text style={styles.addButtonText}>Log Workout</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.sortSection}>
        <Text style={styles.sortLabel}>Filter: {activeFilterLabel}</Text>
        <View style={styles.sortOptionsWrap}>
          {FILTER_OPTIONS.map((option) => {
            const selected = option.key === filter;
            return (
              <TouchableOpacity
                key={option.key}
                style={[styles.sortChip, selected && styles.sortChipSelected]}
                onPress={() => setFilter(option.key)}
                activeOpacity={0.8}
              >
                <Text style={[styles.sortChipText, selected && styles.sortChipTextSelected]}>{option.label}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      <View style={styles.sortSection}>
        <Text style={styles.sortLabel}>Sort: {activeSortLabel}</Text>
        <View style={styles.sortOptionsWrap}>
          {SORT_OPTIONS.map((option) => {
            const selected = option.key === sort;
            return (
              <TouchableOpacity
                key={option.key}
                style={[styles.sortChip, selected && styles.sortChipSelected]}
                onPress={() => setSort(option.key)}
                activeOpacity={0.8}
              >
                <Text style={[styles.sortChipText, selected && styles.sortChipTextSelected]}>{option.label}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#0D2538" />
          <Text style={styles.stateText}>Loading workouts...</Text>
        </View>
      ) : error ? (
        <View style={styles.centered}>
          <Text style={styles.errorTitle}>Could not load workouts</Text>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadWorkouts} activeOpacity={0.8}>
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      ) : workouts.length > 0 && visibleWorkouts.length === 0 ? (
        <View style={styles.centered}>
          <Text style={styles.emptyTitle}>No workouts match this filter</Text>
          <Text style={styles.emptyText}>Try another date or meters filter.</Text>
        </View>
      ) : visibleWorkouts.length === 0 ? (
        <View style={styles.centered}>
          <Text style={styles.emptyTitle}>No workouts logged yet</Text>
          <Text style={styles.emptyText}>Start with your first manual erg workout.</Text>
        </View>
      ) : (
        <FlatList
          data={visibleWorkouts}
          keyExtractor={(item) => item.id}
          renderItem={renderWorkout}
          contentContainerStyle={styles.list}
          ItemSeparatorComponent={() => <View style={styles.separator} />}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 14,
    gap: 14,
  },
  headerTextWrap: {
    gap: 4,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#0D2538',
  },
  subtitle: {
    fontSize: 14,
    color: '#64748B',
  },
  addButton: {
    alignSelf: 'flex-start',
    backgroundColor: '#0D2538',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  sortSection: {
    paddingHorizontal: 20,
    paddingBottom: 12,
    gap: 10,
  },
  sortLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#334155',
  },
  sortOptionsWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  sortChip: {
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#E2E8F0',
  },
  sortChipSelected: {
    backgroundColor: '#0D2538',
  },
  sortChipText: {
    fontSize: 13,
    color: '#334155',
    fontWeight: '600',
  },
  sortChipTextSelected: {
    color: '#FFFFFF',
  },
  list: {
    paddingHorizontal: 20,
    paddingBottom: 28,
  },
  row: {
    borderRadius: 14,
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 14,
    gap: 10,
  },
  rowTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  rowDate: {
    fontSize: 14,
    color: '#475569',
    fontWeight: '600',
    flexShrink: 0,
  },
  rowName: {
    flex: 1,
    textAlign: 'right',
    fontSize: 16,
    color: '#0F172A',
    fontWeight: '700',
  },
  metricsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  metricPill: {
    minWidth: '48%',
    flexGrow: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  metricLabel: {
    fontSize: 11,
    color: '#64748B',
    textTransform: 'uppercase',
    fontWeight: '700',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 14,
    color: '#0F172A',
    fontWeight: '600',
  },
  separator: {
    height: 10,
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
  errorTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 8,
  },
  errorText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#B91C1C',
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
    backgroundColor: '#0D2538',
    borderRadius: 12,
    paddingHorizontal: 18,
    paddingVertical: 12,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 15,
    color: '#64748B',
    textAlign: 'center',
  },
});
