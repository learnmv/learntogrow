export type UserRole = 'student' | 'parent' | 'admin';

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterStudentData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface RegisterParentData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  student_email_or_username: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  new_password: string;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
}
