import React from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";

import { appTheme } from "../styles/theme";

export default function InputField({
  label,
  value,
  onChangeText,
  placeholder,
  keyboardType = "default",
  secureTextEntry = false,
  error,
  editable = true,
  rightElement,
  multiline = false
}) {
  return (
    <View style={styles.wrapper}>
      {!!label && <Text style={styles.label}>{label}</Text>}
      <View style={[styles.inputShell, error ? styles.inputShellError : null, !editable ? styles.inputDisabled : null]}>
        <TextInput
          editable={editable}
          keyboardType={keyboardType}
          multiline={multiline}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={appTheme.colors.textSecondary}
          secureTextEntry={secureTextEntry}
          style={[styles.input, multiline ? styles.multilineInput : null]}
          value={value}
        />
        {!!rightElement && <View style={styles.rightElement}>{rightElement}</View>}
      </View>
      {!!error && <Text style={styles.errorText}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: appTheme.spacing.md
  },
  label: {
    color: appTheme.colors.textPrimary,
    fontSize: 12,
    letterSpacing: 0.4,
    textTransform: "uppercase",
    fontWeight: "700",
    marginBottom: appTheme.spacing.xs
  },
  inputShell: {
    alignItems: "center",
    backgroundColor: appTheme.colors.surface,
    borderColor: appTheme.colors.border,
    borderRadius: appTheme.radius.input,
    borderWidth: 1,
    flexDirection: "row",
    minHeight: 56,
    paddingHorizontal: appTheme.spacing.md
  },
  inputShellError: {
    borderColor: appTheme.colors.danger
  },
  inputDisabled: {
    backgroundColor: appTheme.colors.mutedBlue
  },
  input: {
    color: appTheme.colors.textPrimary,
    flex: 1,
    fontSize: 15,
    fontWeight: "500",
    paddingVertical: 12
  },
  multilineInput: {
    minHeight: 88,
    textAlignVertical: "top"
  },
  rightElement: {
    marginLeft: appTheme.spacing.sm
  },
  errorText: {
    color: appTheme.colors.danger,
    fontSize: 12,
    fontWeight: "600",
    marginTop: 4
  }
});
