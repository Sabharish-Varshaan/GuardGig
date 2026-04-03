import React, { memo, useEffect, useMemo, useRef } from "react";
import { Animated, FlatList, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { SafeAreaView } from "react-native-safe-area-context";

import Card from "../components/Card";
import ClaimItemCard from "../components/ClaimItemCard";
import Header from "../components/Header";
import NeonButton from "../components/NeonButton";
import StatusCard from "../components/StatusCard";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

function formatRupee(value) {
  return `₹${value}`;
}

function capitalizeStatus(value) {
  const normalized = String(value || "pending").toLowerCase();
  return normalized[0].toUpperCase() + normalized.slice(1);
}

function ClaimsScreen({ navigation }) {
  const {
    claimsHistory,
    workflowState,
    payoutAmount,
    movementScore,
    claimsLoading,
    refreshClaims,
    dataError
  } = useAppContext();

  useFocusEffect(
    React.useCallback(() => {
      refreshClaims().catch(() => {});
      return undefined;
    }, [refreshClaims])
  );

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
                subtitle="Claims run automatically with fraud checks"
                title="Claims"
                rightElement={<StatusBadge label="Realtime" variant="success" />}
              />

              <StatusCard
                workflowState={workflowState}
                movementScore={movementScore}
                payoutAmount={payoutAmount}
              />

              {!!latestClaim && (
                <Animated.View style={{ opacity: fade, transform: [{ translateY: rise }] }}>
                  <Card style={styles.resultCard}>
                    <Text style={styles.resultHeading}>Latest Claim Update</Text>
                    <Text style={styles.resultSubHeading}>{capitalizeStatus(latestClaim.status)}</Text>
                    <Text style={styles.resultAmount}>
                      {latestClaim.amount > 0
                        ? `${formatRupee(latestClaim.amount)} Credited 🎉`
                        : latestClaim.status === "rejected"
                          ? "Conditions not met"
                          : "Verification Pending"}
                    </Text>
                    <StatusBadge
                      label={capitalizeStatus(latestClaim.status)}
                      variant={latestClaim.status === "approved" ? "success" : latestClaim.status === "rejected" ? "danger" : "warning"}
                    />
                  </Card>
                </Animated.View>
              )}

              <Text style={styles.historyTitle}>Claim History</Text>
              {claimsLoading && <Text style={styles.loadingText}>Refreshing claims...</Text>}
              {!!dataError && <Text style={styles.errorText}>{dataError}</Text>}
            </View>
          }
          contentContainerStyle={styles.listContent}
          data={claimsHistory}
          keyExtractor={(item) => item.id}
          ListEmptyComponent={
            <Card>
              <Text style={styles.emptyTitle}>No claims yet</Text>
              <Text style={styles.emptySubtitle}>
                Claims appear automatically after trigger checks.
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

export default memo(ClaimsScreen);

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
    paddingBottom: 120
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
    marginBottom: appTheme.spacing.sm,
    marginTop: appTheme.spacing.sm
  },
  loadingText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    marginBottom: appTheme.spacing.sm
  },
  errorText: {
    color: appTheme.colors.danger,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    marginBottom: appTheme.spacing.sm
  }
});
