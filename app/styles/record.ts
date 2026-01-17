import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
    container: {
      flex: 1,
    },
    content: {
      padding: 20,
    },
    header: {
      marginBottom: 24,
    },
    subtitle: {
      opacity: 0.7,
      marginTop: 4,
    },
    section: {
      marginBottom: 24,
    },
    sectionTitle: {
      marginBottom: 12,
    },
    lineScroll: {
      marginHorizontal: -20,
      paddingHorizontal: 20,
    },
    lineCard: {
      backgroundColor: '#F3F4F6',
      borderRadius: 12,
      padding: 16,
      marginRight: 12,
      minWidth: 140,
      borderWidth: 2,
      borderColor: 'transparent',
    },
    lineCardSelected: {
      borderColor: '#0a7ea4',
      backgroundColor: '#E0F2FE',
    },
    lineName: {
      fontSize: 16,
      fontWeight: '600',
      color: '#374151',
    },
    lineNameSelected: {
      color: '#0a7ea4',
    },
    lineDescription: {
      fontSize: 12,
      color: '#6B7280',
      marginTop: 4,
    },
    noLines: {
      opacity: 0.5,
      fontStyle: 'italic',
    },
    statusSection: {
      backgroundColor: '#F0FDF4',
      borderRadius: 16,
      padding: 20,
      marginBottom: 24,
    },
    statusRow: {
      flexDirection: 'row',
      justifyContent: 'center',
      alignItems: 'center',
    },
    statusItem: {
      alignItems: 'center',
      paddingHorizontal: 24,
    },
    statusValue: {
      fontSize: 32,
      fontWeight: '700',
      color: '#166534',
    },
    statusLabel: {
      fontSize: 14,
      color: '#15803D',
      marginTop: 4,
    },
    statusDivider: {
      width: 1,
      height: 40,
      backgroundColor: '#BBF7D0',
    },
    recordingIndicator: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      marginTop: 16,
    },
    recordingDot: {
      width: 10,
      height: 10,
      borderRadius: 5,
      backgroundColor: '#EF4444',
      marginRight: 8,
    },
    recordingText: {
      fontSize: 14,
      fontWeight: '500',
      color: '#166534',
    },
    switchContainer: {
      alignItems: 'center',
      marginVertical: 32,
    },
    instructions: {
      marginTop: 24,
      padding: 16,
      backgroundColor: '#F9FAFB',
      borderRadius: 12,
    },
    instructionText: {
      fontSize: 14,
      lineHeight: 24,
      opacity: 0.8,
    },
  });
  