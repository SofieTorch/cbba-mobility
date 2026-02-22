import { useTheme } from '@react-navigation/native';

type ThemeColorKey = 'primary' | 'background' | 'card' | 'text' | 'border' | 'notification';

export function useThemeColor(
  props: { light?: string; dark?: string },
  colorName: ThemeColorKey
) {
  const { dark, colors } = useTheme();
  const colorFromProps = props[dark ? 'dark' : 'light'];

  return colorFromProps ?? colors[colorName];
}
