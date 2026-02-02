import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const HEADER_BLUE = '#09A6F3';
const SEGMENT_ACTIVE = 'rgba(255, 255, 255, 0.35)';
const SEGMENT_INACTIVE = 'transparent';

type Segment = 'lineas' | 'mapa';

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const [segment, setSegment] = useState<Segment>('lineas');

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Explorar</Text>
        <View style={styles.segmentedControl}>
          <Pressable
            style={[
              styles.segment,
              segment === 'lineas' && styles.segmentActive,
            ]}
            onPress={() => setSegment('lineas')}
          >
            <Text
              style={[
                styles.segmentText,
                segment === 'lineas' && styles.segmentTextActive,
              ]}
            >
              Líneas
            </Text>
          </Pressable>
          <Pressable
            style={[
              styles.segment,
              segment === 'mapa' && styles.segmentActive,
            ]}
            onPress={() => setSegment('mapa')}
          >
            <Text
              style={[
                styles.segmentText,
                segment === 'mapa' && styles.segmentTextActive,
              ]}
            >
              Mapa
            </Text>
          </Pressable>
        </View>
      </View>

      {/* Content card */}
      <View style={styles.card}>
        {/* Placeholder for Líneas or Mapa content */}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#E5E7EB',
  },
  header: {
    backgroundColor: HEADER_BLUE,
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 28,
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 16,
  },
  segmentedControl: {
    flexDirection: 'row',
    backgroundColor: 'rgba(0, 0, 0, 0.15)',
    borderRadius: 9999,
    padding: 4,
    maxWidth: 280,
    alignSelf: 'center',
  },
  segment: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 9999,
    alignItems: 'center',
    justifyContent: 'center',
  },
  segmentActive: {
    backgroundColor: SEGMENT_ACTIVE,
  },
  segmentText: {
    fontSize: 15,
    fontWeight: '500',
    color: 'rgba(255, 255, 255, 0.9)',
  },
  segmentTextActive: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  card: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    marginTop: -16,
    minHeight: 400,
  },
});
