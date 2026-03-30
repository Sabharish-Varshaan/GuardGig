import React, { useEffect, useState } from "react";
import { NavigationContainer, DefaultTheme } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";

import { useAppContext } from "../context/AppContext";
import SettingsScreen from "../screens/SettingsScreen";
import SplashScreen from "../screens/SplashScreen";
import { appTheme } from "../styles/theme";
import AuthNavigator from "./AuthNavigator";
import MainTabNavigator from "./MainTabNavigator";

const RootStack = createNativeStackNavigator();

const navigationTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: appTheme.colors.background,
    card: appTheme.colors.primary,
    primary: appTheme.colors.accent,
    text: appTheme.colors.surface,
    border: "transparent"
  }
};

export default function RootNavigator() {
  const { isAuthenticated, authInitializing } = useAppContext();
  const [booting, setBooting] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setBooting(false);
    }, 1400);

    return () => {
      clearTimeout(timer);
    };
  }, []);

  if (booting || authInitializing) {
    return <SplashScreen />;
  }

  return (
    <NavigationContainer theme={navigationTheme}>
      <StatusBar style="light" />
      <RootStack.Navigator
        screenOptions={{
          animation: "slide_from_right",
          contentStyle: { backgroundColor: appTheme.colors.background },
          headerStyle: { backgroundColor: appTheme.colors.primary },
          headerTintColor: appTheme.colors.surface,
          headerTitleStyle: {
            fontSize: 17,
            fontWeight: "700"
          }
        }}
      >
        {isAuthenticated ? (
          <>
            <RootStack.Screen
              component={MainTabNavigator}
              name="MainTabs"
              options={{ headerShown: false }}
            />
            <RootStack.Screen
              component={SettingsScreen}
              name="Settings"
              options={{ title: "Settings" }}
            />
          </>
        ) : (
          <RootStack.Screen
            component={AuthNavigator}
            name="Auth"
            options={{ headerShown: false }}
          />
        )}
      </RootStack.Navigator>
    </NavigationContainer>
  );
}
