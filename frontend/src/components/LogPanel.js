import React from "react";
import { StyleSheet, Text, View } from "react-native";

import Card from "./Card";
import { appTheme } from "../styles/theme";

const levelColorMap = {
  danger: appTheme.colors.danger,
  info: appTheme.colors.textSecondary,
  success: appTheme.colors.accentSuccess,
  warning: appTheme.colors.warning
};

export default function LogPanel({ logs = [] }) {
  return (
    <Card style={styles.card}>
      <Text style={styles.title}>Event Log</Text>

      {logs.length === 0 && <Text style={styles.emptyText}>No events yet.</Text>}

      {logs.slice(0, 5).map((log) => (
        <View key={log.id} style={styles.logRow}>
          <Text style={styles.timeText}>{`[${log.time}]`}</Text>
          <Text
            style={[
              styles.messageText,
              { color: levelColorMap[log.level] || appTheme.colors.textSecondary }
            ]}
          >
            {log.message}
          </Text>
        </View>
      ))}
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    marginBottom: appTheme.spacing.md
  },
  title: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 17,
    letterSpacing: 0.2,
    marginBottom: appTheme.spacing.md
  },
  emptyText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14
  },
  logRow: {
    borderBottomColor: appTheme.colors.borderSubtle,
    borderBottomWidth: 1,
    flexDirection: "row",
    marginBottom: appTheme.spacing.sm,
    paddingBottom: appTheme.spacing.sm
  },
  timeText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 13,
    letterSpacing: 0.2,
    marginRight: appTheme.spacing.xs,
    minWidth: 60
  },
  messageText: {
    flex: 1,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    lineHeight: 20
  }
});
