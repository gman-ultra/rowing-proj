import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native';
import type { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import { HermesIcon, AthenaIcon, ApolloIcon } from '../components/GreekIcons';
import type { TabParamList } from './types';
import type { RouteProp } from '@react-navigation/native';

const ICON_MAP: Record<keyof TabParamList, React.FC<{ size?: number; color?: string }>> = {
  Teams: HermesIcon,
  Stats: AthenaIcon,
  Profile: ApolloIcon,
};

export default function CustomTabBar({ state, descriptors, navigation, insets }: BottomTabBarProps) {
  return (
    <View style={[styles.container, { paddingBottom: insets.bottom }]}>
      {state.routes.map((route, index) => {
        const isFocused = state.index === index;
        const { options } = descriptors[route.key];
        const label = options.tabBarLabel !== undefined
          ? options.tabBarLabel
          : options.title !== undefined
            ? options.title
            : route.name;

        const displayLabel = typeof label === 'string' ? label : route.name;

        const routeName = route.name as keyof TabParamList;
        const IconComponent = ICON_MAP[routeName];

        const onPress = () => {
          const event = navigation.emit({
            type: 'tabPress',
            target: route.key,
            canPreventDefault: true,
          });

          if (!isFocused && !event.defaultPrevented) {
            navigation.navigate(route.name);
          }
        };

        const onLongPress = () => {
          navigation.emit({
            type: 'tabLongPress',
            target: route.key,
          });
        };

        const activeColor = '#0D2538';
        const inactiveColor = '#94A3B8';
        const color = isFocused ? activeColor : inactiveColor;

        return (
          <TouchableOpacity
            key={route.key}
            accessibilityRole="button"
            accessibilityState={isFocused ? { selected: true } : {}}
            accessibilityLabel={options.tabBarAccessibilityLabel}
            testID={options.tabBarButtonTestID}
            onPress={onPress}
            onLongPress={onLongPress}
            style={styles.tabItem}
          >
            {IconComponent && <IconComponent size={24} color={color} />}
            <Text style={[styles.label, { color }]}>{displayLabel}</Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
    height: 72,
  },
  tabItem: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 2,
  },
  label: {
    fontSize: 11,
    fontWeight: '600',
  },
});
