import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';

import DashboardScreen from '../screens/admin/DashboardScreen';
import VendorsScreen from '../screens/admin/VendorsScreen';
import CategoriesScreen from '../screens/admin/CategoriesScreen';
import AdminsScreen from '../screens/admin/AdminsScreen';
import RegionsScreen from '../screens/admin/RegionsScreen';
import ProfileScreen from '../screens/admin/ProfileScreen';
import ChangePasswordScreen from '../screens/admin/ChangePasswordScreen';
import RegionRevenueScreen from '../screens/admin/RegionRevenueScreen';
import VendorTransactionsScreen from '../screens/admin/VendorTransactionsScreen';
import { useAuthStore } from '../store/authStore';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function DashboardStack() {
    return (
        <Stack.Navigator>
            <Stack.Screen 
                name="DashboardMain" 
                component={DashboardScreen}
                options={{ headerShown: false }}
            />
            <Stack.Screen 
                name="RegionRevenue" 
                component={RegionRevenueScreen}
                options={{ 
                    title: 'Revenue by Region',
                    headerBackTitle: 'Dashboard'
                }}
            />
        </Stack.Navigator>
    );
}

function VendorsStack() {
    return (
        <Stack.Navigator>
            <Stack.Screen 
                name="VendorsList" 
                component={VendorsScreen}
                options={{ headerShown: false }}
            />
            <Stack.Screen 
                name="VendorTransactions" 
                component={VendorTransactionsScreen}
                options={{ 
                    title: 'Transaction History',
                    headerBackTitle: 'Vendors'
                }}
            />
        </Stack.Navigator>
    );
}

function ProfileStack() {
    return (
        <Stack.Navigator>
            <Stack.Screen 
                name="ProfileMain" 
                component={ProfileScreen}
                options={{ headerShown: false }}
            />
            <Stack.Screen 
                name="ChangePassword" 
                component={ChangePasswordScreen}
                options={{ headerShown: false }}
            />
        </Stack.Navigator>
    );
}

export default function AdminNavigator() {
    const { user } = useAuthStore();
    const isSuperAdmin = user?.role === 'SUPER_ADMIN';

    return (
        <Tab.Navigator
            screenOptions={({ route }) => ({
                tabBarIcon: ({ focused, color, size }) => {
                    let iconName;
                    if (route.name === 'Dashboard') {
                        iconName = focused ? 'grid' : 'grid-outline';
                    } else if (route.name === 'Vendors') {
                        iconName = focused ? 'storefront' : 'storefront-outline';
                    } else if (route.name === 'Categories') {
                        iconName = focused ? 'apps' : 'apps-outline';
                    } else if (route.name === 'Regions') {
                        iconName = focused ? 'location' : 'location-outline';
                    } else if (route.name === 'Admins') {
                        iconName = focused ? 'people' : 'people-outline';
                    } else if (route.name === 'Profile') {
                        iconName = focused ? 'person' : 'person-outline';
                    }
                    return <Ionicons name={iconName} size={size} color={color} />;
                },
                tabBarActiveTintColor: '#1E88E5',
                tabBarInactiveTintColor: 'gray',
                headerShown: false,
            })}
        >
            <Tab.Screen name="Dashboard" component={DashboardStack} />
            <Tab.Screen name="Vendors" component={VendorsStack} />
            <Tab.Screen name="Categories" component={CategoriesScreen} />
            {isSuperAdmin && (
                <>
                    <Tab.Screen name="Regions" component={RegionsScreen} />
                    <Tab.Screen name="Admins" component={AdminsScreen} />
                </>
            )}
            <Tab.Screen name="Profile" component={ProfileStack} />
        </Tab.Navigator>
    );
}
