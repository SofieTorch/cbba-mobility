import { Tabs } from 'expo-router';
import React from 'react';

import { HapticTab } from '@/components/haptic-tab';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '@react-navigation/native';

export default function TabLayout() {
  const { colors } = useTheme();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        headerShown: false,
        tabBarButton: HapticTab,
      }}>
      <Tabs.Screen
        name="index"
        options={{
          tabBarIcon: ({ color }: { color: string }) => <Ionicons size={24} name="map-outline" color={color} />,
          tabBarLabel: 'Rutas',
        }}
      />
      <Tabs.Screen
        name="record"
        options={{
          tabBarLabel: 'Recorrido',
          tabBarIcon: ({ color }: { color: string }) => <Ionicons size={24} name="locate" color={color} />,
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          tabBarLabel: 'Favoritos',
          tabBarIcon: ({ color }: { color: string }) => <Ionicons size={24} name="star-outline" color={color} />,
        }}
      />
    </Tabs>
  );
}
