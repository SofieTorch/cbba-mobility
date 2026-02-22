'use client';

import { useMigrations } from 'drizzle-orm/expo-sqlite/migrator';
import { SQLiteProvider, useSQLiteContext } from 'expo-sqlite';
import React, { useMemo } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';

import { createDb } from '@/lib/db';
import migrations from '@/drizzle/migrations';

function MigrationsGate({ children }: { children: React.ReactNode }) {
  const expoDb = useSQLiteContext();
  const db = useMemo(() => createDb(expoDb), [expoDb]);
  const { success, error } = useMigrations(db, migrations);

  if (error) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 }}>
        <Text style={{ color: 'red', marginBottom: 10 }}>Migration error</Text>
        <Text style={{ color: '#666' }}>{error.message}</Text>
      </View>
    );
  }

  if (!success) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" />
        <Text style={{ marginTop: 12, color: '#666' }}>Initializing database...</Text>
      </View>
    );
  }

  return <>{children}</>;
}

export function DatabaseProvider({ children }: { children: React.ReactNode }) {
  return (
    <SQLiteProvider databaseName="cbba-mobility.db">
      <MigrationsGate>{children}</MigrationsGate>
    </SQLiteProvider>
  );
}
