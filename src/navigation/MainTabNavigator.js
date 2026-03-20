import React from "react";
import { Text } from "react-native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";

import ClaimsScreen from "../screens/ClaimsScreen";
import DashboardScreen from "../screens/DashboardScreen";
import PolicyScreen from "../screens/PolicyScreen";
import ProfileScreen from "../screens/ProfileScreen";
import RiskScreen from "../screens/RiskScreen";
import { appTheme } from "../styles/theme";

const Tab = createBottomTabNavigator();

const iconMap = {
  Home: "🏠",
  Risk: "📊",
  Policy: "📜",
  Claims: "💸",
  Profile: "👤"
};

function TabIcon({ routeName, focused }) {
  return (
    <Text
      style={{
        fontSize: focused ? 19 : 18,
        opacity: focused ? 1 : 0.7
      }}
    >
      {iconMap[routeName]}
    </Text>
  );
}

export default function MainTabNavigator() {
  return (
    <Tab.Navigator
      initialRouteName="Home"
      screenOptions={({ route }) => ({
        animation: "fade",
        headerShown: false,
        tabBarActiveTintColor: appTheme.colors.primary,
        tabBarInactiveTintColor: appTheme.colors.textSecondary,
        tabBarStyle: {
          backgroundColor: appTheme.colors.surface,
          borderTopWidth: 0,
          elevation: 20,
          height: 78,
          paddingBottom: 10,
          paddingTop: 8
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: "700"
        },
        tabBarIcon: ({ focused }) => <TabIcon focused={focused} routeName={route.name} />
      })}
    >
      <Tab.Screen component={DashboardScreen} name="Home" />
      <Tab.Screen component={RiskScreen} name="Risk" />
      <Tab.Screen component={PolicyScreen} name="Policy" />
      <Tab.Screen component={ClaimsScreen} name="Claims" />
      <Tab.Screen component={ProfileScreen} name="Profile" />
    </Tab.Navigator>
  );
}
