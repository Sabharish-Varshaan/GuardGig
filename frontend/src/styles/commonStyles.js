import { StyleSheet } from "react-native";

import { appTheme } from "./theme";

export const commonStyles = StyleSheet.create({
  screen: {
    alignSelf: "center",
    backgroundColor: appTheme.colors.background,
    flex: 1,
    maxWidth: 960,
    width: "100%"
  },
  screenContent: {
    alignSelf: "center",
    maxWidth: 720,
    paddingHorizontal: appTheme.spacing.lg,
    paddingTop: appTheme.spacing.lg,
    paddingBottom: appTheme.spacing.xxl,
    width: "100%"
  },
  sectionGap: {
    marginTop: appTheme.spacing.lg
  }
});
