import React, { memo, useCallback, useMemo, useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import Button from "../components/Button";
import Card from "../components/Card";
import Header from "../components/Header";
import InputField from "../components/InputField";
import ProgressBar from "../components/ProgressBar";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

const cities = ["Chennai", "Bengaluru", "Hyderabad", "Mumbai"];
const platforms = ["Blinkit", "Zepto", "Swiggy"];
const vehicles = ["Bike", "Scooter", "Cycle"];
const riskLevels = ["Low", "Medium", "High"];

function Chip({ label, selected, onPress }) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.chip, selected ? styles.chipSelected : null, pressed ? styles.chipPressed : null]}
    >
      <Text style={[styles.chipLabel, selected ? styles.chipLabelSelected : null]}>{label}</Text>
    </Pressable>
  );
}

function OnboardingScreen({ navigation, route }) {
  const {
    completeOnboarding,
    authLoading,
    authError,
    pendingOnboardingUser,
    setAuthError
  } = useAppContext();
  const [step, setStep] = useState(0);
  const [showCityDropdown, setShowCityDropdown] = useState(false);
  const [errors, setErrors] = useState({});
  const [form, setForm] = useState({
    fullName: route.params?.fullName || pendingOnboardingUser?.fullName || "",
    age: "",
    city: "",
    platform: "",
    vehicleType: "",
    workHours: "",
    minIncome: "",
    maxIncome: "",
    riskPreference: "Medium"
  });

  const stepProgress = useMemo(() => ((step + 1) / 4) * 100, [step]);

  const updateField = useCallback((key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  }, []);

  const handleFullNameChange = useCallback((value) => updateField("fullName", value), [updateField]);
  const handleAgeChange = useCallback((value) => updateField("age", value), [updateField]);
  const handleWorkHoursChange = useCallback((value) => updateField("workHours", value), [updateField]);
  const handleMinIncomeChange = useCallback((value) => updateField("minIncome", value), [updateField]);
  const handleMaxIncomeChange = useCallback((value) => updateField("maxIncome", value), [updateField]);

  const validateStep = () => {
    let nextErrors = {};

    if (step === 0) {
      nextErrors = {
        fullName: form.fullName.trim() ? "" : "Name is required.",
        age:
          Number(form.age) >= 18 && Number(form.age) <= 70
            ? ""
            : "Age must be between 18 and 70.",
        city: form.city ? "" : "Select a city."
      };
    }

    if (step === 1) {
      nextErrors = {
        platform: form.platform ? "" : "Select a platform.",
        vehicleType: form.vehicleType ? "" : "Select vehicle type.",
        workHours:
          Number(form.workHours) > 0 ? "" : "Enter work hours per day."
      };
    }

    if (step === 2) {
      const minIncome = Number(form.minIncome);
      const maxIncome = Number(form.maxIncome);

      nextErrors = {
        minIncome: minIncome > 0 ? "" : "Minimum income must be greater than zero.",
        maxIncome: maxIncome > minIncome ? "" : "Max must be greater than min"
      };
    }

    if (step === 3) {
      nextErrors = {
        riskPreference: form.riskPreference ? "" : "Select a risk preference."
      };
    }

    setErrors(nextErrors);

    return !Object.values(nextErrors).some(Boolean);
  };

  const nextStep = () => {
    if (!validateStep()) {
      return;
    }

    setStep((prev) => Math.min(3, prev + 1));
  };

  const prevStep = () => {
    setStep((prev) => Math.max(0, prev - 1));
  };

  const handleGenerate = async () => {
    if (!validateStep()) {
      return;
    }

    setAuthError("");
    const result = await completeOnboarding(form);
    if (!result.success) {
      return;
    }
  };

  return (
    <SafeAreaView style={styles.screen}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.flex}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardDismissMode="none"
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <Header
            subtitle="Complete your 4-step profile to generate your personalized insurance plan"
            title="Onboarding"
            rightElement={<StatusBadge label={`Step ${step + 1}/4`} variant="info" />}
          />

          <Card style={styles.progressCard}>
            <ProgressBar
              color={appTheme.colors.accent}
              label="Profile Completion"
              progress={stepProgress}
              rightLabel={`${Math.round(stepProgress)}%`}
              value={Math.round(stepProgress)}
            />
          </Card>

          <Card>
            {step === 0 && (
              <View>
                <Text style={styles.sectionTitle}>Step 1: Personal Info</Text>
                <InputField
                  error={errors.fullName}
                  label="Name"
                  onChangeText={handleFullNameChange}
                  placeholder="Full name"
                  value={form.fullName}
                />
                <InputField
                  error={errors.age}
                  keyboardType="number-pad"
                  label="Age"
                  onChangeText={handleAgeChange}
                  placeholder="Age"
                  value={form.age}
                />
                <Text style={styles.selectLabel}>City (Dropdown)</Text>
                <View style={styles.dropdownWrap}>
                  <Pressable
                    onPress={() => setShowCityDropdown((prev) => !prev)}
                    style={({ pressed }) => [styles.dropdownTrigger, pressed ? styles.chipPressed : null]}
                  >
                    <Text style={styles.dropdownText}>{form.city || "Select city"}</Text>
                    <Text style={styles.dropdownArrow}>▼</Text>
                  </Pressable>
                  {showCityDropdown && (
                    <View style={styles.dropdownPanel}>
                      {cities.map((city) => (
                        <Pressable
                          key={city}
                          onPress={() => {
                            updateField("city", city);
                            setShowCityDropdown(false);
                          }}
                          style={styles.dropdownOption}
                        >
                          <Text style={styles.dropdownOptionText}>{city}</Text>
                        </Pressable>
                      ))}
                    </View>
                  )}
                </View>
                {!!errors.city && <Text style={styles.errorText}>{errors.city}</Text>}
              </View>
            )}

            {step === 1 && (
              <View>
                <Text style={styles.sectionTitle}>Step 2: Work Info</Text>
                <Text style={styles.selectLabel}>Platform</Text>
                <View style={styles.chipRow}>
                  {platforms.map((item) => (
                    <Chip
                      key={item}
                      label={item}
                      onPress={() => updateField("platform", item)}
                      selected={form.platform === item}
                    />
                  ))}
                </View>
                {!!errors.platform && <Text style={styles.errorText}>{errors.platform}</Text>}

                <Text style={styles.selectLabel}>Vehicle Type</Text>
                <View style={styles.chipRow}>
                  {vehicles.map((item) => (
                    <Chip
                      key={item}
                      label={item}
                      onPress={() => updateField("vehicleType", item)}
                      selected={form.vehicleType === item}
                    />
                  ))}
                </View>
                {!!errors.vehicleType && <Text style={styles.errorText}>{errors.vehicleType}</Text>}

                <InputField
                  error={errors.workHours}
                  keyboardType="number-pad"
                  label="Work hours/day"
                  onChangeText={handleWorkHoursChange}
                  placeholder="Hours per day"
                  value={form.workHours}
                />
              </View>
            )}

            {step === 2 && (
              <View>
                <Text style={styles.sectionTitle}>Step 3: Income Info</Text>
                <Text style={styles.helperHint}>Your income varies daily. Enter a realistic range.</Text>
                <InputField
                  error={errors.minIncome}
                  keyboardType="number-pad"
                  label="Minimum Daily Income"
                  onChangeText={handleMinIncomeChange}
                  placeholder="Minimum daily income in INR"
                  value={form.minIncome}
                />
                <InputField
                  error={errors.maxIncome}
                  keyboardType="number-pad"
                  label="Maximum Daily Income"
                  onChangeText={handleMaxIncomeChange}
                  placeholder="Maximum daily income in INR"
                  value={form.maxIncome}
                />
              </View>
            )}

            {step === 3 && (
              <View>
                <Text style={styles.sectionTitle}>Step 4: Risk Preference</Text>
                <Text style={styles.selectLabel}>Choose Coverage Preference</Text>
                <View style={styles.chipRow}>
                  {riskLevels.map((item) => (
                    <Chip
                      key={item}
                      label={item}
                      onPress={() => updateField("riskPreference", item)}
                      selected={form.riskPreference === item}
                    />
                  ))}
                </View>
                {!!errors.riskPreference && (
                  <Text style={styles.errorText}>{errors.riskPreference}</Text>
                )}
              </View>
            )}

            <View style={styles.actionRow}>
              {step > 0 ? (
                <Button
                  onPress={prevStep}
                  style={styles.backButton}
                  title="Back"
                  variant="secondary"
                />
              ) : (
                <View style={styles.backButton} />
              )}

              {step < 3 ? (
                <Button onPress={nextStep} style={styles.nextButton} title="Next" />
              ) : (
                <Button
                  disabled={authLoading}
                  loading={authLoading}
                  onPress={handleGenerate}
                  style={styles.nextButton}
                  title="Generate Plan"
                />
              )}
            </View>
            {!!authError && <Text style={styles.submitError}>{authError}</Text>}
          </Card>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

export default memo(OnboardingScreen);

const styles = StyleSheet.create({
  screen: {
    backgroundColor: appTheme.colors.background,
    flex: 1
  },
  flex: {
    flex: 1
  },
  scrollContent: {
    paddingHorizontal: appTheme.spacing.lg,
    paddingTop: appTheme.spacing.lg,
    paddingBottom: 150
  },
  progressCard: {
    marginBottom: appTheme.spacing.md,
    paddingVertical: appTheme.spacing.md
  },
  sectionTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 20,
    marginBottom: appTheme.spacing.md
  },
  helperHint: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    marginBottom: appTheme.spacing.sm
  },
  selectLabel: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14,
    marginBottom: appTheme.spacing.xs
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginBottom: appTheme.spacing.sm
  },
  chip: {
    backgroundColor: appTheme.colors.chipBg,
    borderRadius: appTheme.radius.pill,
    borderColor: appTheme.colors.chipBorder,
    borderWidth: 1,
    marginBottom: appTheme.spacing.sm,
    marginRight: appTheme.spacing.sm,
    paddingHorizontal: appTheme.spacing.md,
    paddingVertical: 9
  },
  chipSelected: {
    backgroundColor: appTheme.colors.primary,
    borderColor: appTheme.colors.primary
  },
  chipLabel: {
    color: appTheme.colors.accentPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 12,
    letterSpacing: 0.2
  },
  chipLabelSelected: {
    color: appTheme.colors.bgPrimary
  },
  chipPressed: {
    opacity: 0.85
  },
  dropdownTrigger: {
    alignItems: "center",
    backgroundColor: appTheme.colors.surface,
    borderColor: appTheme.colors.border,
    borderRadius: appTheme.radius.input,
    borderWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    minHeight: 56,
    paddingHorizontal: appTheme.spacing.md
  },
  dropdownWrap: {
    position: "relative",
    zIndex: 20
  },
  dropdownText: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 16
  },
  dropdownArrow: {
    color: appTheme.colors.primary,
    fontSize: 12,
    fontWeight: "700"
  },
  dropdownPanel: {
    backgroundColor: appTheme.colors.surface,
    borderColor: appTheme.colors.border,
    borderRadius: appTheme.radius.input,
    borderWidth: 1,
    left: 0,
    marginTop: appTheme.spacing.xs,
    maxHeight: 220,
    position: "absolute",
    right: 0,
    top: 56,
    zIndex: 30,
    overflow: "hidden"
  },
  dropdownOption: {
    paddingHorizontal: appTheme.spacing.md,
    paddingVertical: appTheme.spacing.sm
  },
  dropdownOptionText: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 15
  },
  errorText: {
    color: appTheme.colors.danger,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 12,
    marginBottom: appTheme.spacing.sm,
    marginTop: 2
  },
  actionRow: {
    flexDirection: "row",
    marginTop: appTheme.spacing.lg
  },
  submitError: {
    color: appTheme.colors.danger,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 13,
    marginTop: appTheme.spacing.sm
  },
  backButton: {
    flex: 1,
    marginRight: appTheme.spacing.sm
  },
  nextButton: {
    flex: 1
  }
});
