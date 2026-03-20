import React from "react";
import { StyleSheet, Text, View } from "react-native";

import Card from "./Card";
import { appTheme } from "../styles/theme";

const levelColorMap = {
  danger: appTheme.colors.danger,
  info: appTheme.colors.textSecondary,
  success: appTheme.colors.accent,
  warning: appTheme.colors.warning
};

export default function LogPanel({ logs = [] }) {
  return (
    <Card style={styles.card}>
      <Text style={styles.title}>Event Log</Text>

      {logs.length === 0 && <Text style={styles.emptyText}>No events yet.</Text>}

      {logs.slice(0, 8).map((log) => (
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
    color: appTheme.colors.primary,
    fontSize: 18,
    fontWeight: "700",
    marginBottom: appTheme.spacing.sm
  },
  emptyText: {
    color: appTheme.colors.textSecondary,
    fontSize: 14,
    fontWeight: "600"
  },
  logRow: {
    flexDirection: "row",
    marginBottom: appTheme.spacing.xs
  },
  timeText: {
    color: appTheme.colors.textSecondary,
    fontSize: 12,
    fontWeight: "700",
    marginRight: appTheme.spacing.xs,
    minWidth: 52
  },
  messageText: {
    flex: 1,
    fontSize: 13,
    fontWeight: "600",
    lineHeight: 18
  }
});
