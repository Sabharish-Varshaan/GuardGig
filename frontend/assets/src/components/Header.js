import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { appTheme } from "../styles/theme";

export default function Header({ title, subtitle, rightElement }) {
  return (
    <View style={styles.container}>
      <View style={styles.leftColumn}>
        <Text style={styles.title}>{title}</Text>
        {!!subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      </View>
      {!!rightElement && <View style={styles.rightColumn}>{rightElement}</View>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: appTheme.spacing.xl
  },
  leftColumn: {
    flex: 1,
    paddingRight: appTheme.spacing.md
  },
  rightColumn: {
    alignItems: "flex-end",
    justifyContent: "center"
  },
  title: {
    color: appTheme.colors.primary,
    fontSize: appTheme.typography.h1.fontSize,
    letterSpacing: appTheme.typography.h1.letterSpacing,
    fontWeight: "700",
    lineHeight: 38
  },
  subtitle: {
    color: appTheme.colors.textSecondary,
    fontSize: 14,
    fontWeight: "500",
    lineHeight: 20,
    marginTop: appTheme.spacing.xs
  }
});
