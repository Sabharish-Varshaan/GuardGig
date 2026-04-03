import React, { memo } from "react";
import { Ionicons } from "@expo/vector-icons";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";

import ClaimsScreen from "../screens/ClaimsScreen";
import DashboardScreen from "../screens/DashboardScreen";
import PayoutScreen from "../screens/PayoutScreen";
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
  Payout: "wallet-outline",
  Profile: "person-circle-outline"
};

function TabIcon({ routeName, focused }) {
  const iconName = iconMap[routeName] || "ellipse-outline";

  return (
    <Ionicons
      color={focused ? appTheme.colors.accentPrimary : appTheme.colors.textSecondary}
      name={iconName}
      size={focused ? 22 : 20}
    />
  );
}

function MainTabNavigator() {
  return (
    <Tab.Navigator
      initialRouteName="Home"
      screenOptions={({ route }) => ({
        animation: "fade",
        headerShown: false,
        tabBarHideOnKeyboard: true,
        tabBarActiveTintColor: appTheme.colors.accentPrimary,
        tabBarInactiveTintColor: appTheme.colors.textSecondary,
        tabBarStyle: {
          position: "absolute",
          backgroundColor: appTheme.colors.tabGlass,
          borderColor: appTheme.colors.borderSubtle,
          borderTopWidth: 1,
          borderRadius: appTheme.radius.card,
          elevation: 0,
          height: 84,
          marginBottom: 10,
          marginHorizontal: 16,
          paddingBottom: 12,
          paddingTop: 10,
          ...appTheme.shadows.floating
        },
        tabBarLabelStyle: {
          ...appTheme.typography.caption,
          color: appTheme.colors.textSecondary,
          fontSize: 12,
          lineHeight: 14
        },
        tabBarIcon: ({ focused }) => <TabIcon focused={focused} routeName={route.name} />
      })}
    >
      <Tab.Screen component={DashboardScreen} name="Home" />
      <Tab.Screen component={RiskScreen} name="Risk" />
      <Tab.Screen component={PolicyScreen} name="Policy" />
      <Tab.Screen component={ClaimsScreen} name="Claims" />
      <Tab.Screen component={PayoutScreen} name="Payout" />
      <Tab.Screen component={ProfileScreen} name="Profile" />
    </Tab.Navigator>
  );
}

export default memo(MainTabNavigator);
