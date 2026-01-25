import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';

import DashboardScreen from '../screens/admin/DashboardScreen';
import VendorsScreen from '../screens/admin/VendorsScreen';
import CategoriesScreen from '../screens/admin/CategoriesScreen';
import AdminsScreen from '../screens/admin/AdminsScreen';
import ProfileScreen from '../screens/admin/ProfileScreen';
import { useAuthStore } from '../store/authStore';

const Tab = createBottomTabNavigator();

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
            <Tab.Screen name="Dashboard" component={DashboardScreen} />
            <Tab.Screen name="Vendors" component={VendorsScreen} />
            <Tab.Screen name="Categories" component={CategoriesScreen} />
            {isSuperAdmin && (
                <Tab.Screen name="Admins" component={AdminsScreen} />
            )}
            <Tab.Screen name="Profile" component={ProfileScreen} />
        </Tab.Navigator>
    );
}
