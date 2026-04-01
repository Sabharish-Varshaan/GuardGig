import React, { useState } from "react";
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

export default function ProfileScreen({ navigation }) {
  const { user, updateProfile, logout } = useAppContext();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({
    fullName: user.fullName,
    phone: user.phone,
    city: user.city
  });

  const handleSave = () => {
    updateProfile(draft);
    setEditing(false);
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
                onChangeText={(value) => setDraft((prev) => ({ ...prev, fullName: value }))}
                value={draft.fullName}
              />
              <InputField
                keyboardType="phone-pad"
                label="Phone"
                onChangeText={(value) => setDraft((prev) => ({ ...prev, phone: value }))}
                value={draft.phone}
              />
              <InputField
                label="City"
                onChangeText={(value) => setDraft((prev) => ({ ...prev, city: value }))}
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
    fontSize: 13,
    fontWeight: "600"
  },
  infoValue: {
    color: appTheme.colors.primary,
    fontSize: 17,
    fontWeight: "700",
    marginTop: 2
  },
  buttonSpacing: {
    marginBottom: appTheme.spacing.sm
  }
});
