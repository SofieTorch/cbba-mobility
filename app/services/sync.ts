/**
 * Sync pending recordings to the server when online.
 */
import NetInfo from '@react-native-community/netinfo';
import api from '@/services/api';
import {
  getPendingSyncRecordings,
  getLocationPoints,
  getSensorReadings,
  getRecording,
  deleteRecording,
} from '@/services/recording-store';

const BATCH_SIZE = 100;

/** Upload one pending recording to the server. Returns true if synced. */
async function syncOneRecording(recordingId: number): Promise<boolean> {
  const rec = getRecording(recordingId);
  if (!rec || rec.status !== 'pending_sync') return false;

  try {
    // 1. Start session on server
    const session = await api.startRecording(
      rec.deviceModel ?? undefined,
      rec.osVersion ?? undefined
    );

    const serverId = session.id;

    // 2. Upload location points in batches
    const points = getLocationPoints(recordingId);
    for (let i = 0; i < points.length; i += BATCH_SIZE) {
      const batch = points.slice(i, i + BATCH_SIZE);
      await api.uploadLocationBatch(serverId, batch);
    }

    // 3. Upload sensor readings in batches
    const readings = getSensorReadings(recordingId);
    for (let i = 0; i < readings.length; i += BATCH_SIZE) {
      const batch = readings.slice(i, i + BATCH_SIZE);
      await api.uploadSensorBatch(serverId, batch);
    }

    // 4. End recording with line
    await api.endRecording(serverId, rec.lineId, rec.lineName);

    // 5. Remove from local DB (data now on server)
    deleteRecording(recordingId);
    return true;
  } catch (err) {
    console.error('Sync failed for recording', recordingId, err);
    return false;
  }
}

/** Sync all pending recordings. Call when network is back. */
export async function syncPendingRecordings(): Promise<number> {
  const netInfo = await NetInfo.fetch();
  if (!netInfo.isConnected) return 0;

  const pending = getPendingSyncRecordings();
  let synced = 0;

  for (const rec of pending) {
    const ok = await syncOneRecording(rec.id);
    if (ok) synced++;
  }

  return synced;
}
