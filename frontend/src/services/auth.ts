import { get, post } from './api';
import type {
  User,
  LoginCredentials,
  RegisterStudentData,
  RegisterParentData,
  AuthResponse,
  PasswordResetRequest,
  PasswordResetConfirm,
  PasswordChange,
} from '../types/auth';

// Token storage key
const TOKEN_KEY = 'learntogrow_token';
const USER_KEY = 'learntogrow_user';

/**
 * Store auth token
 */
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Get auth token
 */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Remove auth token
 */
export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Store user data
 */
export function setUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Get stored user data
 */
export function getStoredUser(): User | null {
  const userJson = localStorage.getItem(USER_KEY);
  if (userJson) {
    try {
      return JSON.parse(userJson);
    } catch {
      return null;
    }
  }
  return null;
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return !!getToken();
}

/**
 * Get auth headers for API requests
 */
export function getAuthHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Login user
 */
export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  const response = await post<AuthResponse>('/auth/login', credentials);
  setToken(response.access_token);
  return response;
}

/**
 * Register student account
 */
export async function registerStudent(data: RegisterStudentData): Promise<User> {
  return post<User>('/auth/register/student', data);
}

/**
 * Register parent account
 */
export async function registerParent(data: RegisterParentData): Promise<{ user: User; message: string }> {
  return post('/auth/register/parent', data);
}

/**
 * Get current user info
 */
export async function getCurrentUser(): Promise<User> {
  const user = await get<User>('/auth/me', { headers: getAuthHeaders() });
  setUser(user);
  return user;
}

/**
 * Logout user
 */
export function logout(): void {
  removeToken();
}

/**
 * Request password reset
 */
export async function requestPasswordReset(data: PasswordResetRequest): Promise<{ message: string; token?: string }> {
  return post('/auth/password-reset/request', data);
}

/**
 * Confirm password reset
 */
export async function confirmPasswordReset(data: PasswordResetConfirm): Promise<{ message: string }> {
  return post('/auth/password-reset/confirm', data);
}

/**
 * Change password
 */
export async function changePassword(data: PasswordChange): Promise<{ message: string }> {
  return post('/auth/password/change', data, { headers: getAuthHeaders() });
}
