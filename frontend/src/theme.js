import { extendTheme } from '@chakra-ui/react'

const config = {
  initialColorMode: 'dark',
  useSystemColorMode: false,
}

const colors = {
  brand: {
    50: '#e0fff4',
    100: '#b3ffde',
    200: '#80ffc8',
    300: '#4dffb2',
    400: '#1aff9c',
    500: '#00ff94', // Neon Green Main
    600: '#00cc76',
    700: '#009959',
    800: '#00663b',
    900: '#00331d',
  },
  dark: {
    bg: '#000000',
    card: '#111111',
    border: '#222222',
    hover: '#1a1a1a',
    text: '#EDEDED',
    muted: '#888888',
  },
  accent: {
    blue: '#0070F3',
    purple: '#7928CA',
    cyan: '#50E3C2',
    pink: '#FF0080',
  }
}

const fonts = {
  heading: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
  body: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
  mono: '"JetBrains Mono", "Fira Code", "Roboto Mono", monospace',
}

const components = {
  Button: {
    baseStyle: {
      fontWeight: 'medium',
      borderRadius: 'md',
    },
    variants: {
      solid: (props) => ({
        bg: props.colorScheme === 'brand' ? 'brand.500' : undefined,
        color: props.colorScheme === 'brand' ? 'black' : undefined,
        _hover: {
          bg: props.colorScheme === 'brand' ? 'brand.400' : undefined,
        },
      }),
      ghost: {
        _hover: {
          bg: 'dark.hover',
        },
      },
    },
  },
  Card: {
    baseStyle: {
      container: {
        bg: 'dark.card',
        borderColor: 'dark.border',
        borderWidth: '1px',
        borderRadius: 'lg',
        boxShadow: 'none',
      },
    },
  },
  Table: {
    variants: {
      simple: {
        th: {
          borderColor: 'dark.border',
          color: 'dark.muted',
          fontFamily: 'mono',
          textTransform: 'uppercase',
          fontSize: 'xs',
          letterSpacing: 'wider',
        },
        td: {
          borderColor: 'dark.border',
        },
      },
    },
  },
}

const styles = {
  global: {
    body: {
      bg: 'dark.bg',
      color: 'dark.text',
    },
    '::-webkit-scrollbar': {
      width: '8px',
      height: '8px',
    },
    '::-webkit-scrollbar-track': {
      bg: 'dark.bg',
    },
    '::-webkit-scrollbar-thumb': {
      bg: 'dark.border',
      borderRadius: '4px',
    },
    '::-webkit-scrollbar-thumb:hover': {
      bg: 'dark.muted',
    },
  },
}

const theme = extendTheme({ config, colors, fonts, components, styles })

export default theme
