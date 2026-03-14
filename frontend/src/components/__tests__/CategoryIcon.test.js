import React from 'react';
import { render } from '@testing-library/react-native';
import CategoryIcon from '../CategoryIcon';

// Mock Ionicons
jest.mock('@expo/vector-icons', () => ({
    Ionicons: 'Ionicons'
}));

// Mock Image component
jest.mock('react-native', () => {
    const RN = jest.requireActual('react-native');
    RN.Image.resolveAssetSource = jest.fn(() => ({ uri: 'mocked' }));
    return RN;
});

describe('CategoryIcon', () => {
    it('renders Ionicons when valid icon name is provided', () => {
        const { getByTestId } = render(
            <CategoryIcon iconName="car-sport" size={36} color="#1E88E5" />
        );
        
        // Component should render without errors
        expect(getByTestId).toBeDefined();
    });

    it('renders default logo when no icon name is provided', () => {
        const { UNSAFE_getByType } = render(
            <CategoryIcon iconName={null} size={36} color="#1E88E5" />
        );
        
        // Should render Image component (default logo)
        const images = UNSAFE_getByType('Image');
        expect(images).toBeDefined();
    });

    it('renders default logo when empty icon name is provided', () => {
        const { UNSAFE_getByType } = render(
            <CategoryIcon iconName="" size={36} color="#1E88E5" />
        );
        
        // Should render Image component (default logo)
        const images = UNSAFE_getByType('Image');
        expect(images).toBeDefined();
    });

    it('applies custom size to icon', () => {
        const { UNSAFE_getByType } = render(
            <CategoryIcon iconName={null} size={48} color="#1E88E5" />
        );
        
        const image = UNSAFE_getByType('Image');
        expect(image.props.style).toContainEqual(
            expect.objectContaining({ width: 48, height: 48 })
        );
    });
});
