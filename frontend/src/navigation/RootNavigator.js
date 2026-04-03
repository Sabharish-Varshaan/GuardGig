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
    background: appTheme.colors.bgPrimary,
    card: appTheme.colors.bgCard,
    primary: appTheme.colors.accentPrimary,
    text: appTheme.colors.textPrimary,
    border: appTheme.colors.borderSubtle
  }
};

export default function RootNavigator() {
  const { isAuthenticated, authInitializing } = useAppContext();
  const [booting, setBooting] = useState(true);

  useEffect(() => {
    if (authInitializing) {
      return undefined;
    }

    const timer = setTimeout(() => {
      setBooting(false);
    }, 1400);

    return () => {
      clearTimeout(timer);
    };
  }, [authInitializing]);

  if (booting || authInitializing) {
    return <SplashScreen />;
  }

  return (
    <NavigationContainer theme={navigationTheme}>
      <StatusBar style="light" />
      <RootStack.Navigator
        screenOptions={{
          animation: "fade_from_bottom",
          contentStyle: { backgroundColor: appTheme.colors.bgPrimary },
          headerStyle: {
            backgroundColor: appTheme.colors.bgCard
          },
          headerTintColor: appTheme.colors.textPrimary,
          headerTitleStyle: {
            ...appTheme.typography.subtitle,
            color: appTheme.colors.textPrimary
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
