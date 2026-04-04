import React, { memo, useCallback, useRef, useState } from "react";
import {
  Animated,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
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

function LoginScreen({ navigation }) {
  const {
    login,
    updateProfile,
    authLoading,
    authError,
    setAuthError,
    pendingOnboardingUser
  } = useAppContext();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const errorOpacity = useRef(new Animated.Value(0)).current;
  const { width } = useWindowDimensions();
  const contentWidth = width >= 1200 ? 520 : width >= 768 ? 480 : undefined;

  const handlePhoneChange = useCallback((value) => {
    setPhone(value);
  }, []);

  const handlePasswordChange = useCallback((value) => {
    setPassword(value);
  }, []);

  const handleNavigateToRegister = useCallback(() => {
    navigation.navigate("Register");
  }, [navigation]);

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

    if (!result.accessToken) {
      setAuthError("Login succeeded but token was missing.");
      return;
    }

    await AsyncStorage.setItem("token", result.accessToken);
    updateProfile({ token: result.accessToken });

    if (!result.onboardingCompleted) {
      navigation.reset({
        index: 0,
        routes: [
          {
            name: "Onboarding",
            params: {
              fullName: pendingOnboardingUser?.fullName || "",
              phone: phone.trim()
            }
          }
        ]
      });
      return;
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
          behavior={Platform.OS === "ios" ? "padding" : "height"}
          style={styles.flex}
        >
          <ScrollView
            contentContainerStyle={styles.scrollContent}
            keyboardDismissMode="none"
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >
            <View style={[styles.centeredContent, contentWidth ? { maxWidth: contentWidth } : null]}>
              <Card style={styles.authCard}>
                <Text style={styles.title}>guardgig</Text>
                <Text style={styles.subtitle}>AI Insurance for Delivery Workers</Text>
                <Text style={styles.helperText}>Welcome back. Sign in to view your policy and risk dashboard.</Text>

                <InputField
                  error={errors.phone}
                  keyboardType="phone-pad"
                  label="Phone number"
                  onChangeText={handlePhoneChange}
                  autoComplete="off"
                  placeholder="9876543210"
                  value={phone}
                />

                <InputField
                  error={errors.password}
                  label="Password"
                  onChangeText={handlePasswordChange}
                  autoComplete="off"
                  placeholder="Enter your password"
                  secureTextEntry
                  value={password}
                />

                {!!authError && (
                  <Animated.Text
                    onLayout={() => {
                      Animated.timing(errorOpacity, {
                        duration: appTheme.motion.duration.normal,
                        toValue: 1,
                        useNativeDriver: true
                      }).start();
                    }}
                    style={[styles.errorText, { opacity: errorOpacity }]}
                  >
                    {authError}
                  </Animated.Text>
                )}

                <Button loading={authLoading} onPress={handleLogin} style={styles.primaryAction} title="Login" />
                <Button
                  onPress={handleNavigateToRegister}
                  style={styles.secondaryAction}
                  title="New user? Register"
                  variant="ghost"
                />
              </Card>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </LinearGradient>
    </SafeAreaView>
  );
}

export default memo(LoginScreen);

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
  scrollContent: {
    flexGrow: 1
  },
  centeredContent: {
    alignSelf: "center",
    paddingBottom: appTheme.spacing.xxl,
    paddingTop: appTheme.spacing.xxl,
    paddingHorizontal: appTheme.spacing.lg,
    width: "100%"
  },
  authCard: {
    backgroundColor: appTheme.colors.cardGlass,
    borderColor: appTheme.colors.cardGlassBorder,
    borderWidth: 1,
    paddingTop: appTheme.spacing.xl,
    ...appTheme.shadows.floating
  },
  title: {
    color: appTheme.colors.textPrimary,
    ...appTheme.typography.display
  },
  subtitle: {
    color: appTheme.colors.accentPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 16,
    letterSpacing: 0.6,
    marginTop: appTheme.spacing.xs
  },
  helperText: {
    color: appTheme.colors.textSecondary,
    ...appTheme.typography.body,
    marginBottom: appTheme.spacing.lg,
    marginTop: appTheme.spacing.sm
  },
  primaryAction: {
    marginTop: appTheme.spacing.sm
  },
  errorText: {
    color: appTheme.colors.danger,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 13,
    marginBottom: appTheme.spacing.xs
  },
  secondaryAction: {
    marginTop: appTheme.spacing.sm
  }
});
