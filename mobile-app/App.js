import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  View,
  ActivityIndicator,
  Platform,
  BackHandler,
  Text,
  TouchableOpacity,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { WebView } from 'react-native-webview';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import Constants from 'expo-constants';

// ─── Server URL ────────────────────────────────────────────────────────────────
// Physical device: must use the host machine's LAN IP, not localhost.
// Update this if your IP changes (check with ipconfig / ifconfig).
// Android Emulator only → use http://10.0.2.2:8000
const WEB_APP_PORT = '8000';

function resolveAppUrl() {
  // Optional override for non-LAN setups (public host/tunnel).
  const overrideUrl = process.env.EXPO_PUBLIC_APP_URL;
  if (overrideUrl) {
    return overrideUrl;
  }

  const hostUri =
    Constants.expoConfig?.hostUri ||
    Constants.expoGoConfig?.debuggerHost ||
    Constants.manifest2?.extra?.expoClient?.hostUri ||
    Constants.manifest?.debuggerHost;
  const host = hostUri?.split(':')?.[0];

  if (host) {
    return `http://${host}:${WEB_APP_PORT}`;
  }

  if (Platform.OS === 'android') {
    return `http://10.0.2.2:${WEB_APP_PORT}`;
  }

  return `http://localhost:${WEB_APP_PORT}`;
}

const APP_URL = resolveAppUrl();
// ───────────────────────────────────────────────────────────────────────────────

const MAX_RETRIES = 3;

export default function App() {
  const webViewRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [canGoBack, setCanGoBack] = useState(false);
  const retryCount = useRef(0);

  useEffect(() => {
    if (Platform.OS === 'android') {
      const backAction = () => {
        if (canGoBack && webViewRef.current) {
          webViewRef.current.goBack();
          return true;
        }
        return false;
      };
      const backHandler = BackHandler.addEventListener('hardwareBackPress', backAction);
      return () => backHandler.remove();
    }
  }, [canGoBack]);

  const handleError = useCallback((message) => {
    retryCount.current += 1;
    if (retryCount.current < MAX_RETRIES) {
      // Auto-retry silently before showing the error screen
      setTimeout(() => {
        if (webViewRef.current) {
          webViewRef.current.reload();
        }
      }, retryCount.current * 1500);
    } else {
      setErrorMessage(message || '');
      setHasError(true);
      setIsLoading(false);
    }
  }, []);

  const handleRetry = useCallback(() => {
    retryCount.current = 0;
    setHasError(false);
    setIsLoading(true);
  }, []);

  const injectedJS = `
    (function() {
      var meta = document.querySelector('meta[name="viewport"]');
      if (meta) {
        meta.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover');
      }

      document.body.style.overscrollBehavior = 'none';
      document.documentElement.style.overscrollBehavior = 'none';

      var originalFetch = window.fetch;
      window.fetch = function(url, options) {
        var maxRetries = 3;
        var attempt = 0;

        function tryFetch() {
          attempt++;
          return originalFetch(url, options).then(function(response) {
            if (response.status === 503 && attempt < maxRetries) {
              var delay = Math.pow(2, attempt) * 500;
              return new Promise(function(resolve) {
                setTimeout(resolve, delay);
              }).then(tryFetch);
            }
            return response;
          }).catch(function(error) {
            if (attempt < maxRetries) {
              var delay = Math.pow(2, attempt) * 500;
              return new Promise(function(resolve) {
                setTimeout(resolve, delay);
              }).then(tryFetch);
            }
            throw error;
          });
        }

        return tryFetch();
      };

      window.addEventListener('message', function(event) {
        if (window.ReactNativeWebView) {
          window.ReactNativeWebView.postMessage(JSON.stringify(event.data));
        }
      });
    })();
    true;
  `;

  if (hasError) {
    return (
      <SafeAreaProvider>
        <SafeAreaView style={styles.errorContainer}>
          <StatusBar style="light" />
          <View style={styles.errorContent}>
            <Text style={styles.errorIcon}>📡</Text>
            <Text style={styles.errorTitle}>Connection Issue</Text>
            <Text style={styles.errorMessage}>
              Unable to connect to AURA-AI. Make sure the server is running and try again.
            </Text>
            {!!errorMessage && (
              <Text style={styles.errorDetail}>{errorMessage}</Text>
            )}
            <TouchableOpacity style={styles.retryButton} onPress={handleRetry}>
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </SafeAreaProvider>
    );
  }

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" translucent backgroundColor="transparent" />

        <WebView
          ref={webViewRef}
          source={{ uri: APP_URL }}
          style={styles.webview}
          javaScriptEnabled={true}
          domStorageEnabled={true}
          startInLoadingState={false}
          allowsFullscreenVideo={true}
          allowsInlineMediaPlayback={true}
          mediaPlaybackRequiresUserAction={false}
          geolocationEnabled={true}
          allowsBackForwardNavigationGestures={true}
          injectedJavaScript={injectedJS}
          // Allow HTTP content on Android
          mixedContentMode="always"
          onLoadStart={() => setIsLoading(true)}
          onLoadEnd={() => {
            setIsLoading(false);
            retryCount.current = 0;
          }}
          onNavigationStateChange={(navState) => {
            setCanGoBack(navState.canGoBack);
          }}
          onError={(syntheticEvent) => {
            const { nativeEvent } = syntheticEvent;
            handleError(nativeEvent.description || nativeEvent.title);
          }}
          onHttpError={(syntheticEvent) => {
            const { nativeEvent } = syntheticEvent;
            if (nativeEvent.statusCode >= 500) {
              handleError(`Server error ${nativeEvent.statusCode}`);
            }
          }}
          contentMode="mobile"
          allowsLinkPreview={false}
          bounces={false}
          overScrollMode="never"
          pullToRefreshEnabled={true}
          cacheEnabled={true}
          cacheMode="LOAD_DEFAULT"
          setSupportMultipleWindows={false}
        />

        {isLoading && (
          <View style={styles.loadingOverlay}>
            <View style={styles.loadingContent}>
              <Text style={styles.loadingIcon}>🛰️</Text>
              <Text style={styles.loadingTitle}>AURA-AI</Text>
              <Text style={styles.loadingSubtitle}>Connecting to satellites...</Text>
              <ActivityIndicator size="large" color="#64B5F6" style={styles.spinner} />
            </View>
          </View>
        )}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  webview: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#0c0c0c',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  loadingContent: {
    alignItems: 'center',
  },
  loadingIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  loadingTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  loadingSubtitle: {
    fontSize: 16,
    color: '#64B5F6',
    marginBottom: 24,
  },
  spinner: {
    marginTop: 8,
  },
  errorContainer: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  errorContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  errorIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  errorTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 12,
  },
  errorMessage: {
    fontSize: 16,
    color: '#94A3B8',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 12,
  },
  errorDetail: {
    fontSize: 12,
    color: '#475569',
    textAlign: 'center',
    marginBottom: 32,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  retryButton: {
    backgroundColor: '#64B5F6',
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 12,
  },
  retryText: {
    color: '#0c0c0c',
    fontSize: 16,
    fontWeight: '600',
  },
});
