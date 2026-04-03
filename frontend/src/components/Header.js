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
    color: appTheme.colors.textPrimary,
    ...appTheme.typography.h1
  },
  subtitle: {
    color: appTheme.colors.textSecondary,
    ...appTheme.typography.body,
    marginTop: appTheme.spacing.xs
  }
});
