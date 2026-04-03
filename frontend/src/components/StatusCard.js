import React, { useEffect, useMemo, useRef } from "react";
import { Animated, StyleSheet, Text, View } from "react-native";

import Card from "./Card";
import StepLoader from "./StepLoader";
import StatusBadge from "./StatusBadge";
import { appTheme } from "../styles/theme";

const STATE_META = {
  idle: {
    message: "Standby",
    tone: "info"
  },
  checking_conditions: {
    message: "Checking conditions",
    tone: "warning"
  },
  validating: {
    message: "Trigger detected",
    tone: "warning"
  },
  fraud_check: {
    message: "Processing claim",
    tone: "warning"
  },
  approved: {
    message: "Claim approved",
    tone: "success"
  },
  flagged: {
    message: "Conditions not met",
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
      return `Claim Approved ✅ Payout released: ₹${payoutAmount || 0}.`;
    }

    if (workflowState === "flagged") {
      return "Conditions not met for automated claim approval.";
    }

    if (workflowState === "checking_conditions") {
      return "Checking live conditions...";
    }

    if (workflowState === "validating") {
      return "Trigger detected... Validating eligibility...";
    }

    if (workflowState === "fraud_check") {
      return "Processing claim...";
    }

    return "System idle. Tap Check Coverage to run automated verification.";
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
            label={statusMeta.message}
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
                  : "Processing claim"
            }
            tone="warning"
          />
        )}
        {workflowState === "fraud_check" && movementScore !== null && movementScore !== undefined && (
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
    overflow: "hidden",
    paddingHorizontal: 12,
    paddingVertical: 10
  },
  headerRow: {
    alignItems: "flex-start",
    flexDirection: "column",
    marginBottom: 6
  },
  title: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 15,
    letterSpacing: 0.2,
    marginBottom: 6
  },
  message: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    lineHeight: 20,
    marginTop: 0
  },
  helperText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 12,
    marginTop: appTheme.spacing.xs
  },
  badge: {
    marginLeft: 0,
    marginTop: 0
  }
});
