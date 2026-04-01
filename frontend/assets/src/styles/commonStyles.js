import { StyleSheet } from "react-native";

import { appTheme } from "./theme";

export const commonStyles = StyleSheet.create({
  screen: {
    backgroundColor: appTheme.colors.background,
    flex: 1
  },
  screenContent: {
    paddingHorizontal: appTheme.spacing.lg,
    paddingTop: appTheme.spacing.lg,
    paddingBottom: appTheme.spacing.xxl
  },
  sectionGap: {
    marginTop: appTheme.spacing.lg
  }
});
