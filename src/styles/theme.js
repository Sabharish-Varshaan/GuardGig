export const colors = {
  primary: "#0B3C5D",
  accent: "#00C897",
  warning: "#FFC857",
  danger: "#FF4D4D",
  background: "#F4F6F8",
  surface: "#FFFFFF",
  textPrimary: "#102A43",
  textSecondary: "#5B7083",
  border: "#E4EAF0",
  mutedBlue: "#E7F0F7"
};

export const spacing = {
  xs: 6,
  sm: 10,
  md: 16,
  lg: 20,
  xl: 28,
  xxl: 36
};

export const radius = {
  card: 16,
  soft: 12,
  pill: 999
};

export const typography = {
  h1: {
    fontSize: 30,
    fontWeight: "700",
    letterSpacing: 0.2
  },
  h2: {
    fontSize: 24,
    fontWeight: "700"
  },
  h3: {
    fontSize: 18,
    fontWeight: "700"
  },
  body: {
    fontSize: 15,
    fontWeight: "500"
  },
  label: {
    fontSize: 13,
    fontWeight: "600"
  }
};

export const shadows = {
  soft: {
    shadowColor: "#0B3C5D",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.08,
    shadowRadius: 18,
    elevation: 4
  },
  card: {
    shadowColor: "#0B3C5D",
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.12,
    shadowRadius: 20,
    elevation: 6
  }
};

export const appTheme = {
  colors,
  spacing,
  radius,
  typography,
  shadows
};
