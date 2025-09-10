/**
 * API Configuration for SecureAI Frontend
 * Handles different environments (development, production, Vercel deployment)
 */

// Get API base URL based on environment
const getApiBaseUrl = (): string => {
  // Check for Vite environment variable (for Vercel deployment)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // Check for deployment on Vercel (same domain deployment)
  if (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')) {
    return `${window.location.protocol}//${window.location.hostname}`;
  }
  
  // Development fallback
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();

// API endpoints
export const API_ENDPOINTS = {
  INTERPRET: `${API_BASE_URL}/api/interpret`,
  PARSE_IMAGE: `${API_BASE_URL}/api/parse-image`,
  PROGRESS: (workflowId: string) => `${API_BASE_URL}/api/progress/${workflowId}`,
  CONVERT_EXECUTE: `${API_BASE_URL}/api/convert-and-execute`,
  HEALTH: `${API_BASE_URL}/health`,
  TEST_EDGES: `${API_BASE_URL}/api/test-edges`
};

console.log('API Configuration:', {
  baseUrl: API_BASE_URL,
  environment: import.meta.env.MODE,
  hostname: typeof window !== 'undefined' ? window.location.hostname : 'server'
});