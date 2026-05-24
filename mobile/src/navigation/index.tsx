import React from 'react';
import { NavigationContainer, type NavigatorScreenParams } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import type { AnalysisReport } from '@/api/client';
import type { HistoryEntry } from '@/storage/history';
import { colors } from '@/theme';

import { HomeScreen } from '@/screens/HomeScreen';
import { UploadPreviewScreen } from '@/screens/UploadPreviewScreen';
import { AnalysisScreen } from '@/screens/AnalysisScreen';
import { ResultsScreen } from '@/screens/ResultsScreen';
import { HistoryScreen } from '@/screens/HistoryScreen';
import { ExportScreen } from '@/screens/ExportScreen';

export type SelectedImage = { uri: string; mime: string; name: string };

export type RootStackParamList = {
  Home: undefined;
  UploadPreview: { images: SelectedImage[] };
  Analysis: { images: SelectedImage[] };
  Results: { report: AnalysisReport; thumbnails: string[] };
  History: undefined;
  Export: { report: AnalysisReport };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
  return (
    <NavigationContainer
      theme={{
        dark: false,
        colors: {
          primary: colors.text,
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
        initialRouteName="Home"
        screenOptions={{
          headerShown: false,
          animation: 'fade',
          contentStyle: { backgroundColor: colors.bg },
        }}
      >
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="UploadPreview" component={UploadPreviewScreen} />
        <Stack.Screen
          name="Analysis"
          component={AnalysisScreen}
          options={{ animation: 'fade', gestureEnabled: false }}
        />
        <Stack.Screen name="Results" component={ResultsScreen} />
        <Stack.Screen name="History" component={HistoryScreen} />
        <Stack.Screen name="Export" component={ExportScreen} options={{ presentation: 'modal' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

export type { NavigatorScreenParams };
