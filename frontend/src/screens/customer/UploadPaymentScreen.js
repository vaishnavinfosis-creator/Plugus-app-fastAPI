import React, { useState } from 'react';
import {
    View,
    Text,
    TouchableOpacity,
    StyleSheet,
    Image,
    Alert,
    ActivityIndicator,
    Platform
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as ImageManipulator from 'expo-image-manipulator';
import client from '../../api/client';

const UploadPaymentScreen = ({ route, navigation }) => {
    const { bookingId } = route.params;
    
    const [selectedImage, setSelectedImage] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);

    const requestPermissions = async () => {
        if (Platform.OS !== 'web') {
            const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert(
                    'Permission Required',
                    'Please grant camera roll permissions to upload payment receipts'
                );
                return false;
            }
        }
        return true;
    };

    const compressImage = async (uri) => {
        try {
            const manipResult = await ImageManipulator.manipulateAsync(
                uri,
                [{ resize: { width: 1024 } }], // Resize to max width 1024px
                { compress: 0.7, format: ImageManipulator.SaveFormat.JPEG }
            );
            return manipResult.uri;
        } catch (error) {
            console.error('Image compression error:', error);
            return uri; // Return original if compression fails
        }
    };

    const pickImageFromGallery = async () => {
        const hasPermission = await requestPermissions();
        if (!hasPermission) return;

        try {
            const result = await ImagePicker.launchImageLibraryAsync({
                mediaTypes: ImagePicker.MediaTypeOptions.Images,
                allowsEditing: true,
                aspect: [4, 3],
                quality: 0.8,
            });

            if (!result.canceled && result.assets && result.assets.length > 0) {
                const compressedUri = await compressImage(result.assets[0].uri);
                setSelectedImage(compressedUri);
            }
        } catch (error) {
            Alert.alert('Error', 'Failed to pick image from gallery');
            console.error(error);
        }
    };

    const takePhoto = async () => {
        const hasPermission = await requestPermissions();
        if (!hasPermission) return;

        try {
            const result = await ImagePicker.launchCameraAsync({
                allowsEditing: true,
                aspect: [4, 3],
                quality: 0.8,
            });

            if (!result.canceled && result.assets && result.assets.length > 0) {
                const compressedUri = await compressImage(result.assets[0].uri);
                setSelectedImage(compressedUri);
            }
        } catch (error) {
            Alert.alert('Error', 'Failed to take photo');
            console.error(error);
        }
    };

    const uploadPayment = async () => {
        if (!selectedImage) {
            Alert.alert('Error', 'Please select an image first');
            return;
        }

        setUploading(true);
        setUploadProgress(0);

        try {
            // Create form data
            const formData = new FormData();
            
            // Get file extension
            const uriParts = selectedImage.split('.');
            const fileType = uriParts[uriParts.length - 1];
            
            formData.append('file', {
                uri: selectedImage,
                name: `payment_${bookingId}.${fileType}`,
                type: `image/${fileType}`,
            });

            // Upload with progress tracking
            const response = await client.post(
                `/payments/bookings/${bookingId}/payment-receipt`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                    onUploadProgress: (progressEvent) => {
                        const progress = Math.round(
                            (progressEvent.loaded * 100) / progressEvent.total
                        );
                        setUploadProgress(progress);
                    },
                }
            );

            Alert.alert(
                'Success',
                'Payment receipt uploaded successfully! Your payment will be verified by our team.',
                [
                    {
                        text: 'OK',
                        onPress: () => navigation.goBack()
                    }
                ]
            );
        } catch (error) {
            const errorMessage = error.response?.data?.detail || 'Failed to upload payment receipt';
            Alert.alert('Upload Failed', errorMessage);
        } finally {
            setUploading(false);
            setUploadProgress(0);
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Upload Payment Receipt</Text>
            <Text style={styles.subtitle}>
                Please upload a clear photo of your payment receipt
            </Text>

            {/* Image Preview */}
            {selectedImage ? (
                <View style={styles.imageContainer}>
                    <Image source={{ uri: selectedImage }} style={styles.image} />
                    <TouchableOpacity
                        style={styles.removeButton}
                        onPress={() => setSelectedImage(null)}
                    >
                        <Text style={styles.removeButtonText}>Remove</Text>
                    </TouchableOpacity>
                </View>
            ) : (
                <View style={styles.placeholderContainer}>
                    <Text style={styles.placeholderText}>No image selected</Text>
                </View>
            )}

            {/* Upload Progress */}
            {uploading && (
                <View style={styles.progressContainer}>
                    <ActivityIndicator size="large" color="#007AFF" />
                    <Text style={styles.progressText}>
                        Uploading... {uploadProgress}%
                    </Text>
                </View>
            )}

            {/* Action Buttons */}
            {!uploading && (
                <>
                    <View style={styles.buttonRow}>
                        <TouchableOpacity
                            style={[styles.button, styles.cameraButton]}
                            onPress={takePhoto}
                        >
                            <Text style={styles.buttonText}>📷 Take Photo</Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={[styles.button, styles.galleryButton]}
                            onPress={pickImageFromGallery}
                        >
                            <Text style={styles.buttonText}>🖼️ Choose from Gallery</Text>
                        </TouchableOpacity>
                    </View>

                    <TouchableOpacity
                        style={[
                            styles.uploadButton,
                            !selectedImage && styles.uploadButtonDisabled
                        ]}
                        onPress={uploadPayment}
                        disabled={!selectedImage}
                    >
                        <Text style={styles.uploadButtonText}>Upload Receipt</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={styles.cancelButton}
                        onPress={() => navigation.goBack()}
                    >
                        <Text style={styles.cancelButtonText}>Cancel</Text>
                    </TouchableOpacity>
                </>
            )}

            {/* Requirements */}
            <View style={styles.requirementsContainer}>
                <Text style={styles.requirementsTitle}>Requirements:</Text>
                <Text style={styles.requirementText}>• Format: JPEG or PNG</Text>
                <Text style={styles.requirementText}>• Maximum size: 5MB</Text>
                <Text style={styles.requirementText}>• Image should be clear and readable</Text>
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        padding: 20,
        backgroundColor: '#f5f5f5',
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 10,
    },
    subtitle: {
        fontSize: 16,
        color: '#666',
        marginBottom: 20,
    },
    imageContainer: {
        alignItems: 'center',
        marginBottom: 20,
    },
    image: {
        width: '100%',
        height: 300,
        borderRadius: 8,
        resizeMode: 'contain',
    },
    removeButton: {
        marginTop: 10,
        padding: 10,
        backgroundColor: '#ff3b30',
        borderRadius: 8,
    },
    removeButtonText: {
        color: '#fff',
        fontWeight: '600',
    },
    placeholderContainer: {
        width: '100%',
        height: 300,
        backgroundColor: '#e0e0e0',
        borderRadius: 8,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 20,
    },
    placeholderText: {
        fontSize: 16,
        color: '#999',
    },
    progressContainer: {
        alignItems: 'center',
        marginVertical: 20,
    },
    progressText: {
        marginTop: 10,
        fontSize: 16,
        color: '#007AFF',
    },
    buttonRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 15,
    },
    button: {
        flex: 1,
        padding: 15,
        borderRadius: 8,
        alignItems: 'center',
        marginHorizontal: 5,
    },
    cameraButton: {
        backgroundColor: '#34C759',
    },
    galleryButton: {
        backgroundColor: '#5856D6',
    },
    buttonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
    },
    uploadButton: {
        backgroundColor: '#007AFF',
        padding: 16,
        borderRadius: 8,
        alignItems: 'center',
        marginBottom: 10,
    },
    uploadButtonDisabled: {
        backgroundColor: '#ccc',
    },
    uploadButtonText: {
        color: '#fff',
        fontSize: 18,
        fontWeight: '600',
    },
    cancelButton: {
        padding: 16,
        borderRadius: 8,
        alignItems: 'center',
        marginBottom: 20,
    },
    cancelButtonText: {
        color: '#666',
        fontSize: 16,
    },
    requirementsContainer: {
        backgroundColor: '#fff',
        padding: 15,
        borderRadius: 8,
        borderLeftWidth: 4,
        borderLeftColor: '#007AFF',
    },
    requirementsTitle: {
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 10,
    },
    requirementText: {
        fontSize: 14,
        color: '#666',
        marginBottom: 5,
    },
});

export default UploadPaymentScreen;
