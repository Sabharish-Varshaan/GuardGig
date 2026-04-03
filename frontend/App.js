import React from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { useFonts } from "expo-font";
import { Orbitron_600SemiBold, Orbitron_700Bold } from "@expo-google-fonts/orbitron";
import { Rajdhani_500Medium, Rajdhani_600SemiBold, Rajdhani_700Bold } from "@expo-google-fonts/rajdhani";

import { AppProvider } from "./src/context/AppContext";
import RootNavigator from "./src/navigation/RootNavigator";
import { appTheme } from "./src/styles/theme";

export default function App() {
  const [fontsLoaded] = useFonts({
    Orbitron_600SemiBold,
    Orbitron_700Bold,
    Rajdhani_500Medium,
    Rajdhani_600SemiBold,
    Rajdhani_700Bold
  });

  if (!fontsLoaded) {
    return (
      <View style={styles.loaderScreen}>
        <ActivityIndicator color={appTheme.colors.accentPrimary} size="large" />
      </View>
    );
  }

  return (
    <AppProvider>
      <RootNavigator />
    </AppProvider>
  );
}

const styles = StyleSheet.create({
  loaderScreen: {
    alignItems: "center",
    backgroundColor: appTheme.colors.bgPrimary,
    flex: 1,
    justifyContent: "center"
  }
});
