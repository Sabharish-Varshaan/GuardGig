export const colors = {
  bgPrimary: "#050A14",
  bgCard: "#0A1628",
  bgElevated: "#0F1F3D",
  accentPrimary: "#00D4FF",
  accentSuccess: "#00FF94",
  accentWarning: "#FFB800",
  accentDanger: "#FF4560",
  textPrimary: "#E8F4FD",
  textSecondary: "#6D8AA9",
  textDisabled: "#3A556E",
  borderSubtle: "rgba(0,212,255,0.15)",
  borderStrong: "rgba(0,212,255,0.4)",
  glowSoft: "rgba(0,212,255,0.14)",
  glowStrong: "rgba(0,212,255,0.28)",
  gradientCyanStart: "#00B8E6",
  gradientCyanEnd: "#007CFF",
  gradientDarkStart: "#081426",
  gradientDarkEnd: "#102444",
  overlaySoft: "rgba(5,10,20,0.55)",
  successSoft: "rgba(0,255,148,0.14)",
  successText: "#00FF94",
  successBorder: "rgba(0,255,148,0.45)",
  warningSoft: "rgba(255,184,0,0.14)",
  warningText: "#FFB800",
  warningBorder: "rgba(255,184,0,0.45)",
  dangerSoft: "rgba(255,69,96,0.14)",
  dangerText: "#FF4560",
  dangerBorder: "rgba(255,69,96,0.45)",
  infoSoft: "rgba(0,212,255,0.14)",
  infoBorder: "rgba(0,212,255,0.45)",
  mutedBlue: "#0C1A31",
  chipBg: "#0D1C34",
  chipBorder: "rgba(0,212,255,0.25)",
  tabGlass: "rgba(9,20,37,0.95)",
  cardGlass: "rgba(10,22,40,0.95)",
  cardGlassBorder: "rgba(0,212,255,0.2)",
  semanticSafe: "#00FF94",
  semanticWarning: "#FFB800",
  semanticHighRisk: "#FF4560",
  semanticPayout: "#00D4FF",
  semanticFocus: "rgba(0,212,255,0.4)",
  semanticSurfaceMuted: "#0B1A30",
  background: "#050A14",
  surface: "#0A1628",
  primary: "#00D4FF",
  accent: "#00D4FF",
  accentAlt: "#00FF94",
  warning: "#FFB800",
  danger: "#FF4560",
  textInverse: "#E8F4FD",
  border: "rgba(0,212,255,0.15)",
  borderSoft: "rgba(0,212,255,0.24)",
  cardTint: "#0A1628",
  switchTrackOff: "#1A2D45",
  switchTrackOn: "rgba(0,255,148,0.38)",
  switchThumbOff: "#3A556E",
  overlay: "rgba(5,10,20,0.55)",
  gradientA: "#081426",
  gradientB: "#102444",
  gradientC: "#050A14"
};

export const spacing = {
  xs: 8,
  sm: 18,
  md: 26,
  lg: 32,
  xl: 40,
  xxl: 48
};

export const radius = {
  card: 16,
  soft: 12,
  input: 14,
  pill: 999
};

export const typography = {
  display: {
    fontFamily: "Orbitron_700Bold",
    fontSize: 34,
    letterSpacing: 0.5,
    lineHeight: 42
  },
  h1: {
    fontFamily: "Orbitron_700Bold",
    fontSize: 28,
    letterSpacing: 0.3,
    lineHeight: 34
  },
  h2: {
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 22,
    lineHeight: 28
  },
  h3: {
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 18,
    lineHeight: 24
  },
  subtitle: {
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 16,
    lineHeight: 22,
    letterSpacing: 0.4
  },
  body: {
    fontFamily: "Rajdhani_500Medium",
    fontSize: 16,
    lineHeight: 22
  },
  caption: {
    fontFamily: "Rajdhani_500Medium",
    fontSize: 13,
    lineHeight: 18,
    letterSpacing: 0.2
  },
  metric: {
    fontFamily: "Orbitron_700Bold",
    fontSize: 32,
    lineHeight: 36,
    letterSpacing: 0.6
  },
  label: {
    fontFamily: "Rajdhani_700Bold",
    fontSize: 12,
    letterSpacing: 0.4,
    textTransform: "uppercase"
  }
};

export const shadows = {
  soft: {
    shadowColor: "#00D4FF",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 3
  },
  card: {
    shadowColor: "#00D4FF",
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.1,
    shadowRadius: 14,
    elevation: 4
  },
  floating: {
    shadowColor: "#00D4FF",
    shadowOffset: { width: 0, height: 16 },
    shadowOpacity: 0.12,
    shadowRadius: 18,
    elevation: 6
  },
  glow: {
    shadowColor: "#00D4FF",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.14,
    shadowRadius: 10,
    elevation: 5
  }
};

export const motion = {
  duration: {
    quick: 250,
    normal: 320,
    slow: 420
  },
  disabledOpacity: 0.5
};

export const appTheme = {
  colors,
  spacing,
  radius,
  typography,
  shadows,
  motion
};
