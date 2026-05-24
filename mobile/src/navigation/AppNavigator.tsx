import React from 'react';
import {
  View,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuth } from '../contexts/AuthContext';
import LoginScreen from '../screens/LoginScreen';
import RegisterScreen from '../screens/RegisterScreen';
import LogWorkoutScreen from '../screens/LogWorkoutScreen';
import WorkoutLogScreen from '../screens/WorkoutLogScreen';
import WorkoutDetailScreen from '../screens/WorkoutDetailScreen';
import EditWorkoutScreen from '../screens/EditWorkoutScreen';
import MainTabs from './MainTabs';
import SettingsScreen from '../screens/SettingsScreen';
import type { AuthStackParamList, AppStackParamList } from './types';

const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const AppStack = createNativeStackNavigator<AppStackParamList>();

export default function AppNavigator() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0D2538" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      {isAuthenticated ? (
        <AppStack.Navigator>
          <AppStack.Screen
            name="MainTabs"
            component={MainTabs}
            options={{ headerShown: false }}
          />
          <AppStack.Screen
            name="Settings"
            component={SettingsScreen}
            options={{ presentation: 'modal', headerShown: false }}
          />
          <AppStack.Screen
            name="WorkoutLog"
            component={WorkoutLogScreen}
            options={{ headerShown: false }}
          />
          <AppStack.Screen
            name="LogWorkout"
            component={LogWorkoutScreen}
            options={{ headerShown: false }}
          />
          <AppStack.Screen
            name="WorkoutDetail"
            component={WorkoutDetailScreen}
            options={{ headerShown: false }}
          />
          <AppStack.Screen
            name="EditWorkout"
            component={EditWorkoutScreen}
            options={{ headerShown: false }}
          />
        </AppStack.Navigator>
      ) : (
        <AuthStack.Navigator screenOptions={{ headerShown: false }}>
          <AuthStack.Screen name="Login" component={LoginScreen} />
          <AuthStack.Screen name="Register" component={RegisterScreen} />
        </AuthStack.Navigator>
      )}
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
});
