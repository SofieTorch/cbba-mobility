/**
 * Database ref - set by SQLiteProvider/DatabaseProvider when ready.
 * Used by services (recording-store, line-cache) that run outside React.
 */
import type { ExpoSQLiteDatabase } from 'drizzle-orm/expo-sqlite';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let dbInstance: ExpoSQLiteDatabase<any> | null = null;

export function setDb(db: ExpoSQLiteDatabase<any>): void {
  dbInstance = db;
}

export function getDb(): ExpoSQLiteDatabase<any> {
  if (!dbInstance) {
    throw new Error('Database not initialized. Ensure SQLiteProvider has mounted.');
  }
  return dbInstance;
}
