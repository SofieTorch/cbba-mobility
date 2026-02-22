import { StyleSheet, Text, View } from "react-native";

export default function Header({ title }: { title: string }) {
  return (
    <View style={styles.header}>
      <Text style={styles.title}>{title}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  header: {
    backgroundColor: '#09A6F3',
    alignItems: 'center',
    padding: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: '500',
    color: '#FFFFFF',
  }
})