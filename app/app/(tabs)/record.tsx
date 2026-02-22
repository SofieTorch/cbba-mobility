/**
 * Record tab - Start/stop recording transit data.
 */
import * as Location from 'expo-location';
import { Accelerometer, Gyroscope } from 'expo-sensors';

import {
  startBackgroundLocation,
  stopBackgroundLocation,
  onLocationBatch,
  requestBackgroundPermission,
} from '@/services/background-location';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert,
  FlatList,
  Modal,
  Platform,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { SwipeSwitch } from '@/components/swipe-switch';
import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { useTheme } from '@react-navigation/native';
import type { Line, SensorReading } from '@/services/api';
import { getLines } from '@/services/line-cache';
import {
  createRecording,
  addLocationPoints,
  addSensorReadings,
  finalizeRecording,
  cancelRecording,
  touchRecording,
} from '@/services/recording-store';
import { syncPendingRecordings } from '@/services/sync';
import { styles } from '@/styles/record';
import Header from '@/components/header';

const SENSOR_INTERVAL = 100;

export default function RecordScreen() {
  const { colors } = useTheme();

  const [isRecording, setIsRecording] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [locationPermission, setLocationPermission] = useState<boolean>(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [pointsCollected, setPointsCollected] = useState(0);

  // Line selection modal (shown after stopping)
  const [showLineModal, setShowLineModal] = useState(false);
  const [lines, setLines] = useState<Line[]>([]);
  const [selectedLine, setSelectedLine] = useState<Line | null>(null);
  const [customLineName, setCustomLineName] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Snapshot of stats at the moment recording stopped (so the modal shows stable values)
  const finalDuration = useRef(0);
  const finalPoints = useRef(0);

  const sensorBuffer = useRef<SensorReading[]>([]);
  const accelSubscription = useRef<ReturnType<typeof Accelerometer.addListener> | null>(null);
  const gyroSubscription = useRef<ReturnType<typeof Gyroscope.addListener> | null>(null);
  const durationInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    requestLocationPermission();
    fetchLines();
  }, []);

  // Subscribe to background location updates for points count
  useEffect(() => {
    if (!isRecording) return;
    const unsub = onLocationBatch((count) => {
      setPointsCollected((prev) => prev + count);
    });
    return unsub;
  }, [isRecording]);

  const fetchLines = async () => {
    try {
      const data = await getLines();
      setLines(data);
    } catch (error) {
      console.error('Failed to fetch lines:', error);
    }
  };

  const requestLocationPermission = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    const granted = status === 'granted';
    setLocationPermission(granted);

    if (!granted) {
      Alert.alert(
        'Location Permission Required',
        'Please enable location services to record transit data.',
        [{ text: 'OK' }]
      );
      return;
    }
    // Request background permission so recording continues when app is minimized
    await requestBackgroundPermission();
  };

  const startDataCollection = useCallback(async (localRecordingId: number) => {
    // Background location works in both foreground and background
    await startBackgroundLocation();

    Accelerometer.setUpdateInterval(SENSOR_INTERVAL);
    accelSubscription.current = Accelerometer.addListener((data) => {
      const reading: SensorReading = {
        timestamp: new Date().toISOString(),
        accel_x: data.x,
        accel_y: data.y,
        accel_z: data.z,
        gyro_x: null,
        gyro_y: null,
        gyro_z: null,
        pressure: null,
        magnetic_heading: null,
      };
      sensorBuffer.current.push(reading);
      addSensorReadings(localRecordingId, [reading]);
    });

    Gyroscope.setUpdateInterval(SENSOR_INTERVAL);
    gyroSubscription.current = Gyroscope.addListener((data) => {
      const reading: SensorReading = {
        timestamp: new Date().toISOString(),
        accel_x: null,
        accel_y: null,
        accel_z: null,
        gyro_x: data.x,
        gyro_y: data.y,
        gyro_z: data.z,
        pressure: null,
        magnetic_heading: null,
      };
      sensorBuffer.current.push(reading);
      addSensorReadings(localRecordingId, [reading]);
    });

    durationInterval.current = setInterval(() => {
      setRecordingDuration((prev) => prev + 1);
      touchRecording(localRecordingId);
    }, 1000);
  }, []);

  const stopDataCollection = useCallback(() => {
    stopBackgroundLocation();
    if (accelSubscription.current) {
      accelSubscription.current.remove();
      accelSubscription.current = null;
    }
    if (gyroSubscription.current) {
      gyroSubscription.current.remove();
      gyroSubscription.current = null;
    }
    if (durationInterval.current) {
      clearInterval(durationInterval.current);
      durationInterval.current = null;
    }
  }, []);

  const handleRecordingToggle = async (shouldRecord: boolean) => {
    if (shouldRecord) {
      if (!locationPermission) {
        Alert.alert('Permission Required', 'Location permission is required to record.');
        return;
      }

      const recording = createRecording({
        deviceModel: Platform.OS,
        osVersion: Platform.Version?.toString(),
      });

      setCurrentSessionId(recording.id);
      setIsRecording(true);
      setRecordingDuration(0);
      setPointsCollected(0);
      sensorBuffer.current = [];

      await startDataCollection(recording.id);
    } else {
      if (!currentSessionId) return;

      stopDataCollection();

      finalDuration.current = recordingDuration;
      finalPoints.current = pointsCollected;

      setIsRecording(false);
      setSelectedLine(null);
      setCustomLineName('');
      setShowLineModal(true);
    }
  };

  const canSave = !!selectedLine || !!customLineName.trim();

  const handleConfirmLine = async () => {
    if (!currentSessionId) return;
    if (!canSave) return;

    setIsSaving(true);
    try {
      finalizeRecording(
        currentSessionId,
        selectedLine?.id ?? null,
        selectedLine ? null : customLineName.trim() || null,
        'pending_sync'
      );

      const synced = await syncPendingRecordings();

      setShowLineModal(false);
      setCurrentSessionId(null);

      const msg =
        synced > 0
          ? `Recorded ${finalPoints.current} points over ${formatDuration(finalDuration.current)}. Synced to server.`
          : `Recorded ${finalPoints.current} points. Will sync when you're back online.`;
      Alert.alert('Recording Complete', msg);
    } catch (error) {
      console.error('Failed to save recording:', error);
      Alert.alert('Error', 'Failed to save recording.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDiscardRecording = () => {
    if (!currentSessionId) return;

    cancelRecording(currentSessionId);

    setShowLineModal(false);
    setCurrentSessionId(null);
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const renderLineItem = ({ item }: { item: Line }) => {
    const isSelected = selectedLine?.id === item.id;
    return (
      <TouchableOpacity
        style={[styles.lineCard, isSelected && styles.lineCardSelected]}
        onPress={() => {
          setSelectedLine(item);
          setCustomLineName('');
        }}
        activeOpacity={0.7}
      >
        <Text style={[styles.lineName, isSelected && styles.lineNameSelected]}>
          {item.name}
        </Text>
        {item.description && (
          <Text style={styles.lineDescription} numberOfLines={2}>
            {item.description}
          </Text>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <Header title="Registrar recorrido" />

      <ScrollView contentContainerStyle={styles.content}>

        {/* Recording Status */}
        {isRecording && (
          <ThemedView style={styles.statusSection}>
            <View style={styles.statusRow}>
              <View style={styles.statusItem}>
                <Text style={styles.statusValue}>{formatDuration(recordingDuration)}</Text>
                <Text style={styles.statusLabel}>Duration</Text>
              </View>
              <View style={styles.statusDivider} />
              <View style={styles.statusItem}>
                <Text style={styles.statusValue}>{pointsCollected}</Text>
                <Text style={styles.statusLabel}>Points</Text>
              </View>
            </View>
            <View style={styles.recordingIndicator}>
              <View style={styles.recordingDot} />
              <Text style={styles.recordingText}>Recording</Text>
            </View>
          </ThemedView>
        )}

        {/* Swipe Switch */}
        <View style={styles.switchContainer}>
          <SwipeSwitch
            value={isRecording}
            onValueChange={handleRecordingToggle}
            onLabel="Recording..."
            offLabel="Swipe to Record"
          />
        </View>

        {/* Instructions */}
        {!isRecording && !showLineModal && (
          <ThemedView style={styles.instructions}>
            <ThemedText style={styles.instructionText}>
              1. Swipe to start recording your trip
            </ThemedText>
            <ThemedText style={styles.instructionText}>
              2. Ride the transit (recording continues in background)
            </ThemedText>
            <ThemedText style={styles.instructionText}>
              3. Swipe left to stop when you're done
            </ThemedText>
            <ThemedText style={styles.instructionText}>
              4. Select the line you rode
            </ThemedText>
          </ThemedView>
        )}
      </ScrollView>

      {/* Line selection bottom modal */}
      <Modal
        visible={showLineModal}
        animationType="slide"
        transparent
        onRequestClose={handleDiscardRecording}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <View style={styles.modalHandle} />

            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select line</Text>
              <Text style={styles.modalSubtitle}>
                Which line did you ride?
              </Text>
            </View>

            {/* Trip summary */}
            <View style={styles.modalSummary}>
              <View style={styles.modalSummaryItem}>
                <Text style={styles.modalSummaryValue}>
                  {formatDuration(finalDuration.current)}
                </Text>
                <Text style={styles.modalSummaryLabel}>Duration</Text>
              </View>
              <View style={styles.modalSummaryDivider} />
              <View style={styles.modalSummaryItem}>
                <Text style={styles.modalSummaryValue}>{finalPoints.current}</Text>
                <Text style={styles.modalSummaryLabel}>Points</Text>
              </View>
            </View>

            {/* Line list */}
            <FlatList
              data={lines}
              keyExtractor={(item) => item.id.toString()}
              renderItem={renderLineItem}
              style={styles.lineList}
              contentContainerStyle={styles.lineListContent}
              ListEmptyComponent={
                <Text style={styles.noLines}>No lines available.</Text>
              }
              ListFooterComponent={
                <View style={styles.newLineSection}>
                  <Text style={styles.newLineLabel}>Or add new line</Text>
                  <TextInput
                    style={styles.newLineInput}
                    placeholder="Enter line name"
                    placeholderTextColor="#9CA3AF"
                    value={customLineName}
                    onChangeText={(text) => {
                      setCustomLineName(text);
                      if (text.trim()) setSelectedLine(null);
                    }}
                  />
                </View>
              }
            />

            {/* Actions */}
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.modalBtnCancel}
                onPress={handleDiscardRecording}
              >
                <Text style={styles.modalBtnCancelText}>Discard</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.modalBtnConfirm,
                  !canSave && styles.modalBtnConfirmDisabled,
                ]}
                onPress={handleConfirmLine}
                disabled={!canSave || isSaving}
              >
                <Text style={styles.modalBtnConfirmText}>
                  {isSaving ? 'Saving...' : 'Save'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

