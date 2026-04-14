import React, { useEffect } from "react";
import { StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { appTheme } from "../styles/theme";

const ICON_BY_TYPE = {
  success: "checkmark-circle",
  error: "alert-circle",
  info: "notifications"
};

export default function ToastOverlay({ toast, onDismiss }) {
  useEffect(() => {
    if (!toast) {
      return undefined;
    }

    const timer = setTimeout(() => {
      onDismiss?.();
    }, 2800);

    return () => clearTimeout(timer);
  }, [onDismiss, toast]);

  if (!toast) {
    return null;
  }

  const iconName = ICON_BY_TYPE[toast.type] || ICON_BY_TYPE.info;

  return (
    <View pointerEvents="none" style={styles.wrapper}>
      <View style={styles.toast}>
        <Ionicons color={appTheme.colors.accentSuccess} name={iconName} size={18} />
        <Text style={styles.toastText}>{toast.message}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    bottom: 110,
    left: 16,
    position: "absolute",
    right: 16,
    zIndex: 1000
  },
  toast: {
    alignItems: "center",
    backgroundColor: appTheme.colors.bgElevated,
    borderColor: appTheme.colors.successBorder,
    borderRadius: appTheme.radius.soft,
    borderWidth: 1,
    flexDirection: "row",
    gap: 10,
    paddingHorizontal: appTheme.spacing.sm,
    paddingVertical: appTheme.spacing.xs,
    ...appTheme.shadows.floating
  },
  toastText: {
    color: appTheme.colors.textPrimary,
    flex: 1,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 15,
    lineHeight: 20
  }
});
