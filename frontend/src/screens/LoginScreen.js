import React, { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  View
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";

import Button from "../components/Button";
import Card from "../components/Card";
import InputField from "../components/InputField";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

const phonePattern = /^[0-9]{10}$/;

function validatePhone(value) {
  const text = value.trim();

  if (!text) {
    return "Phone number is required.";
  }

  if (!phonePattern.test(text)) {
    return "Enter a valid 10-digit phone number.";
  }

  return "";
}

export default function LoginScreen({ navigation }) {
  const {
    login,
    authLoading,
    authError,
    setAuthError,
    pendingOnboardingUser
  } = useAppContext();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});

  const handleLogin = async () => {
    const nextErrors = {
      phone: validatePhone(phone),
      password:
        password.trim().length < 6 ? "Password must be at least 6 characters." : ""
    };

    setErrors(nextErrors);

    if (nextErrors.phone || nextErrors.password) {
      return;
    }

    setAuthError("");

    const result = await login({
      phone: phone.trim(),
      password
    });

    if (!result.success) {
      return;
    }

    if (!result.onboardingCompleted) {
      navigation.navigate("Onboarding", {
        fullName: pendingOnboardingUser?.fullName || "",
        phone: phone.trim()
      });
    }
  };

  return (
    <SafeAreaView style={styles.screen}>
      <LinearGradient
        colors={[appTheme.colors.gradientA, appTheme.colors.gradientB, appTheme.colors.gradientC]}
        locations={[0, 0.45, 1]}
        style={styles.gradient}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === "ios" ? "padding" : undefined}
          style={styles.flex}
        >
          <View style={styles.centeredContent}>
            <Card style={styles.authCard}>
              <Text style={styles.title}>GigShield AI</Text>
              <Text style={styles.subtitle}>Income Protection for Delivery Workers</Text>
              <Text style={styles.helperText}>Welcome back. Sign in to view your policy and risk dashboard.</Text>

              <InputField
                error={errors.phone}
                keyboardType="phone-pad"
                label="Phone number"
                onChangeText={setPhone}
                placeholder="9876543210"
                value={phone}
              />

              <InputField
                error={errors.password}
                label="Password"
                onChangeText={setPassword}
                placeholder="Enter your password"
                secureTextEntry
                value={password}
              />

              {!!authError && <Text style={styles.errorText}>{authError}</Text>}

              <Button loading={authLoading} onPress={handleLogin} style={styles.primaryAction} title="Login" />
              <Button
                onPress={() => navigation.navigate("Register")}
                style={styles.secondaryAction}
                title="New user? Register"
                variant="ghost"
              />
            </Card>
          </View>
        </KeyboardAvoidingView>
      </LinearGradient>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: appTheme.colors.background,
    flex: 1
  },
  gradient: {
    flex: 1
  },
  flex: {
    flex: 1
  },
  centeredContent: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: appTheme.spacing.lg
  },
  authCard: {
    backgroundColor: appTheme.colors.cardGlass,
    borderColor: appTheme.colors.cardGlassBorder,
    borderWidth: 1,
    paddingTop: appTheme.spacing.xl,
    ...appTheme.shadows.floating
  },
  title: {
    color: appTheme.colors.primary,
    fontSize: 36,
    letterSpacing: -0.6,
    fontWeight: "700"
  },
  subtitle: {
    color: appTheme.colors.textPrimary,
    fontSize: 14,
    letterSpacing: 0.2,
    fontWeight: "700",
    marginTop: appTheme.spacing.xs
  },
  helperText: {
    color: appTheme.colors.textSecondary,
    fontSize: 14,
    fontWeight: "500",
    lineHeight: 20,
    marginBottom: appTheme.spacing.lg,
    marginTop: appTheme.spacing.sm
  },
  primaryAction: {
    marginTop: appTheme.spacing.sm
  },
  errorText: {
    color: appTheme.colors.danger,
    fontSize: 13,
    fontWeight: "600",
    marginBottom: appTheme.spacing.xs
  },
  secondaryAction: {
    marginTop: appTheme.spacing.sm
  }
});
