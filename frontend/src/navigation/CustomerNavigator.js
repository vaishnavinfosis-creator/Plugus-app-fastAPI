import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';

// Screens
import HomeScreen from '../screens/customer/HomeScreen';
import BookingsScreen from '../screens/customer/BookingsScreen';
import BookingDetailScreen from '../screens/customer/BookingDetailScreen';
import ProfileScreen from '../screens/customer/ProfileScreen';
import VendorListScreen from '../screens/customer/VendorListScreen';
import VendorServicesScreen from '../screens/customer/VendorServicesScreen';
import BookServiceScreen from '../screens/customer/BookServiceScreen';
import WorkerTrackingScreen from '../screens/customer/WorkerTrackingScreen';
import ComplaintsScreen from '../screens/customer/ComplaintsScreen';
import CreateComplaintScreen from '../screens/customer/CreateComplaintScreen';
import AddAddressScreen from '../screens/customer/AddAddressScreen';
import EditAddressScreen from '../screens/customer/EditAddressScreen';
import AddPhoneScreen from '../screens/customer/AddPhoneScreen';
import EditPhoneScreen from '../screens/customer/EditPhoneScreen';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

// Home Stack - Browse and book services
function HomeStack() {
    return (
        <Stack.Navigator screenOptions={{ headerShown: false }}>
            <Stack.Screen name="HomeMain" component={HomeScreen} />
            <Stack.Screen name="VendorList" component={VendorListScreen} />
            <Stack.Screen name="VendorServices" component={VendorServicesScreen} />
            <Stack.Screen name="BookService" component={BookServiceScreen} />
        </Stack.Navigator>
    );
}

// Bookings Stack - View and track bookings
function BookingsStack() {
    return (
        <Stack.Navigator screenOptions={{ headerShown: false }}>
            <Stack.Screen name="BookingsList" component={BookingsScreen} />
            <Stack.Screen name="BookingDetail" component={BookingDetailScreen} />
            <Stack.Screen name="WorkerTracking" component={WorkerTrackingScreen} />
        </Stack.Navigator>
    );
}

// Complaints Stack - View and create complaints
function ComplaintsStack() {
    return (
        <Stack.Navigator screenOptions={{ headerShown: false }}>
            <Stack.Screen name="ComplaintsList" component={ComplaintsScreen} />
            <Stack.Screen name="CreateComplaint" component={CreateComplaintScreen} />
        </Stack.Navigator>
    );
}

// Profile Stack - Profile and settings
function ProfileStack() {
    return (
        <Stack.Navigator screenOptions={{ headerShown: false }}>
            <Stack.Screen name="ProfileMain" component={ProfileScreen} />
            <Stack.Screen name="AddAddress" component={AddAddressScreen} />
            <Stack.Screen name="EditAddress" component={EditAddressScreen} />
            <Stack.Screen name="AddPhone" component={AddPhoneScreen} />
            <Stack.Screen name="EditPhone" component={EditPhoneScreen} />
        </Stack.Navigator>
    );
}

export default function CustomerNavigator() {
    return (
        <Tab.Navigator
            screenOptions={({ route }) => ({
                tabBarIcon: ({ focused, color, size }) => {
                    let iconName;
                    if (route.name === 'Home') {
                        iconName = focused ? 'home' : 'home-outline';
                    } else if (route.name === 'Bookings') {
                        iconName = focused ? 'calendar' : 'calendar-outline';
                    } else if (route.name === 'Complaints') {
                        iconName = focused ? 'chatbox' : 'chatbox-outline';
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
            <Tab.Screen name="Home" component={HomeStack} />
            <Tab.Screen name="Bookings" component={BookingsStack} />
            <Tab.Screen name="Complaints" component={ComplaintsStack} />
            <Tab.Screen name="Profile" component={ProfileStack} />
        </Tab.Navigator>
    );
}
