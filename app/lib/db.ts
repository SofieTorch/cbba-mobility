/**
 * Database exports. The db instance is set by DatabaseProvider (SQLiteProvider pattern).
 * Use getDb() in services - do not import db directly at module load.
 */
import { drizzle } from 'drizzle-orm/expo-sqlite';
import * as schema from '@/db/schema';
import migrations from '@/drizzle/migrations';
import { getDb, setDb } from '@/lib/db-ref';
import type { SQLiteDatabase } from 'expo-sqlite';

/** Create drizzle db from expo SQLiteDatabase. Call once when provider mounts. */
export function createDb(expoDb: SQLiteDatabase): ReturnType<typeof drizzle> {
  const db = drizzle(expoDb, { schema });
  setDb(db);
  return db;
}

export { getDb, migrations, schema };
