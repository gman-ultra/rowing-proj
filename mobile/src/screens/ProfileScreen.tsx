import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, SafeAreaView } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { AppStackParamList } from '../navigation/types';
import { useAuth } from '../contexts/AuthContext';

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Profile</Text>
        {user?.displayName && (
          <Text style={styles.name}>{user.displayName}</Text>
        )}
        <TouchableOpacity
          style={styles.workoutLogButton}
          onPress={() => navigation.navigate('WorkoutLog')}
          activeOpacity={0.8}
        >
          <Text style={styles.workoutLogText}>Workout Log</Text>
        </TouchableOpacity>
      </View>
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
  content: {
    flex: 1,
    justifyContent: 'center',
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
