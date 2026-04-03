import React from "react";
import NeonButton from "./NeonButton";

export default function Button({
  title,
  onPress,
  variant = "primary",
  style,
  disabled = false,
  loading = false
}) {
  return (
    <NeonButton
      disabled={disabled}
      loading={loading}
      onPress={onPress}
      style={style}
      title={title}
      variant={variant}
    />
  );
}
