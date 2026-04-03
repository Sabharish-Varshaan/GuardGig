import React, { memo } from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";

import { appTheme } from "../styles/theme";

function InputField({
  label,
  value,
  onChangeText,
  placeholder,
  keyboardType = "default",
  secureTextEntry = false,
  error,
  editable = true,
  rightElement,
  multiline = false,
  autoComplete = "off",
  autoCapitalize = "none",
  blurOnSubmit = true,
  enablesReturnKeyAutomatically = true,
  onSubmitEditing,
  returnKeyType = "done",
  textContentType = "none",
  onFocus,
  onBlur
}) {
  return (
    <View style={styles.wrapper}>
      {!!label && <Text style={styles.label}>{label}</Text>}
      <View
        style={[
          styles.inputShell,
          error ? styles.inputShellError : null,
          !editable ? styles.inputDisabled : null
        ]}
      >
        <TextInput
          editable={editable}
          autoCapitalize={autoCapitalize}
          autoComplete={autoComplete}
          autoCorrect={false}
          blurOnSubmit={blurOnSubmit}
          enablesReturnKeyAutomatically={enablesReturnKeyAutomatically}
          onBlur={() => {
            onBlur?.();
          }}
          keyboardType={keyboardType}
          multiline={multiline}
          onChangeText={onChangeText}
          onFocus={() => {
            onFocus?.();
          }}
          onSubmitEditing={onSubmitEditing}
          placeholder={placeholder}
          placeholderTextColor={appTheme.colors.textSecondary}
          secureTextEntry={secureTextEntry}
          returnKeyType={returnKeyType}
          spellCheck={false}
          textContentType={textContentType}
          importantForAutofill="no"
          style={[styles.input, multiline ? styles.multilineInput : null]}
          value={value}
        />
        {!!rightElement && <View style={styles.rightElement}>{rightElement}</View>}
      </View>
      {!!error && <Text style={styles.errorText}>{error}</Text>}
    </View>
  );
}

export default memo(InputField);

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: appTheme.spacing.md
  },
  label: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 12,
    letterSpacing: 0.4,
    textTransform: "uppercase",
    marginBottom: appTheme.spacing.xs
  },
  inputShell: {
    alignItems: "center",
    backgroundColor: appTheme.colors.semanticSurfaceMuted,
    borderColor: appTheme.colors.borderSubtle,
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
    fontFamily: "Rajdhani_500Medium",
    fontSize: 17,
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
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 12,
    marginTop: 4
  }
});
