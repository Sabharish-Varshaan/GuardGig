import React, { useEffect, useMemo, useRef } from "react";
import { Animated, FlatList, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import Card from "../components/Card";
import ClaimItemCard from "../components/ClaimItemCard";
import Header from "../components/Header";
import LogPanel from "../components/LogPanel";
import NeonButton from "../components/NeonButton";
import StatusCard from "../components/StatusCard";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

function formatRupee(value) {
  return `₹${value}`;
}

export default function ClaimsScreen({ navigation }) {
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
          renderItem={({ item }) => <ClaimItemCard item={item} style={styles.historyCard} />}
          ListFooterComponent={
            <NeonButton
              onPress={() => navigation.navigate("Payout")}
              style={styles.payoutButton}
              title="Open Payout Center"
              variant="secondary"
            />
          }
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
    paddingHorizontal: appTheme.spacing.sm,
    paddingTop: appTheme.spacing.sm,
    paddingBottom: appTheme.spacing.xxl + 200
  },
  infoCard: {
    marginBottom: appTheme.spacing.lg
  },
  infoTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 16
  },
  infoSubtext: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 15,
    lineHeight: 22,
    marginTop: appTheme.spacing.sm
  },
  resultCard: {
    backgroundColor: appTheme.colors.successSoft,
    borderColor: appTheme.colors.borderSoft,
    marginBottom: appTheme.spacing.lg
  },
  resultHeading: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_700Bold",
    fontSize: 18
  },
  resultSubHeading: {
    color: appTheme.colors.accentPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 15,
    marginTop: appTheme.spacing.xs
  },
  resultAmount: {
    color: appTheme.colors.successText,
    fontFamily: "Orbitron_700Bold",
    fontSize: 22,
    marginBottom: appTheme.spacing.sm,
    marginTop: appTheme.spacing.sm
  },
  historyTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 18,
    marginBottom: appTheme.spacing.md,
    marginTop: appTheme.spacing.xs
  },
  historyCard: {
    marginBottom: appTheme.spacing.md
  },
  emptyTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 18
  },
  emptySubtitle: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_500Medium",
    fontSize: 14,
    lineHeight: 20,
    marginTop: appTheme.spacing.xs
  },
  payoutButton: {
    marginTop: appTheme.spacing.sm
  }
});
