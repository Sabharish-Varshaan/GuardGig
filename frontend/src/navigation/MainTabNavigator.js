import React from "react";
import { Ionicons } from "@expo/vector-icons";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";

import ClaimsScreen from "../screens/ClaimsScreen";
import DashboardScreen from "../screens/DashboardScreen";
import PolicyScreen from "../screens/PolicyScreen";
import ProfileScreen from "../screens/ProfileScreen";
import RiskScreen from "../screens/RiskScreen";
import { appTheme } from "../styles/theme";

const Tab = createBottomTabNavigator();

const iconMap = {
  Home: "grid-outline",
  Risk: "pulse-outline",
  Policy: "document-text-outline",
  Claims: "cash-outline",
  Profile: "person-circle-outline"
};

function TabIcon({ routeName, focused }) {
  const iconName = iconMap[routeName] || "ellipse-outline";

  return (
    <Ionicons
      color={focused ? appTheme.colors.primary : appTheme.colors.textSecondary}
      name={iconName}
      size={focused ? 22 : 20}
    />
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
          position: "absolute",
          backgroundColor: appTheme.colors.tabGlass,
          borderTopWidth: 0,
          borderRadius: 24,
          elevation: 0,
          height: 76,
          marginBottom: 12,
          marginHorizontal: 16,
          paddingBottom: 10,
          paddingTop: 8,
          ...appTheme.shadows.floating
        },
        tabBarLabelStyle: {
          fontSize: 11,
          letterSpacing: 0.2,
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
