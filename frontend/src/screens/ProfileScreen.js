import React, { memo, useCallback, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import Button from "../components/Button";
import Card from "../components/Card";
import Header from "../components/Header";
import InputField from "../components/InputField";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

function ProfileRow({ label, value }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

function ProfileScreen({ navigation }) {
  const { user, updateProfile, logout } = useAppContext();
  const [editing, setEditing] = useState(false);
  const [savedBanner, setSavedBanner] = useState(false);
  const [draft, setDraft] = useState({
    fullName: user.fullName,
    phone: user.phone,
    city: user.city
  });

  const updateDraftField = useCallback((key, value) => {
    setDraft((prev) => ({ ...prev, [key]: value }));
  }, []);

  const handleNameChange = useCallback((value) => updateDraftField("fullName", value), [updateDraftField]);
  const handlePhoneChange = useCallback((value) => updateDraftField("phone", value), [updateDraftField]);
  const handleCityChange = useCallback((value) => updateDraftField("city", value), [updateDraftField]);

  const handleSave = () => {
    updateProfile(draft);
    setSavedBanner(true);
    setEditing(false);

    setTimeout(() => {
      setSavedBanner(false);
    }, appTheme.motion.duration.slow + 900);
  };

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="Manage your worker profile and account preferences"
          title="Profile"
          rightElement={<StatusBadge label={user.riskPreference || "Medium"} variant="info" />}
        />

        <Card style={styles.cardGap}>
          {savedBanner && (
            <View style={styles.savedBanner}>
              <Text style={styles.savedBannerText}>Profile updated successfully</Text>
            </View>
          )}
          {!editing ? (
            <View>
              <ProfileRow label="Name" value={user.fullName} />
              <ProfileRow label="Phone" value={user.phone} />
              <ProfileRow label="Age" value={user.age} />
              <ProfileRow label="City" value={user.city} />
              <ProfileRow label="Platform" value={user.platform} />
              <ProfileRow label="Vehicle" value={user.vehicleType} />
              <ProfileRow label="Work Hours" value={user.workHours} />
              <ProfileRow label="Daily Income" value={user.dailyIncome} />
              <ProfileRow label="Weekly Income" value={user.weeklyIncome} />
              <ProfileRow label="Risk Preference" value={user.riskPreference} />
            </View>
          ) : (
            <View>
              <InputField
                label="Name"
                onChangeText={handleNameChange}
                value={draft.fullName}
              />
              <InputField
                keyboardType="phone-pad"
                label="Phone"
                onChangeText={handlePhoneChange}
                value={draft.phone}
              />
              <InputField
                label="City"
                onChangeText={handleCityChange}
                value={draft.city}
              />
            </View>
          )}

          <Button
            onPress={editing ? handleSave : () => setEditing(true)}
            style={styles.buttonSpacing}
            title={editing ? "Save Profile" : "Edit Profile"}
          />
          {editing && (
            <Button
              onPress={() => {
                setDraft({
                  fullName: user.fullName,
                  phone: user.phone,
                  city: user.city
                });
                setEditing(false);
              }}
              style={styles.buttonSpacing}
              title="Cancel"
              variant="secondary"
            />
          )}
        </Card>

        <Card style={styles.cardGap}>
          <Button
            onPress={() => navigation.navigate("Settings")}
            style={styles.buttonSpacing}
            title="Open Settings"
            variant="secondary"
          />
          <Button onPress={logout} title="Logout" variant="ghost" />
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
}

export default memo(ProfileScreen);

const styles = StyleSheet.create({
  screen: {
    backgroundColor: appTheme.colors.background,
    flex: 1
  },
  content: {
    paddingHorizontal: appTheme.spacing.lg,
    paddingTop: appTheme.spacing.lg,
    paddingBottom: appTheme.spacing.xxl
  },
  cardGap: {
    marginBottom: appTheme.spacing.md
  },
  infoRow: {
    borderBottomColor: appTheme.colors.border,
    borderBottomWidth: 1,
    marginBottom: appTheme.spacing.sm,
    paddingBottom: appTheme.spacing.sm
  },
  infoLabel: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 13
  },
  infoValue: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 18,
    marginTop: 2
  },
  savedBanner: {
    backgroundColor: appTheme.colors.successSoft,
    borderColor: appTheme.colors.successBorder,
    borderRadius: appTheme.radius.soft,
    borderWidth: 1,
    marginBottom: appTheme.spacing.sm,
    paddingHorizontal: appTheme.spacing.xs,
    paddingVertical: appTheme.spacing.xs
  },
  savedBannerText: {
    color: appTheme.colors.successText,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14
  },
  buttonSpacing: {
    marginBottom: appTheme.spacing.sm
  }
});
