import React from 'react';
import { View, TouchableOpacity, StyleSheet } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import TeamsScreen from '../screens/TeamsScreen';
import StatsScreen from '../screens/StatsScreen';
import ProfileScreen from '../screens/ProfileScreen';
import CustomTabBar from './CustomTabBar';
import type { TabParamList, AppStackParamList } from './types';

const Tab = createBottomTabNavigator<TabParamList>();

export default function MainTabs() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();

  return (
    <View style={styles.wrapper}>
      <Tab.Navigator
        tabBar={(props) => <CustomTabBar {...props} />}
        screenOptions={{
          headerShown: false,
          animation: 'shift',
        }}
      >
        <Tab.Screen name="Teams" component={TeamsScreen} />
        <Tab.Screen name="Stats" component={StatsScreen} />
        <Tab.Screen name="Profile" component={ProfileScreen} />
      </Tab.Navigator>

      <TouchableOpacity
        style={styles.settingsButton}
        onPress={() => navigation.navigate('Settings')}
        activeOpacity={0.7}
        accessibilityLabel="Settings"
        accessibilityRole="button"
      >
        <Ionicons name="settings-outline" size={24} color="#0D2538" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    flex: 1,
  },
  settingsButton: {
    position: 'absolute',
    top: 54, // below safe area, roughly aligned with status bar
    left: 16,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F1F5F9',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
});
