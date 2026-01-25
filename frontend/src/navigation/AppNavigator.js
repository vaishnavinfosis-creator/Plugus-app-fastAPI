import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuthStore } from '../store/authStore';
import { ActivityIndicator, View } from 'react-native';

// Auth screens
import SplashScreen from '../screens/SplashScreen';
import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';

// Role-based navigators
import CustomerNavigator from './CustomerNavigator';
import VendorNavigator from './VendorNavigator';
import WorkerNavigator from './WorkerNavigator';
import AdminNavigator from './AdminNavigator';

const Stack = createNativeStackNavigator();

export default function AppNavigator() {
    const { token, user, isLoading, loadToken } = useAuthStore();
    const [showSplash, setShowSplash] = useState(true);

    useEffect(() => {
        loadToken();
    }, []);

    // Show splash screen first
    if (showSplash) {
        return <SplashScreen onFinish={() => setShowSplash(false)} />;
    }

    // Show loading while checking auth
    if (isLoading) {
        return (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff' }}>
                <ActivityIndicator size="large" color="#1E88E5" />
            </View>
        );
    }

    // Get role-based navigator
    const getRoleNavigator = () => {
        console.log('getRoleNavigator called. User:', user ? user.role : 'null', 'Token:', !!token);
        if (!user) {
            return (
                <Stack.Screen
                    name="Loading"
                    component={() => (
                        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff' }}>
                            <ActivityIndicator size="large" color="#1E88E5" />
                        </View>
                    )}
                />
            );
        }

        switch (user.role) {
            case 'CUSTOMER':
                return <Stack.Screen name="CustomerRoot" component={CustomerNavigator} />;
            case 'VENDOR':
                return <Stack.Screen name="VendorRoot" component={VendorNavigator} />;
            case 'WORKER':
                return <Stack.Screen name="WorkerRoot" component={WorkerNavigator} />;
            case 'REGIONAL_ADMIN':
            case 'SUPER_ADMIN':
                return <Stack.Screen name="AdminRoot" component={AdminNavigator} />;
            default:
                return (
                    <Stack.Screen
                        name="UnknownRole"
                        component={() => (
                            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                                <Text>Unknown User Role</Text>
                            </View>
                        )}
                    />
                );
        }
    };

    return (
        <NavigationContainer>
            <Stack.Navigator screenOptions={{ headerShown: false }}>
                {!token ? (
                    // Auth screens
                    <>
                        <Stack.Screen name="Login" component={LoginScreen} />
                        <Stack.Screen name="Register" component={RegisterScreen} />
                    </>
                ) : (
                    // Role-based navigation
                    getRoleNavigator()
                )}
            </Stack.Navigator>
        </NavigationContainer>
    );
}
