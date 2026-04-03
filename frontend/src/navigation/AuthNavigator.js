import React from "react";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import LoginScreen from "../screens/LoginScreen";
import OnboardingScreen from "../screens/OnboardingScreen";
import RegistrationScreen from "../screens/RegistrationScreen";
import { appTheme } from "../styles/theme";

const Stack = createNativeStackNavigator();

export default function AuthNavigator() {
  return (
    <Stack.Navigator
      initialRouteName="Login"
      screenOptions={{
        animation: "fade_from_bottom",
        contentStyle: { backgroundColor: appTheme.colors.bgPrimary },
        headerStyle: { backgroundColor: appTheme.colors.bgCard },
        headerTintColor: appTheme.colors.textPrimary,
        headerTitleStyle: {
          ...appTheme.typography.subtitle,
          color: appTheme.colors.textPrimary
        }
      }}
    >
      <Stack.Screen component={LoginScreen} name="Login" options={{ headerShown: false }} />
      <Stack.Screen
        component={RegistrationScreen}
        name="Register"
        options={{ title: "Create Account" }}
      />
      <Stack.Screen
        component={OnboardingScreen}
        name="Onboarding"
        options={{ title: "Profile Setup" }}
      />
    </Stack.Navigator>
  );
}
