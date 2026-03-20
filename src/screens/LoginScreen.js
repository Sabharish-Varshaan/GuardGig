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

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const phonePattern = /^[0-9]{10}$/;

function validateIdentifier(value) {
  const text = value.trim();

  if (!text) {
    return "Email or phone number is required.";
  }

  if (!emailPattern.test(text) && !phonePattern.test(text)) {
    return "Enter a valid 10-digit phone or email.";
  }

  return "";
}

export default function LoginScreen({ navigation }) {
  const { login } = useAppContext();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleLogin = () => {
    const nextErrors = {
      identifier: validateIdentifier(identifier),
      password:
        password.trim().length < 6 ? "Password must be at least 6 characters." : ""
    };

    setErrors(nextErrors);

    if (nextErrors.identifier || nextErrors.password) {
      return;
    }

    setLoading(true);

    setTimeout(() => {
      login({
        identifier: identifier.trim(),
        password
      });
      setLoading(false);
    }, 450);
  };

  return (
    <SafeAreaView style={styles.screen}>
      <LinearGradient colors={["#0B3C5D", "#1D628F", "#F4F6F8"]} locations={[0, 0.42, 1]} style={styles.gradient}>
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
                error={errors.identifier}
                keyboardType="email-address"
                label="Phone number or Email"
                onChangeText={setIdentifier}
                placeholder="9876543210 or user@email.com"
                value={identifier}
              />

              <InputField
                error={errors.password}
                label="Password"
                onChangeText={setPassword}
                placeholder="Enter your password"
                secureTextEntry
                value={password}
              />

              <Button loading={loading} onPress={handleLogin} style={styles.primaryAction} title="Login" />
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
    borderWidth: 0,
    paddingTop: appTheme.spacing.xl
  },
  title: {
    color: appTheme.colors.primary,
    fontSize: 34,
    fontWeight: "700"
  },
  subtitle: {
    color: appTheme.colors.textPrimary,
    fontSize: 15,
    fontWeight: "700",
    marginTop: appTheme.spacing.xs
  },
  helperText: {
    color: appTheme.colors.textSecondary,
    fontSize: 13,
    fontWeight: "600",
    lineHeight: 18,
    marginBottom: appTheme.spacing.lg,
    marginTop: appTheme.spacing.sm
  },
  primaryAction: {
    marginTop: appTheme.spacing.sm
  },
  secondaryAction: {
    marginTop: appTheme.spacing.sm
  }
});
