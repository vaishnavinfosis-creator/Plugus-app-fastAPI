import React, { useState } from 'react';
import { View, Image, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

/**
 * CategoryIcon component with fallback to default logo
 * Handles icon loading errors gracefully by switching to default service logo
 * 
 * Requirements: 3.1, 3.2, 3.3
 */
export default function CategoryIcon({ iconName, size = 36, color = '#1E88E5', style }) {
    const [useDefault, setUseDefault] = useState(false);

    // If no icon name provided or error occurred, use default logo
    if (!iconName || useDefault) {
        return (
            <View style={[styles.defaultContainer, style]}>
                <Image
                    source={require('../../assets/logo.png')}
                    style={[styles.defaultLogo, { width: size, height: size }]}
                    resizeMode="contain"
                />
            </View>
        );
    }

    // Try to render the Ionicons icon with error handling
    return (
        <View style={style}>
            <Ionicons
                name={iconName}
                size={size}
                color={color}
                onError={() => setUseDefault(true)}
            />
        </View>
    );
}

const styles = StyleSheet.create({
    defaultContainer: {
        justifyContent: 'center',
        alignItems: 'center'
    },
    defaultLogo: {
        // Size is set dynamically via props
    }
});
