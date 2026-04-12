import React, { useEffect, useRef, useState } from "react";
import {
  NavigationContainer,
  DefaultTheme,
  useNavigationContainerRef
} from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";

import { useAppContext } from "../context/AppContext";
import SettingsScreen from "../screens/SettingsScreen";
import SplashScreen from "../screens/SplashScreen";
import PaymentScreen from "../screens/PaymentScreen";
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
  const navigationRef = useNavigationContainerRef();
  const routeNameRef = useRef("");

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
    <NavigationContainer
      ref={navigationRef}
      theme={navigationTheme}
      onReady={() => {
        routeNameRef.current = navigationRef.getCurrentRoute()?.name || "unknown";
      }}
      onStateChange={() => {
        const routeName = navigationRef.getCurrentRoute()?.name || "unknown";
        if (routeNameRef.current !== routeName) {
          routeNameRef.current = routeName;
        }
      }}
    >
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
            <RootStack.Screen
              component={PaymentScreen}
              name="Payment"
              options={{ title: "Premium Payment" }}
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
