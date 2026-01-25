import { create } from 'zustand';
import { Platform } from 'react-native';
import client from '../api/client';

// Simple storage abstraction
const storage = {
  getItem: async (key) => {
    if (Platform.OS === 'web') {
      return localStorage.getItem(key);
    }
    // For React Native, use AsyncStorage
    const AsyncStorage = require('@react-native-async-storage/async-storage').default;
    return AsyncStorage.getItem(key);
  },
  setItem: async (key, value) => {
    if (Platform.OS === 'web') {
      localStorage.setItem(key, value);
      return;
    }
    const AsyncStorage = require('@react-native-async-storage/async-storage').default;
    await AsyncStorage.setItem(key, value);
  },
  removeItem: async (key) => {
    if (Platform.OS === 'web') {
      localStorage.removeItem(key);
      return;
    }
    const AsyncStorage = require('@react-native-async-storage/async-storage').default;
    await AsyncStorage.removeItem(key);
  },
};

export const useAuthStore = create((set, get) => ({
  token: null,
  user: null,
  isLoading: true,

  // Load token from storage on app start
  loadToken: async () => {
    try {
      const token = await storage.getItem('token');
      if (token) {
        set({ token, isLoading: false });
        // Fetch user data
        get().fetchUser();
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
      console.error('Error loading token:', error);
      set({ isLoading: false });
    }
  },

  // Set token after login
  setToken: async (token) => {
    try {
      console.log('setToken called with token:', token?.substring(0, 20) + '...');
      await storage.setItem('token', token);
      set({ token });
      console.log('Token stored, fetching user...');
      // Fetch user data after setting token
      await get().fetchUser();
      console.log('User fetched successfully');
    } catch (error) {
      console.error('Error saving token:', error);
    }
  },

  // Fetch current user data
  fetchUser: async () => {
    try {
      const response = await client.get('/auth/me');
      set({ user: response.data });
    } catch (error) {
      console.error('Error fetching user:', error);
      // If user fetch fails, logout
      get().logout();
    }
  },

  // Set user data manually
  setUser: (user) => {
    set({ user });
  },

  // Logout
  logout: async () => {
    try {
      await storage.removeItem('token');
    } catch (error) {
      console.error('Error removing token:', error);
    }
    set({ token: null, user: null });
  },
}));
