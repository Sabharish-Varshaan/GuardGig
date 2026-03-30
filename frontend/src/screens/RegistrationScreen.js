import React, { useState } from "react";
import { KeyboardAvoidingView, Platform, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import Button from "../components/Button";
import Card from "../components/Card";
import Header from "../components/Header";
import InputField from "../components/InputField";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

const phonePattern = /^[0-9]{10}$/;

export default function RegistrationScreen({ navigation }) {
  const { register, authLoading, authError, setAuthError } = useAppContext();
  const [form, setForm] = useState({
    fullName: "",
    phone: "",
    password: ""
  });
  const [errors, setErrors] = useState({});

  const updateField = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleRegister = async () => {
    const nextErrors = {
      fullName: form.fullName.trim() ? "" : "Full name is required.",
      phone: phonePattern.test(form.phone.trim()) ? "" : "Enter a valid 10-digit phone number.",
      password:
        form.password.trim().length >= 6 ? "" : "Password must be at least 6 characters."
    };

    setErrors(nextErrors);

    if (nextErrors.fullName || nextErrors.phone || nextErrors.password) {
      return;
    }

    setAuthError("");
    const result = await register(form);
    if (!result.success) {
      return;
    }

    navigation.navigate("Onboarding", {
      fullName: form.fullName.trim(),
      phone: form.phone.trim()
    });
  };

  return (
    <SafeAreaView style={styles.screen}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={styles.flex}>
        <View style={styles.content}>
          <Header
            subtitle="Create your secure worker account to generate a personalized plan"
            title="Register"
          />

          <Card>
            <InputField
              error={errors.fullName}
              label="Full Name"
              onChangeText={(value) => updateField("fullName", value)}
              placeholder="Enter your full name"
              value={form.fullName}
            />
            <InputField
              error={errors.phone}
              keyboardType="phone-pad"
              label="Phone"
              onChangeText={(value) => updateField("phone", value)}
              placeholder="10-digit mobile number"
              value={form.phone}
            />
            <InputField
              error={errors.password}
              label="Password"
              onChangeText={(value) => updateField("password", value)}
              placeholder="Create password"
              secureTextEntry
              value={form.password}
            />
            {!!authError && <Text style={styles.errorText}>{authError}</Text>}
            <Button loading={authLoading} onPress={handleRegister} style={styles.primaryCta} title="Register" />
            <Button
              onPress={() => navigation.goBack()}
              style={styles.secondaryCta}
              title="Already registered? Login"
              variant="ghost"
            />
          </Card>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: appTheme.colors.background,
    flex: 1
  },
  flex: {
    flex: 1
  },
  content: {
    flex: 1,
    paddingHorizontal: appTheme.spacing.lg,
    paddingTop: appTheme.spacing.lg
  },
  primaryCta: {
    marginTop: appTheme.spacing.sm
  },
  errorText: {
    color: appTheme.colors.danger,
    fontSize: 13,
    fontWeight: "600",
    marginBottom: appTheme.spacing.xs
  },
  secondaryCta: {
    marginTop: appTheme.spacing.xs
  }
});
