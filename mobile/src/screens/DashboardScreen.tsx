import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';

export default function DashboardScreen() {
  const { user } = useAuth();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.greeting}>
          Welcome{user?.displayName ? `, ${user.displayName}` : ''}
        </Text>
        <Text style={styles.stats}>0 workouts logged</Text>

        <TouchableOpacity style={styles.button} disabled activeOpacity={1}>
          <Text style={styles.buttonText}>Log Workout</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 32,
    alignItems: 'center',
  },
  greeting: {
    fontSize: 28,
    fontWeight: '700',
    color: '#0D2538',
    marginBottom: 8,
  },
  stats: {
    fontSize: 16,
    color: '#64748B',
    marginBottom: 32,
  },
  button: {
    backgroundColor: '#E2E8F0',
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 48,
    alignItems: 'center',
    opacity: 0.5,
  },
  buttonText: {
    color: '#94A3B8',
    fontSize: 16,
    fontWeight: '600',
  },
});
