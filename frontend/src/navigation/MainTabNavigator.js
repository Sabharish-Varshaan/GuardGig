import React, { memo } from "react";
import { Ionicons } from "@expo/vector-icons";
import { useWindowDimensions } from "react-native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { useSafeAreaInsets } from "react-native-safe-area-context";

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
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const isMobileLayout = width < 768;
  const computedTabBarHeight = isMobileLayout ? 62 + Math.max(insets.bottom, 6) : 84;

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
          borderRadius: isMobileLayout ? 0 : appTheme.radius.card,
          elevation: 0,
          height: computedTabBarHeight,
          marginBottom: isMobileLayout ? 0 : 10,
          marginHorizontal: isMobileLayout ? 0 : 16,
          paddingBottom: isMobileLayout ? Math.max(insets.bottom, 6) : 12,
          paddingTop: isMobileLayout ? 8 : 10,
          left: 0,
          right: 0,
          ...appTheme.shadows.floating
        },
        tabBarLabelStyle: {
          ...appTheme.typography.caption,
          color: appTheme.colors.textSecondary,
          fontSize: isMobileLayout ? 11 : 12,
          lineHeight: isMobileLayout ? 13 : 14
        },
        tabBarItemStyle: {
          paddingHorizontal: isMobileLayout ? 2 : 0
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
