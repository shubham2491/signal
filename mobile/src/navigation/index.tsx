import React from 'react';
import { NavigationContainer, type NavigatorScreenParams } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StyleSheet, Text, View } from 'react-native';
import type { AnalysisReport } from '@/api/client';
import { colors, spacing, type as typo } from '@/theme';

import { HomeScreen } from '@/screens/HomeScreen';
import { UploadPreviewScreen } from '@/screens/UploadPreviewScreen';
import { AnalysisScreen } from '@/screens/AnalysisScreen';
import { ResultsScreen } from '@/screens/ResultsScreen';
import { HistoryScreen } from '@/screens/HistoryScreen';
import { ExportScreen } from '@/screens/ExportScreen';
import { ProfileScreen } from '@/screens/ProfileScreen';

export type SelectedImage = { uri: string; mime: string; name: string };

export type RootStackParamList = {
  Tabs: NavigatorScreenParams<TabParamList> | undefined;
  // Deep screens live in the stack above the tab navigator so they get
  // full-bleed presentation without the tab bar.
  UploadPreview: { images: SelectedImage[] };
  Analysis: { images: SelectedImage[] };
  Results: { report: AnalysisReport; thumbnails: string[] };
  Export: { report: AnalysisReport };
};

export type TabParamList = {
  Home: undefined;
  History: undefined;
  Profile: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tabs = createBottomTabNavigator<TabParamList>();

function TabIcon({ glyph, active }: { glyph: string; active: boolean }) {
  return (
    <View style={styles.tabIcon}>
      <Text style={[styles.tabGlyph, active && styles.tabGlyphActive]}>{glyph}</Text>
    </View>
  );
}

function TabsNavigator() {
  return (
    <Tabs.Navigator
      screenOptions={{
        headerShown: false,
        tabBarShowLabel: true,
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: colors.emerald,
        tabBarInactiveTintColor: colors.textSubtle,
        tabBarLabelStyle: styles.tabLabel,
        sceneStyle: { backgroundColor: colors.bg },
      }}
    >
      <Tabs.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon glyph="◉" active={focused} />,
        }}
      />
      <Tabs.Screen
        name="History"
        component={HistoryScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon glyph="◷" active={focused} />,
        }}
      />
      <Tabs.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon glyph="◯" active={focused} />,
        }}
      />
    </Tabs.Navigator>
  );
}

export function RootNavigator() {
  return (
    <NavigationContainer
      theme={{
        dark: false,
        colors: {
          primary: colors.emerald,
          background: colors.bg,
          card: colors.bg,
          text: colors.text,
          border: colors.divider,
          notification: colors.burgundy,
        },
        fonts: {
          regular: { fontFamily: 'System', fontWeight: '400' },
          medium:  { fontFamily: 'System', fontWeight: '500' },
          bold:    { fontFamily: 'System', fontWeight: '700' },
          heavy:   { fontFamily: 'System', fontWeight: '800' },
        },
      }}
    >
      <Stack.Navigator
        initialRouteName="Tabs"
        screenOptions={{
          headerShown: false,
          animation: 'fade',
          contentStyle: { backgroundColor: colors.bg },
        }}
      >
        <Stack.Screen name="Tabs" component={TabsNavigator} />
        <Stack.Screen name="UploadPreview" component={UploadPreviewScreen} />
        <Stack.Screen
          name="Analysis"
          component={AnalysisScreen}
          options={{ animation: 'fade', gestureEnabled: false }}
        />
        <Stack.Screen name="Results" component={ResultsScreen} />
        <Stack.Screen name="Export" component={ExportScreen} options={{ presentation: 'modal' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: colors.bg,
    borderTopColor: colors.divider,
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingTop: 6,
    height: 68,
  },
  tabIcon: { alignItems: 'center', justifyContent: 'center', height: 22 },
  tabGlyph: { fontSize: 16, color: colors.textSubtle },
  tabGlyphActive: { color: colors.emerald },
  tabLabel: { ...typo.caption, fontSize: 10, letterSpacing: 0.4, paddingTop: 2 },
});

export type { NavigatorScreenParams };
