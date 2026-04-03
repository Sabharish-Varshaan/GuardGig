import React, { useEffect, useMemo, useRef } from "react";
import { Animated, StyleSheet, Text, View } from "react-native";

import Card from "./Card";
import StepLoader from "./StepLoader";
import StatusBadge from "./StatusBadge";
import { appTheme } from "../styles/theme";

const STATE_META = {
  idle: {
    emoji: "🛰️",
    message: "Idle",
    tone: "info"
  },
  checking_conditions: {
    emoji: "⚙️",
    message: "Checking conditions",
    tone: "warning"
  },
  validating: {
    emoji: "🧾",
    message: "Validating eligibility",
    tone: "warning"
  },
  fraud_check: {
    emoji: "🔍",
    message: "Fraud check",
    tone: "warning"
  },
  approved: {
    emoji: "✅",
    message: "Approved",
    tone: "success"
  },
  flagged: {
    emoji: "⚠️",
    message: "Flagged",
    tone: "danger"
  }
};

const toneStyleMap = {
  danger: {
    backgroundColor: appTheme.colors.dangerSoft,
    borderColor: appTheme.colors.dangerBorder
  },
  info: {
    backgroundColor: appTheme.colors.infoSoft,
    borderColor: appTheme.colors.infoBorder
  },
  success: {
    backgroundColor: appTheme.colors.successSoft,
    borderColor: appTheme.colors.successBorder
  },
  warning: {
    backgroundColor: appTheme.colors.warningSoft,
    borderColor: appTheme.colors.warningBorder
  }
};

export default function StatusCard({ workflowState, payoutAmount, movementScore }) {
  const fade = useRef(new Animated.Value(0)).current;
  const slide = useRef(new Animated.Value(8)).current;

  const statusMeta = useMemo(() => {
    return STATE_META[workflowState] || STATE_META.idle;
  }, [workflowState]);

  const resolvedMessage = useMemo(() => {
    if (workflowState === "approved") {
      return `Payout released: ₹${payoutAmount || 500} credited instantly.`;
    }

    if (workflowState === "flagged") {
      return "Verification required before payout release.";
    }

    if (workflowState === "checking_conditions") {
      return "Heavy rain detected. Checking trigger conditions...";
    }

    if (workflowState === "validating") {
      return "Claim being processed. Validating policy eligibility...";
    }

    if (workflowState === "fraud_check") {
      return "Running fraud detection...";
    }

    return "Monitoring conditions. Tap Check Coverage to start workflow.";
  }, [workflowState, payoutAmount]);

  const isInProgress =
    workflowState === "checking_conditions" ||
    workflowState === "validating" ||
    workflowState === "fraud_check";

  useEffect(() => {
    fade.setValue(0);
    slide.setValue(8);

    Animated.parallel([
      Animated.timing(fade, {
        duration: 220,
        toValue: 1,
        useNativeDriver: true
      }),
      Animated.timing(slide, {
        duration: 220,
        toValue: 0,
        useNativeDriver: true
      })
    ]).start();
  }, [workflowState, fade, slide]);

  return (
    <Animated.View style={{ opacity: fade, transform: [{ translateY: slide }] }}>
      <Card style={[styles.card, toneStyleMap[statusMeta.tone]]}>
        <View style={styles.headerRow}>
          <Text style={styles.title}>Coverage Workflow</Text>
          <StatusBadge
            label={`${statusMeta.emoji} ${statusMeta.message}`}
            variant={statusMeta.tone === "info" ? "info" : statusMeta.tone}
            style={styles.badge}
          />
        </View>
        <Text style={styles.message}>{resolvedMessage}</Text>
        {isInProgress && (
          <StepLoader
            label={
              workflowState === "checking_conditions"
                ? "Checking conditions"
                : workflowState === "validating"
                  ? "Validating eligibility"
                  : "Running fraud detection"
            }
            tone="warning"
          />
        )}
        {workflowState === "fraud_check" && (
          <Text style={styles.helperText}>{`Movement score: ${movementScore}`}</Text>
        )}
      </Card>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginBottom: appTheme.spacing.lg,
    borderWidth: 0.8,
    paddingVertical: 12
  },
  headerRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    marginBottom: appTheme.spacing.xs
  },
  title: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 15,
    letterSpacing: 0.2,
    marginBottom: appTheme.spacing.xs,
    paddingRight: appTheme.spacing.sm
  },
  message: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 15,
    lineHeight: 20
  },
  helperText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 12,
    marginTop: appTheme.spacing.xs
  },
  badge: {
    flexBasis: "100%",
    marginBottom: appTheme.spacing.xs
  }
});
