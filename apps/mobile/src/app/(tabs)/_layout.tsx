/**
 * MSGI One — Authenticated Main Tab Navigator
 * 5 Core Navigation Hubs: Dashboard, Network, Career, AI Command, Profile.
 */

import React from 'react';
import { Tabs } from 'expo-router';
import { Text, Platform, StyleSheet } from 'react-native';
import { Colors, Typography } from '../../constants/theme';

function TabIcon({ name, color }: { name: string; color: string }) {
  // Unicode symbols for clean, zero-dependency icon rendering across Android & iOS
  const icons: Record<string, string> = {
    dashboard: '🏛️',
    network: '🌐',
    opportunities: '💼',
    ai: '🤖',
    profile: '👤',
  };

  return <Text style={styles.tabIcon}>{icons[name] || '•'}</Text>;
}

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerStyle: {
          backgroundColor: Colors.primary,
        },
        headerTintColor: '#FFFFFF',
        headerTitleStyle: {
          fontWeight: 'bold',
          fontSize: Typography.fontSize.lg,
        },
        tabBarActiveTintColor: Colors.primary,
        tabBarInactiveTintColor: Colors.textMuted,
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopColor: Colors.border,
          height: Platform.OS === 'ios' ? 88 : 64,
          paddingBottom: Platform.OS === 'ios' ? 24 : 8,
          paddingTop: 8,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Dashboard',
          tabBarLabel: 'Home',
          tabBarIcon: ({ color }) => <TabIcon name="dashboard" color={color} />,
        }}
      />
      <Tabs.Screen
        name="network"
        options={{
          title: 'Alumni Network',
          tabBarLabel: 'Network',
          tabBarIcon: ({ color }) => <TabIcon name="network" color={color} />,
        }}
      />
      <Tabs.Screen
        name="opportunities"
        options={{
          title: 'CareerBridge',
          tabBarLabel: 'Career',
          tabBarIcon: ({ color }) => <TabIcon name="opportunities" color={color} />,
        }}
      />
      <Tabs.Screen
        name="ai"
        options={{
          title: 'AI Command Centre',
          tabBarLabel: 'AI Assistant',
          tabBarIcon: ({ color }) => <TabIcon name="ai" color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Institutional Profile',
          tabBarLabel: 'Profile',
          tabBarIcon: ({ color }) => <TabIcon name="profile" color={color} />,
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabIcon: {
    fontSize: 20,
    marginBottom: 2,
  },
});
