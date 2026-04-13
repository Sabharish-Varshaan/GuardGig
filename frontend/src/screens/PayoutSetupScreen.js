import React, { memo, useEffect, useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import Button from "../components/Button";
import Card from "../components/Card";
import Header from "../components/Header";
import InputField from "../components/InputField";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

function PayoutSetupScreen() {
  const insets = useSafeAreaInsets();
  const { payoutDetails, savePayoutDetails, payoutDetailsLoading } = useAppContext();
  const [form, setForm] = useState({
    accountHolderName: payoutDetails?.accountHolderName || "",
    bankAccountNumber: "",
    ifscCode: payoutDetails?.ifscCode || "",
    upiId: payoutDetails?.upiId || ""
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!payoutDetails) {
      return;
    }

    setForm((prev) => ({
      ...prev,
      accountHolderName: payoutDetails.accountHolderName || prev.accountHolderName,
      ifscCode: payoutDetails.ifscCode || prev.ifscCode,
      upiId: payoutDetails.upiId || prev.upiId,
    }));
  }, [payoutDetails]);

  const contentStyle = useMemo(
    () => ({
      paddingHorizontal: appTheme.spacing.sm,
      paddingTop: appTheme.spacing.md,
      paddingBottom: insets.bottom + appTheme.spacing.lg
    }),
    [insets.bottom]
  );

  const updateField = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async () => {
    setSaving(true);
    setError("");
    setMessage("");

    try {
      await savePayoutDetails({
        accountHolderName: form.accountHolderName,
        bankAccountNumber: form.bankAccountNumber,
        ifscCode: form.ifscCode,
        upiId: form.upiId
      });

      setMessage("Payout details saved successfully.");
      setForm((prev) => ({
        ...prev,
        bankAccountNumber: ""
      }));
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save payout details");
    } finally {
      setSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={contentStyle} showsVerticalScrollIndicator={false}>
        <Header
          title="Payout Setup"
          subtitle="Add bank or UPI destination for automated compensation"
          rightElement={<StatusBadge label={payoutDetails?.hasPayoutMethod ? "Configured" : "Required"} variant={payoutDetails?.hasPayoutMethod ? "success" : "warning"} />}
        />

        <Card>
          <Text style={styles.sectionTitle}>Recipient Details</Text>
          <InputField
            label="Name"
            value={form.accountHolderName}
            onChangeText={(value) => updateField("accountHolderName", value)}
            placeholder="Account holder full name"
            autoCapitalize="words"
          />
          <InputField
            label="Bank Account"
            value={form.bankAccountNumber}
            onChangeText={(value) => updateField("bankAccountNumber", value)}
            placeholder="Optional if UPI is provided"
            keyboardType="number-pad"
          />
          <InputField
            label="IFSC"
            value={form.ifscCode}
            onChangeText={(value) => updateField("ifscCode", value.toUpperCase())}
            placeholder="Example: HDFC0001234"
            autoCapitalize="characters"
          />

          <View style={styles.orWrap}>
            <Text style={styles.orText}>OR</Text>
          </View>

          <InputField
            label="UPI ID"
            value={form.upiId}
            onChangeText={(value) => updateField("upiId", value)}
            placeholder="example@upi"
            autoCapitalize="none"
          />

          {!!payoutDetails?.bankAccountMasked && (
            <Text style={styles.metaText}>Current bank destination: {payoutDetails.bankAccountMasked}</Text>
          )}
          {!!payoutDetails?.upiId && <Text style={styles.metaText}>Current UPI destination: {payoutDetails.upiId}</Text>}

          {!!error && <Text style={styles.errorText}>{error}</Text>}
          {!!message && <Text style={styles.successText}>{message}</Text>}

          <Button title={saving ? "Saving..." : "Save Payout Details"} onPress={handleSubmit} disabled={saving || payoutDetailsLoading} />
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
}

export default memo(PayoutSetupScreen);

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: appTheme.colors.background
  },
  sectionTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 18,
    marginBottom: appTheme.spacing.sm
  },
  orWrap: {
    alignItems: "center",
    marginTop: appTheme.spacing.xs,
    marginBottom: appTheme.spacing.sm
  },
  orText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14,
    letterSpacing: 1
  },
  metaText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 13,
    marginBottom: appTheme.spacing.xs
  },
  errorText: {
    color: appTheme.colors.dangerText,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14,
    marginBottom: appTheme.spacing.sm
  },
  successText: {
    color: appTheme.colors.successText,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14,
    marginBottom: appTheme.spacing.sm
  }
});
