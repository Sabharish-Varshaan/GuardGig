export const colors = {
  primary: "#10243E",
  accent: "#FF6B3D",
  accentAlt: "#28C2A0",
  warning: "#F7B844",
  danger: "#E74B5E",
  dangerText: "#B83B53",
  dangerSoft: "#FFE7EC",
  background: "#ECF2F8",
  surface: "#FFFFFF",
  textPrimary: "#142A44",
  textSecondary: "#60758E",
  textInverse: "#F8FBFF",
  border: "#D7E2ED",
  borderSoft: "#E6EEF7",
  mutedBlue: "#DDEBFA",
  successSoft: "#E7F8F2",
  successText: "#0B8A63",
  successBorder: "#C1F0E0",
  warningSoft: "#FFF2DB",
  warningText: "#996300",
  warningBorder: "#F9DFA8",
  infoSoft: "#E6F0FB",
  infoBorder: "#C7DBF3",
  dangerBorder: "#F9C7D1",
  chipBg: "#E7EFF8",
  chipBorder: "#D3E0ED",
  cardTint: "#F7FAFE",
  switchTrackOff: "#D9E2EC",
  switchTrackOn: "#BDEFD9",
  switchThumbOff: "#C9D4E0",
  tabGlass: "rgba(255,255,255,0.92)",
  cardGlass: "rgba(255,255,255,0.96)",
  cardGlassBorder: "rgba(255,255,255,0.5)",
  overlay: "rgba(16,36,62,0.08)",
  gradientA: "#122A4A",
  gradientB: "#214D80",
  gradientC: "#ECF2F8"
};

export const spacing = {
  xs: 6,
  sm: 10,
  md: 16,
  lg: 22,
  xl: 30,
  xxl: 40
};

export const radius = {
  card: 20,
  soft: 14,
  input: 16,
  pill: 999
};

export const typography = {
  h1: {
    fontSize: 32,
    fontWeight: "700",
    letterSpacing: -0.4
  },
  h2: {
    fontSize: 25,
    fontWeight: "700"
  },
  h3: {
    fontSize: 19,
    fontWeight: "700"
  },
  body: {
    fontSize: 15,
    fontWeight: "500"
  },
  label: {
    fontSize: 12,
    letterSpacing: 0.4,
    fontWeight: "600"
  }
};

export const shadows = {
  soft: {
    shadowColor: "#10243E",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.08,
    shadowRadius: 14,
    elevation: 4
  },
  card: {
    shadowColor: "#10243E",
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.1,
    shadowRadius: 20,
    elevation: 6
  },
  floating: {
    shadowColor: "#0F2138",
    shadowOffset: { width: 0, height: 16 },
    shadowOpacity: 0.18,
    shadowRadius: 26,
    elevation: 10
  }
};

export const appTheme = {
  colors,
  spacing,
  radius,
  typography,
  shadows
};
