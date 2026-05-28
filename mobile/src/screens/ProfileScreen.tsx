import React, { useState, useCallback } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, SafeAreaView, ScrollView, Linking, ActivityIndicator } from 'react-native';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../navigation/types';
import { useAuth } from '../contexts/AuthContext';
import { getConcept2Status, startConcept2Connect, syncConcept2Workouts, disconnectConcept2, type Concept2Status } from '../api/concept2';
import { getStravaStatus, startStravaConnect, syncStravaWorkouts, disconnectStrava, type StravaStatus } from '../api/strava';

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();

  const [concept2Status, setConcept2Status] = useState<Concept2Status | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [concept2SyncLoading, setConcept2SyncLoading] = useState(false);
  const [concept2ConnectLoading, setConcept2ConnectLoading] = useState(false);
  const [concept2DisconnectLoading, setConcept2DisconnectLoading] = useState(false);
  const [concept2SyncResult, setConcept2SyncResult] = useState<string | null>(null);
  const [concept2Error, setConcept2Error] = useState<string | null>(null);

  const [stravaStatus, setStravaStatus] = useState<StravaStatus | null>(null);
  const [stravaSyncLoading, setStravaSyncLoading] = useState(false);
  const [stravaConnectLoading, setStravaConnectLoading] = useState(false);
  const [stravaDisconnectLoading, setStravaDisconnectLoading] = useState(false);
  const [stravaSyncResult, setStravaSyncResult] = useState<string | null>(null);
  const [stravaError, setStravaError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    setStatusLoading(true);
    setConcept2Error(null);
    setStravaError(null);

    const [c2Result, svResult] = await Promise.allSettled([
      getConcept2Status(),
      getStravaStatus(),
    ]);

    if (c2Result.status === 'fulfilled') {
      setConcept2Status(c2Result.value);
    } else {
      setConcept2Status(null);
      setConcept2Error('Failed to load Concept2 status');
    }

    if (svResult.status === 'fulfilled') {
      setStravaStatus(svResult.value);
    } else {
      setStravaStatus(null);
      setStravaError('Failed to load Strava status');
    }

    setStatusLoading(false);
  }, []);

  useFocusEffect(
    useCallback(() => {
      fetchStatus();
    }, [fetchStatus])
  );

  const handleConcept2Connect = async () => {
    setConcept2ConnectLoading(true);
    setConcept2Error(null);
    try {
      const { authorization_url } = await startConcept2Connect();
      await Linking.openURL(authorization_url);
    } catch {
      setConcept2Error('Failed to start Concept2 connection');
    } finally {
      setConcept2ConnectLoading(false);
    }
  };

  const handleConcept2Sync = async () => {
    setConcept2SyncLoading(true);
    setConcept2Error(null);
    setConcept2SyncResult(null);
    try {
      const result = await syncConcept2Workouts();
      setConcept2SyncResult(`Imported ${result.imported}, updated ${result.updated}, skipped ${result.skipped}`);
      await fetchStatus();
    } catch {
      setConcept2Error('Failed to sync Concept2 workouts');
    } finally {
      setConcept2SyncLoading(false);
    }
  };

  const handleConcept2Disconnect = async () => {
    setConcept2DisconnectLoading(true);
    setConcept2Error(null);
    try {
      await disconnectConcept2();
      await fetchStatus();
    } catch {
      setConcept2Error('Failed to disconnect Concept2');
    } finally {
      setConcept2DisconnectLoading(false);
    }
  };

  const handleStravaConnect = async () => {
    setStravaConnectLoading(true);
    setStravaError(null);
    try {
      const { authorization_url } = await startStravaConnect();
      await Linking.openURL(authorization_url);
    } catch {
      setStravaError('Failed to start Strava connection');
    } finally {
      setStravaConnectLoading(false);
    }
  };

  const handleStravaSync = async () => {
    setStravaSyncLoading(true);
    setStravaError(null);
    setStravaSyncResult(null);
    try {
      const result = await syncStravaWorkouts();
      setStravaSyncResult(`Imported ${result.imported}, updated ${result.updated}, skipped ${result.skipped}`);
      await fetchStatus();
    } catch {
      setStravaError('Failed to sync Strava workouts');
    } finally {
      setStravaSyncLoading(false);
    }
  };

  const handleStravaDisconnect = async () => {
    setStravaDisconnectLoading(true);
    setStravaError(null);
    try {
      await disconnectStrava();
      await fetchStatus();
    } catch {
      setStravaError('Failed to disconnect Strava');
    } finally {
      setStravaDisconnectLoading(false);
    }
  };

  const formatDateTime = (isoString: string | null) => {
    if (!isoString) return '';
    const d = new Date(isoString);
    return d.toLocaleString();
  };

  const renderConcept2Content = () => {
    if (!concept2Status) {
      return (
        <View>
          <Text style={styles.errorText}>Could not load connection status.</Text>
          <TouchableOpacity onPress={fetchStatus} style={styles.retryButton}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      );
    }

    if (concept2Status.connected) {
      return (
        <View>
          <View style={styles.statusRow}>
            <Text style={styles.statusLabel}>Status:</Text>
            <Text style={styles.statusValueConnected}>Connected</Text>
          </View>
          {concept2Status.concept2_user_id && (
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>User ID:</Text>
              <Text style={styles.statusValue}>{concept2Status.concept2_user_id}</Text>
            </View>
          )}
          {concept2Status.last_sync_at && (
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Last sync:</Text>
              <Text style={styles.statusValue}>{formatDateTime(concept2Status.last_sync_at)}</Text>
            </View>
          )}
          {concept2SyncResult && (
            <View style={styles.syncResultBadge}>
              <Text style={styles.syncResultText}>{concept2SyncResult}</Text>
            </View>
          )}
          <TouchableOpacity
            style={[styles.syncButton, concept2SyncLoading && styles.buttonDisabled]}
            onPress={handleConcept2Sync}
            disabled={concept2SyncLoading}
            activeOpacity={0.8}
          >
            {concept2SyncLoading ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.syncButtonText}>Sync Workouts</Text>
            )}
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.secondaryButton, concept2DisconnectLoading && styles.buttonDisabled]}
            onPress={handleConcept2Disconnect}
            disabled={concept2DisconnectLoading}
            activeOpacity={0.8}
          >
            {concept2DisconnectLoading ? (
              <ActivityIndicator size="small" color="#EF4444" />
            ) : (
              <Text style={styles.secondaryButtonText}>Disconnect</Text>
            )}
          </TouchableOpacity>
          {concept2Error && <Text style={styles.errorText}>{concept2Error}</Text>}
        </View>
      );
    }

    return (
      <View>
        <Text style={styles.cardBodyText}>
          Connect your Concept2 Logbook to import your workouts automatically.
        </Text>
        <TouchableOpacity
          style={[styles.connectButton, concept2ConnectLoading && styles.buttonDisabled]}
          onPress={handleConcept2Connect}
          disabled={concept2ConnectLoading}
          activeOpacity={0.8}
        >
          {concept2ConnectLoading ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={styles.connectButtonText}>Connect Concept2</Text>
          )}
        </TouchableOpacity>
        {concept2Error && <Text style={styles.errorText}>{concept2Error}</Text>}
      </View>
    );
  };

  const renderStravaContent = () => {
    if (!stravaStatus) {
      return (
        <View>
          <Text style={styles.errorText}>Could not load connection status.</Text>
          <TouchableOpacity onPress={fetchStatus} style={styles.retryButton}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      );
    }

    if (stravaStatus.connected) {
      return (
        <View>
          <View style={styles.statusRow}>
            <Text style={styles.statusLabel}>Status:</Text>
            <Text style={styles.statusValueConnected}>Connected</Text>
          </View>
          {stravaStatus.strava_athlete_id && (
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Athlete ID:</Text>
              <Text style={styles.statusValue}>{stravaStatus.strava_athlete_id}</Text>
            </View>
          )}
          {stravaStatus.last_sync_at && (
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Last sync:</Text>
              <Text style={styles.statusValue}>{formatDateTime(stravaStatus.last_sync_at)}</Text>
            </View>
          )}
          {stravaSyncResult && (
            <View style={styles.syncResultBadge}>
              <Text style={styles.syncResultText}>{stravaSyncResult}</Text>
            </View>
          )}
          <TouchableOpacity
            style={[styles.syncButton, stravaSyncLoading && styles.buttonDisabled]}
            onPress={handleStravaSync}
            disabled={stravaSyncLoading}
            activeOpacity={0.8}
          >
            {stravaSyncLoading ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.syncButtonText}>Sync Rowing Workouts</Text>
            )}
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.secondaryButton, stravaDisconnectLoading && styles.buttonDisabled]}
            onPress={handleStravaDisconnect}
            disabled={stravaDisconnectLoading}
            activeOpacity={0.8}
          >
            {stravaDisconnectLoading ? (
              <ActivityIndicator size="small" color="#EF4444" />
            ) : (
              <Text style={styles.secondaryButtonText}>Disconnect</Text>
            )}
          </TouchableOpacity>
          {stravaError && <Text style={styles.errorText}>{stravaError}</Text>}
        </View>
      );
    }

    return (
      <View>
        <Text style={styles.cardBodyText}>
          Connect your Strava account to import your rowing activities automatically.
        </Text>
        <TouchableOpacity
          style={[styles.connectButton, stravaConnectLoading && styles.buttonDisabled]}
          onPress={handleStravaConnect}
          disabled={stravaConnectLoading}
          activeOpacity={0.8}
        >
          {stravaConnectLoading ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={styles.connectButtonText}>Connect Strava</Text>
          )}
        </TouchableOpacity>
        {stravaError && <Text style={styles.errorText}>{stravaError}</Text>}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.title}>Profile</Text>
        {user?.displayName && (
          <Text style={styles.name}>{user.displayName}</Text>
        )}

        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Concept2 Logbook</Text>
            {!statusLoading && concept2Status && (
              <TouchableOpacity onPress={fetchStatus}>
                <Text style={styles.refreshText}>Refresh</Text>
              </TouchableOpacity>
            )}
          </View>
          {renderConcept2Content()}
        </View>

        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Strava</Text>
            {!statusLoading && stravaStatus && (
              <TouchableOpacity onPress={fetchStatus}>
                <Text style={styles.refreshText}>Refresh</Text>
              </TouchableOpacity>
            )}
          </View>
          {renderStravaContent()}
        </View>

        <TouchableOpacity
          style={styles.workoutLogButton}
          onPress={() => navigation.navigate('WorkoutLog')}
          activeOpacity={0.8}
        >
          <Text style={styles.workoutLogText}>Workout Log</Text>
        </TouchableOpacity>
      </ScrollView>
      <TouchableOpacity onPress={logout} style={styles.logoutButton}>
        <Text style={styles.logoutText}>Log Out</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  scrollContent: {
    paddingTop: 80,
    paddingHorizontal: 24,
    paddingBottom: 100,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#0D2538',
    marginBottom: 8,
  },
  name: {
    fontSize: 18,
    color: '#64748B',
    marginBottom: 32,
  },
  card: {
    backgroundColor: '#F8FAFC',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 20,
    width: '100%',
    marginBottom: 24,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#0D2538',
  },
  refreshText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#3B82F6',
  },
  cardBodyText: {
    fontSize: 14,
    color: '#64748B',
    lineHeight: 20,
    marginBottom: 16,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  statusLabel: {
    fontSize: 14,
    color: '#64748B',
  },
  statusValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#0D2538',
  },
  statusValueConnected: {
    fontSize: 14,
    fontWeight: '600',
    color: '#059669',
  },
  syncResultBadge: {
    backgroundColor: '#ECFDF5',
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginTop: 12,
    marginBottom: 4,
  },
  syncResultText: {
    fontSize: 13,
    color: '#059669',
    fontWeight: '500',
    textAlign: 'center',
  },
  connectButton: {
    backgroundColor: '#0D2538',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  connectButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  syncButton: {
    backgroundColor: '#0D2538',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 16,
  },
  syncButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  secondaryButtonText: {
    color: '#EF4444',
    fontSize: 14,
    fontWeight: '500',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  errorText: {
    fontSize: 13,
    color: '#EF4444',
    marginTop: 12,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 12,
    alignItems: 'center',
  },
  retryButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#3B82F6',
  },
  workoutLogButton: {
    backgroundColor: '#0D2538',
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 32,
  },
  workoutLogText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  logoutButton: {
    marginHorizontal: 24,
    marginBottom: 32,
    paddingVertical: 14,
    alignItems: 'center',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  logoutText: {
    color: '#0D2538',
    fontSize: 16,
    fontWeight: '600',
  },
});
