import React, { useEffect, useMemo, useRef } from "react";
import { Animated, FlatList, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import Card from "../components/Card";
import Header from "../components/Header";
import LogPanel from "../components/LogPanel";
import StatusCard from "../components/StatusCard";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

function formatRupee(value) {
  return `₹${value}`;
}

export default function ClaimsScreen() {
  const {
    claimsHistory,
    workflowState,
    payoutAmount,
    movementScore,
    eventLogs
  } = useAppContext();

  const fade = useRef(new Animated.Value(0)).current;
  const rise = useRef(new Animated.Value(18)).current;

  const latestClaim = useMemo(() => {
    return claimsHistory.length > 0 ? claimsHistory[0] : null;
  }, [claimsHistory]);

  const animateStateTransition = () => {
    fade.setValue(0);
    rise.setValue(18);

    Animated.parallel([
      Animated.timing(fade, {
        duration: 350,
        toValue: 1,
        useNativeDriver: true
      }),
      Animated.timing(rise, {
        duration: 350,
        toValue: 0,
        useNativeDriver: true
      })
    ]).start();
  };

  useEffect(() => {
    if (workflowState !== "idle") {
      animateStateTransition();
    }
  }, [workflowState]);

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.content}>
        <FlatList
          ListHeaderComponent={
            <View>
              <Header
                subtitle="User-initiated claim checks processed step-by-step with eligibility and fraud validation"
                title="Claims"
                rightElement={<StatusBadge label="Realtime" variant="success" />}
              />

              <StatusCard
                workflowState={workflowState}
                movementScore={movementScore}
                payoutAmount={payoutAmount}
              />

              <Card style={styles.infoCard}>
                <Text style={styles.infoTitle}>Claim Processing Engine</Text>
                <Text style={styles.infoSubtext}>
                  Start a coverage check from Dashboard when high risk is detected. The system then validates conditions, eligibility, and fraud signals before finalizing payout.
                </Text>
              </Card>

              {!!latestClaim && (
                <Animated.View style={{ opacity: fade, transform: [{ translateY: rise }] }}>
                  <Card style={styles.resultCard}>
                    <Text style={styles.resultHeading}>Latest Claim Update</Text>
                    <Text style={styles.resultSubHeading}>{latestClaim.status}</Text>
                    <Text style={styles.resultAmount}>
                      {latestClaim.amount > 0
                        ? `${formatRupee(latestClaim.amount)} Credited 🎉`
                        : "Verification Pending"}
                    </Text>
                    <StatusBadge
                      label={latestClaim.status}
                      variant={latestClaim.status === "Approved" ? "success" : "warning"}
                    />
                  </Card>
                </Animated.View>
              )}

              <LogPanel logs={eventLogs} />

              <Text style={styles.historyTitle}>Claim History</Text>
            </View>
          }
          contentContainerStyle={styles.listContent}
          data={claimsHistory}
          keyExtractor={(item) => item.id}
          ListEmptyComponent={
            <Card>
              <Text style={styles.emptyTitle}>No claims yet</Text>
              <Text style={styles.emptySubtitle}>
                Use Check Coverage from Dashboard to start the real workflow.
              </Text>
            </Card>
          }
          renderItem={({ item }) => (
            <Card style={styles.historyCard}>
              <View style={styles.historyTopRow}>
                <Text style={styles.historyEvent}>{item.event}</Text>
                <StatusBadge
                  label={item.status}
                  variant={item.status === "Approved" ? "success" : "warning"}
                />
              </View>
              <Text style={styles.historyAmount}>{formatRupee(item.amount)}</Text>
              <Text style={styles.historyTime}>{item.timestamp}</Text>
            </Card>
          )}
          showsVerticalScrollIndicator={false}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: appTheme.colors.background,
    flex: 1
  },
  content: {
    flex: 1
  },
  listContent: {
    paddingHorizontal: appTheme.spacing.lg,
    paddingTop: appTheme.spacing.lg,
    paddingBottom: appTheme.spacing.xxl
  },
  infoCard: {
    marginBottom: appTheme.spacing.md
  },
  infoTitle: {
    color: appTheme.colors.primary,
    fontSize: 18,
    fontWeight: "700"
  },
  infoSubtext: {
    color: appTheme.colors.textSecondary,
    fontSize: 14,
    fontWeight: "600",
    lineHeight: 20,
    marginTop: appTheme.spacing.xs
  },
  resultCard: {
    backgroundColor: appTheme.colors.successSoft,
    borderColor: appTheme.colors.borderSoft,
    marginBottom: appTheme.spacing.md
  },
  resultHeading: {
    color: appTheme.colors.primary,
    fontSize: 22,
    fontWeight: "700"
  },
  resultSubHeading: {
    color: appTheme.colors.accent,
    fontSize: 18,
    fontWeight: "700",
    marginTop: appTheme.spacing.xs
  },
  resultAmount: {
    color: appTheme.colors.successText,
    fontSize: 30,
    fontWeight: "700",
    marginBottom: appTheme.spacing.sm,
    marginTop: appTheme.spacing.md
  },
  historyTitle: {
    color: appTheme.colors.primary,
    fontSize: 18,
    fontWeight: "700",
    marginBottom: appTheme.spacing.sm
  },
  historyCard: {
    marginBottom: appTheme.spacing.sm
  },
  emptyTitle: {
    color: appTheme.colors.primary,
    fontSize: 16,
    fontWeight: "700"
  },
  emptySubtitle: {
    color: appTheme.colors.textSecondary,
    fontSize: 13,
    fontWeight: "600",
    lineHeight: 18,
    marginTop: appTheme.spacing.xs
  },
  historyTopRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between"
  },
  historyEvent: {
    color: appTheme.colors.textPrimary,
    fontSize: 16,
    fontWeight: "700"
  },
  historyAmount: {
    color: appTheme.colors.primary,
    fontSize: 25,
    fontWeight: "700",
    marginTop: appTheme.spacing.sm
  },
  historyTime: {
    color: appTheme.colors.textSecondary,
    fontSize: 13,
    fontWeight: "600",
    marginTop: appTheme.spacing.xs
  }
});
