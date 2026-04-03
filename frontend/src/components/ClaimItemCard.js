import React from "react";
import { StyleSheet, Text, View } from "react-native";

import NeonCard from "./NeonCard";
import StatusBadge from "./StatusBadge";
import { appTheme } from "../styles/theme";

function formatRupee(value) {
  return `₹${value}`;
}

function formatStatus(value) {
  const normalized = String(value || "pending").toLowerCase();
  return normalized[0].toUpperCase() + normalized.slice(1);
}

export default function ClaimItemCard({ item, style }) {
  const statusLabel = formatStatus(item.status);
  const isApproved = statusLabel === "Approved";
  const claimType = item.type ? `${String(item.type).toUpperCase()} Event` : "Rain Event";

  return (
    <NeonCard style={style} variant="elevated">
      <View style={styles.topRow}>
        <Text numberOfLines={2} style={styles.trigger}>{claimType}</Text>
        <StatusBadge label={statusLabel} variant={isApproved ? "success" : statusLabel === "Rejected" ? "danger" : "warning"} />
      </View>
      <Text style={[styles.payout, { color: isApproved ? appTheme.colors.semanticSafe : appTheme.colors.semanticWarning }]}>
        {formatRupee(item.amount)}
      </Text>
      <Text style={styles.meta}>{item.timestamp}</Text>
    </NeonCard>
  );
}

const styles = StyleSheet.create({
  topRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between"
  },
  trigger: {
    color: appTheme.colors.textPrimary,
    flex: 1,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 17,
    lineHeight: 22,
    paddingRight: appTheme.spacing.sm
  },
  payout: {
    fontFamily: "Orbitron_700Bold",
    fontSize: 30,
    marginTop: appTheme.spacing.sm
  },
  meta: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_500Medium",
    fontSize: 14,
    marginTop: appTheme.spacing.xs
  }
});