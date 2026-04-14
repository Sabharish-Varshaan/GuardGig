import React, { useMemo } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";

import Button from "../components/Button";
import Card from "../components/Card";
import Header from "../components/Header";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

function formatDateTime(value) {
  if (!value) {
    return "--";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short"
  });
}

function iconForType(type) {
  const normalized = String(type || "").toLowerCase();
  if (normalized.includes("payout")) {
    return "cash";
  }
  if (normalized.includes("risk")) {
    return "warning";
  }
  return "notifications";
}

export default function NotificationsScreen() {
  const tabBarHeight = useBottomTabBarHeight();
  const {
    notifications,
    notificationsLoading,
    notificationsError,
    refreshNotifications,
    markNotificationAsRead
  } = useAppContext();

  const contentStyle = useMemo(
    () => ({
      paddingHorizontal: appTheme.spacing.sm,
      paddingTop: appTheme.spacing.sm,
      paddingBottom: tabBarHeight + 20
    }),
    [tabBarHeight]
  );

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={contentStyle} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="All payout and activity updates in one place"
          title="Notifications"
          rightElement={<StatusBadge label={`${notifications.length}`} variant="info" />}
        />

        <Card style={styles.card}>
          <View style={styles.rowBetween}>
            <Text style={styles.sectionTitle}>Recent Updates</Text>
            <Button
              onPress={() => refreshNotifications().catch(() => {})}
              title="Retry"
              variant="secondary"
            />
          </View>

          {notificationsLoading && (
            <View style={styles.loadingRow}>
              <ActivityIndicator color={appTheme.colors.accentPrimary} />
              <Text style={styles.loadingText}>Loading notifications...</Text>
            </View>
          )}

          {!!notificationsError && <Text style={styles.errorText}>{notificationsError}</Text>}

          {!notificationsLoading && notifications.length === 0 ? (
            <Text style={styles.emptyText}>No notifications yet. Payout updates will appear automatically.</Text>
          ) : (
            notifications.map((item) => (
              <Pressable
                key={String(item.id)}
                onPress={() => {
                  if (!item.read) {
                    markNotificationAsRead(item.id).catch(() => {});
                  }
                }}
                style={[styles.notificationItem, !item.read ? styles.notificationUnread : null]}
              >
                <Ionicons color={appTheme.colors.accentPrimary} name={iconForType(item.type)} size={18} />
                <View style={styles.notificationCopy}>
                  <View style={styles.rowBetween}>
                    <Text style={styles.notificationTitle}>{item.title}</Text>
                    <StatusBadge label={item.read ? "Read" : "New"} variant={item.read ? "info" : "success"} />
                  </View>
                  <Text style={styles.notificationMessage}>{item.message}</Text>
                  <Text style={styles.notificationTime}>{formatDateTime(item.createdAt)}</Text>
                </View>
              </Pressable>
            ))
          )}
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: appTheme.colors.background,
    flex: 1
  },
  card: {
    marginBottom: appTheme.spacing.md
  },
  sectionTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 18
  },
  rowBetween: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 10
  },
  loadingRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: 10,
    marginTop: appTheme.spacing.sm
  },
  loadingText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14
  },
  errorText: {
    color: appTheme.colors.dangerText,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14,
    marginTop: appTheme.spacing.sm
  },
  emptyText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 15,
    marginTop: appTheme.spacing.sm
  },
  notificationItem: {
    borderColor: appTheme.colors.borderSoft,
    borderTopWidth: 1,
    flexDirection: "row",
    gap: 10,
    marginTop: appTheme.spacing.sm,
    paddingTop: appTheme.spacing.sm
  },
  notificationUnread: {
    backgroundColor: appTheme.colors.infoSoft,
    borderRadius: appTheme.radius.soft,
    paddingHorizontal: appTheme.spacing.xs,
    paddingBottom: appTheme.spacing.xs
  },
  notificationCopy: {
    flex: 1,
    gap: 4
  },
  notificationTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 16,
    paddingRight: 10
  },
  notificationMessage: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14,
    lineHeight: 19
  },
  notificationTime: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 12
  }
});
