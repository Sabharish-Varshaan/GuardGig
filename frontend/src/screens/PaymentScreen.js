import React, { useMemo, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { WebView } from "react-native-webview";

import Button from "../components/Button";
import { useAppContext } from "../context/AppContext";
import { verifyPayment } from "../services/insuranceApi";
import { appTheme } from "../styles/theme";

export default function PaymentScreen({ navigation, route }) {
  const { authToken, refreshPolicy } = useAppContext();
  const checkoutUrl = route?.params?.checkoutUrl || "";
  const orderId = route?.params?.orderId || "";
  const amountPaise = Number(route?.params?.amount || 0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentError, setPaymentError] = useState("");
  const [statusMessage, setStatusMessage] = useState("Opening Razorpay...");

  const amountRupees = useMemo(() => (amountPaise > 0 ? (amountPaise / 100).toFixed(2) : "0.00"), [amountPaise]);

  const onWebMessage = async (event) => {
    let payload;
    try {
      payload = JSON.parse(event?.nativeEvent?.data || "{}");
    } catch (_error) {
      return;
    }

    if (payload?.type === "payment_failed") {
      setStatusMessage("Payment failed");
      setPaymentError(payload.reason || "Payment failed");
      return;
    }

    if (payload?.type !== "payment_success") {
      return;
    }

    if (!authToken) {
      setPaymentError("Session expired. Please login again.");
      return;
    }

    setIsProcessing(true);
    setPaymentError("");
    setStatusMessage("Verifying payment...");

    try {
      const receivedOrderId = payload.order_id || orderId;
      const paymentId = payload.payment_id || `${receivedOrderId}_simulated`;

      await verifyPayment(authToken, {
        orderId: receivedOrderId,
        paymentId
      });

      await refreshPolicy(authToken);
      setStatusMessage("Payment successful");
      navigation.navigate("MainTabs", { screen: "Home" });
    } catch (error) {
      setPaymentError(error instanceof Error ? error.message : "Payment verification failed");
      setStatusMessage("Verification failed");
    } finally {
      setIsProcessing(false);
    }
  };

  if (!orderId || !checkoutUrl) {
    return (
      <SafeAreaView style={styles.screen}>
        <View style={styles.centered}>
          <Text style={styles.title}>Unable to start payment</Text>
          <Text style={styles.meta}>Order details are missing. Please return and retry.</Text>
          <Button onPress={() => navigation.goBack()} style={styles.actionButton} title="Back" />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.centered}>
        <Text style={styles.title}>Complete Payment</Text>
        <Text style={styles.meta}>{`Order: ${orderId}`}</Text>
        <Text style={styles.amount}>{`Amount: ₹${amountRupees}`}</Text>
        <Text style={styles.meta}>{statusMessage}</Text>

        <View style={styles.webViewWrap}>
          <WebView
            source={{ uri: checkoutUrl }}
            javaScriptEnabled
            domStorageEnabled
            startInLoadingState
            onMessage={onWebMessage}
            renderLoading={() => (
              <View style={styles.loaderWrap}>
                <ActivityIndicator color={appTheme.colors.accentPrimary} size="large" />
                <Text style={styles.meta}>Loading Razorpay UI...</Text>
              </View>
            )}
          />
        </View>

        {isProcessing && (
          <View style={styles.loaderWrap}>
            <ActivityIndicator color={appTheme.colors.accentPrimary} size="small" />
            <Text style={styles.meta}>Finalizing payment...</Text>
          </View>
        )}

        {!!paymentError && <Text style={styles.errorText}>{paymentError}</Text>}
        <Button onPress={() => navigation.goBack()} style={styles.secondaryButton} title="Cancel" />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: appTheme.colors.background
  },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: appTheme.spacing.lg
  },
  loaderWrap: {
    alignItems: "center",
    justifyContent: "center",
    gap: appTheme.spacing.sm,
    marginTop: appTheme.spacing.md
  },
  webViewWrap: {
    height: 380,
    width: "100%",
    marginTop: appTheme.spacing.md,
    borderRadius: 12,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: appTheme.colors.borderSubtle,
    backgroundColor: appTheme.colors.bgCard
  },
  title: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 18
  },
  meta: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    marginTop: 4
  },
  amount: {
    color: appTheme.colors.accentPrimary,
    fontFamily: "Orbitron_700Bold",
    fontSize: 24,
    marginTop: appTheme.spacing.sm
  },
  secondaryButton: {
    marginTop: appTheme.spacing.sm,
    minWidth: 140
  },
  errorText: {
    color: appTheme.colors.danger,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    marginTop: appTheme.spacing.sm,
    textAlign: "center"
  }
});
