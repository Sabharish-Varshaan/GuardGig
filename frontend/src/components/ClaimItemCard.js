import React from "react";
import { StyleSheet, Text, View } from "react-native";

import NeonCard from "./NeonCard";
import StatusBadge from "./StatusBadge";
import { appTheme } from "../styles/theme";

function formatRupee(value) {
  return `₹${value}`;
}

export default function ClaimItemCard({ item, style }) {
  const isApproved = item.status === "Approved";
  const claimType = item.type ? `${String(item.type).toUpperCase()} EVENT` : "RAIN EVENT";

  return (
    <NeonCard style={style} variant="elevated">
      <View style={styles.topRow}>
        <Text numberOfLines={2} style={styles.trigger}>{claimType}</Text>
        <StatusBadge label={item.status} variant={isApproved ? "success" : "warning"} />
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