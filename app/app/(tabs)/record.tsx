/**
 * Record tab - Start/stop recording transit data.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Alert,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Location from 'expo-location';
import { Accelerometer, Gyroscope } from 'expo-sensors';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { SwipeSwitch } from '@/components/swipe-switch';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import api, { Line, RecordingSession, LocationPoint, SensorReading } from '@/services/api';
import { styles } from '@/styles/record';

// TODO: Replace with actual user authentication
const MOCK_USER_ID = 1;

// Upload batch every 30 seconds
const BATCH_UPLOAD_INTERVAL = 30000;

// Collect location every 2 seconds
const LOCATION_INTERVAL = 2000;

// Collect sensors at 10Hz
const SENSOR_INTERVAL = 100;

export default function RecordScreen() {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme ?? 'light'];

  // State
  const [isRecording, setIsRecording] = useState(false);
  const [selectedLine, setSelectedLine] = useState<Line | null>(null);
  const [lines, setLines] = useState<Line[]>([]);
  const [currentSession, setCurrentSession] = useState<RecordingSession | null>(null);
  const [locationPermission, setLocationPermission] = useState<boolean>(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [pointsCollected, setPointsCollected] = useState(0);

  // Refs for data collection
  const locationBuffer = useRef<LocationPoint[]>([]);
  const sensorBuffer = useRef<SensorReading[]>([]);
  const locationSubscription = useRef<Location.LocationSubscription | null>(null);
  const accelSubscription = useRef<ReturnType<typeof Accelerometer.addListener> | null>(null);
  const gyroSubscription = useRef<ReturnType<typeof Gyroscope.addListener> | null>(null);
  const uploadInterval = useRef<ReturnType<typeof setInterval> | null>(null);
  const durationInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  // Load lines on mount
  useEffect(() => {
    loadLines();
    requestLocationPermission();
  }, []);

  const loadLines = async () => {
    try {
      const fetchedLines = await api.getLines('approved');
      setLines(fetchedLines);
    } catch (error) {
      console.error('Failed to load lines:', error);
    }
  };

  const requestLocationPermission = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    setLocationPermission(status === 'granted');
    
    if (status !== 'granted') {
      Alert.alert(
        'Location Permission Required',
        'Please enable location services to record transit data.',
        [{ text: 'OK' }]
      );
    }
  };

  const startDataCollection = useCallback(async (sessionId: number) => {
    // Start location tracking
    locationSubscription.current = await Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.BestForNavigation,
        timeInterval: LOCATION_INTERVAL,
        distanceInterval: 5, // meters
      },
      (location) => {
        const point: LocationPoint = {
          timestamp: new Date(location.timestamp).toISOString(),
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
          altitude: location.coords.altitude,
          speed: location.coords.speed,
          bearing: location.coords.heading,
          horizontal_accuracy: location.coords.accuracy,
          vertical_accuracy: location.coords.altitudeAccuracy,
        };
        locationBuffer.current.push(point);
        setPointsCollected((prev) => prev + 1);
      }
    );

    // Start accelerometer
    Accelerometer.setUpdateInterval(SENSOR_INTERVAL);
    accelSubscription.current = Accelerometer.addListener((data) => {
      // We'll combine with gyro data on upload
      const reading: Partial<SensorReading> = {
        timestamp: new Date().toISOString(),
        accel_x: data.x,
        accel_y: data.y,
        accel_z: data.z,
      };
      // Store temporarily - we'll merge with gyro
      (reading as any)._accel = true;
      sensorBuffer.current.push(reading as SensorReading);
    });

    // Start gyroscope
    Gyroscope.setUpdateInterval(SENSOR_INTERVAL);
    gyroSubscription.current = Gyroscope.addListener((data) => {
      const reading: Partial<SensorReading> = {
        timestamp: new Date().toISOString(),
        gyro_x: data.x,
        gyro_y: data.y,
        gyro_z: data.z,
      };
      (reading as any)._gyro = true;
      sensorBuffer.current.push(reading as SensorReading);
    });

    // Start batch upload interval
    uploadInterval.current = setInterval(() => {
      uploadBatch(sessionId);
    }, BATCH_UPLOAD_INTERVAL);

    // Start duration timer
    durationInterval.current = setInterval(() => {
      setRecordingDuration((prev) => prev + 1);
    }, 1000);
  }, []);

  const stopDataCollection = useCallback(() => {
    // Stop location tracking
    if (locationSubscription.current) {
      locationSubscription.current.remove();
      locationSubscription.current = null;
    }

    // Stop sensors
    if (accelSubscription.current) {
      accelSubscription.current.remove();
      accelSubscription.current = null;
    }
    if (gyroSubscription.current) {
      gyroSubscription.current.remove();
      gyroSubscription.current = null;
    }

    // Stop intervals
    if (uploadInterval.current) {
      clearInterval(uploadInterval.current);
      uploadInterval.current = null;
    }
    if (durationInterval.current) {
      clearInterval(durationInterval.current);
      durationInterval.current = null;
    }
  }, []);

  const uploadBatch = async (sessionId: number) => {
    // Upload location points
    if (locationBuffer.current.length > 0) {
      const points = [...locationBuffer.current];
      locationBuffer.current = [];
      
      try {
        await api.uploadLocationBatch(sessionId, points);
        console.log(`Uploaded ${points.length} location points`);
      } catch (error) {
        console.error('Failed to upload locations:', error);
        // Re-add points to buffer on failure
        locationBuffer.current = [...points, ...locationBuffer.current];
      }
    }

    // Upload sensor readings (simplified - just upload as-is)
    if (sensorBuffer.current.length > 0) {
      const readings = [...sensorBuffer.current];
      sensorBuffer.current = [];
      
      try {
        await api.uploadSensorBatch(sessionId, readings);
        console.log(`Uploaded ${readings.length} sensor readings`);
      } catch (error) {
        console.error('Failed to upload sensors:', error);
        // Re-add readings to buffer on failure
        sensorBuffer.current = [...readings, ...sensorBuffer.current];
      }
    }
  };

  const handleRecordingToggle = async (shouldRecord: boolean) => {
    if (shouldRecord) {
      // Start recording
      if (!selectedLine) {
        Alert.alert('Select a Line', 'Please select a transit line before recording.');
        return;
      }

      if (!locationPermission) {
        Alert.alert('Permission Required', 'Location permission is required to record.');
        return;
      }

      try {
        const session = await api.startRecording(
          MOCK_USER_ID,
          selectedLine.id,
          undefined, // direction
          Platform.OS,
          Platform.Version?.toString()
        );
        
        setCurrentSession(session);
        setIsRecording(true);
        setRecordingDuration(0);
        setPointsCollected(0);
        
        await startDataCollection(session.id);
      } catch (error) {
        console.error('Failed to start recording:', error);
        Alert.alert('Error', 'Failed to start recording. Please try again.');
      }
    } else {
      // Stop recording
      if (!currentSession) return;

      try {
        // Upload any remaining data
        await uploadBatch(currentSession.id);
        
        // Stop data collection
        stopDataCollection();
        
        // End the session on server
        await api.endRecording(currentSession.id);
        
        setIsRecording(false);
        setCurrentSession(null);
        
        Alert.alert(
          'Recording Complete',
          `Recorded ${pointsCollected} location points over ${formatDuration(recordingDuration)}.`
        );
      } catch (error) {
        console.error('Failed to end recording:', error);
        Alert.alert('Error', 'Failed to end recording properly.');
        setIsRecording(false);
        setCurrentSession(null);
        stopDataCollection();
      }
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView contentContainerStyle={styles.content}>
        {/* Header */}
        <ThemedView style={styles.header}>
          <ThemedText type="title">Record Trip</ThemedText>
          <ThemedText style={styles.subtitle}>
            Select a line and swipe to start recording
          </ThemedText>
        </ThemedView>

        {/* Line Selection */}
        {!isRecording && (
          <ThemedView style={styles.section}>
            <ThemedText type="subtitle" style={styles.sectionTitle}>
              Select Line
            </ThemedText>
            <ScrollView 
              horizontal 
              showsHorizontalScrollIndicator={false}
              style={styles.lineScroll}
            >
              {lines.map((line) => (
                <TouchableOpacity
                  key={line.id}
                  style={[
                    styles.lineCard,
                    selectedLine?.id === line.id && styles.lineCardSelected,
                  ]}
                  onPress={() => setSelectedLine(line)}
                >
                  <Text
                    style={[
                      styles.lineName,
                      selectedLine?.id === line.id && styles.lineNameSelected,
                    ]}
                  >
                    {line.name}
                  </Text>
                  {line.description && (
                    <Text style={styles.lineDescription} numberOfLines={1}>
                      {line.description}
                    </Text>
                  )}
                </TouchableOpacity>
              ))}
              {lines.length === 0 && (
                <ThemedText style={styles.noLines}>
                  No lines available. Create one first.
                </ThemedText>
              )}
            </ScrollView>
          </ThemedView>
        )}

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
              <Text style={styles.recordingText}>Recording {selectedLine?.name}</Text>
            </View>
          </ThemedView>
        )}

        {/* Swipe Switch */}
        <View style={styles.switchContainer}>
          <SwipeSwitch
            value={isRecording}
            onValueChange={handleRecordingToggle}
            disabled={!selectedLine && !isRecording}
            onLabel="Recording..."
            offLabel="Swipe to Record"
          />
        </View>

        {/* Instructions */}
        {!isRecording && (
          <ThemedView style={styles.instructions}>
            <ThemedText style={styles.instructionText}>
              1. Select a transit line above
            </ThemedText>
            <ThemedText style={styles.instructionText}>
              2. Swipe the switch to the right to start recording
            </ThemedText>
            <ThemedText style={styles.instructionText}>
              3. Ride the transit and keep the app open
            </ThemedText>
            <ThemedText style={styles.instructionText}>
              4. Swipe left to stop recording when done
            </ThemedText>
          </ThemedView>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

