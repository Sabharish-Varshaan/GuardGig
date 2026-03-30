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
