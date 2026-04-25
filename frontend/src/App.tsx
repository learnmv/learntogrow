import { Routes, Route, Link } from 'react-router-dom'
import { BookOpen, Play, LogIn, UserPlus } from 'lucide-react'
import { useAuth } from './contexts/AuthContext'
import { ProtectedRoute } from './components/guards/ProtectedRoute'
import { RoleRoute } from './components/guards/RoleRoute'
import { AppLayout } from './components/layout/AppLayout'
import { LoginPage } from './pages/auth/LoginPage'
import { StudentRegistrationPage } from './pages/auth/StudentRegistrationPage'
import { ParentRegistrationPage } from './pages/auth/ParentRegistrationPage'
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage'
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage'
import { StudentDashboard } from './pages/student/StudentDashboard'
import { QuizPage } from './pages/student/QuizPage'
import { ParentDashboard } from './pages/parent/ParentDashboard'
import { ParentLinkRequestPage } from './pages/parent/ParentLinkRequestPage'
import { ChildProgressPage } from './pages/parent/ChildProgressPage'
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage'
import { AdminQuestionManagementPage } from './pages/admin/AdminQuestionManagementPage'

// ── Landing Page ──────────────────────────────────────────────────────

function LandingPage() {
  const { isAuthenticated, user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-surface flex flex-col items-center justify-center gap-8 px-4">
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-sage-100 rounded-full mb-6">
          <BookOpen className="w-4 h-4 text-sage-600" />
          <span className="text-sm font-display font-medium text-sage-700">
            AI-Powered Learning
          </span>
        </div>

        <h1 className="font-display text-6xl font-semibold text-text tracking-tight">
          Learn<span className="text-sage-600">To</span>Grow
        </h1>

        <p className="mt-4 text-lg text-text-muted max-w-md mx-auto">
          {isAuthenticated
            ? `Welcome back! Ready to continue learning?`
            : 'Log in or create an account to start your personalized quiz'}
        </p>
      </div>

      {isAuthenticated && user ? (
        <div className="flex flex-col items-center gap-4">
          <p className="text-text-muted font-display">
            Signed in as <span className="text-sage-700 font-semibold">{user.full_name || user.username}</span>
          </p>
          <div className="flex gap-3">
            <Link
              to={user.role === 'admin' ? '/admin' : user.role === 'parent' ? '/parent' : '/student'}
              className="flex items-center gap-3 px-8 py-4 bg-coral-500 text-white rounded-2xl font-display font-semibold text-lg shadow-lg shadow-coral-200 hover:shadow-xl transition-shadow"
            >
              <Play className="w-5 h-5" />
              Go to Dashboard
            </Link>
            <button
              onClick={logout}
              className="px-6 py-4 bg-surface-elevated border border-border text-text-muted rounded-2xl font-display font-medium hover:text-text transition-colors"
            >
              Log out
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-6">
          <div className="text-center max-w-md">
            <p className="text-text-muted font-body">
              Create a free account to track your progress and see your strengths and weaknesses.
            </p>
          </div>
          <div className="flex gap-3">
            <Link
              to="/login"
              className="flex items-center gap-2 px-6 py-3 bg-sage-600 text-white rounded-xl font-display font-semibold hover:bg-sage-700 transition-colors"
            >
              <LogIn className="w-5 h-5" />
              Log in
            </Link>
            <Link
              to="/register/student"
              className="flex items-center gap-2 px-6 py-3 bg-surface-elevated border border-border text-text-muted rounded-xl font-display font-medium hover:text-text transition-colors"
            >
              <UserPlus className="w-5 h-5" />
              Sign up
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

// ── NotFound Page ──────────────────────────────────────────────────────

function NotFoundPage() {
  return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-display font-bold text-sage-300">404</h1>
        <p className="mt-2 text-xl font-display font-semibold text-text">Page not found</p>
        <p className="mt-2 text-text-muted">The page you are looking for does not exist.</p>
        <Link
          to="/"
          className="mt-6 inline-block px-6 py-3 bg-sage-600 text-white rounded-xl font-display font-semibold hover:bg-sage-700 transition-colors"
        >
          Go home
        </Link>
      </div>
    </div>
  )
}

// ── Route definitions ─────────────────────────────────────────────────

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register/student" element={<StudentRegistrationPage />} />
      <Route path="/register/parent" element={<ParentRegistrationPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />

      {/* Protected routes (any authenticated user) */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/quiz" element={<QuizPage />} />
        </Route>
      </Route>

      {/* Student routes */}
      <Route element={<RoleRoute allowedRoles={['student']} />}>
        <Route element={<AppLayout />}>
          <Route path="/student" element={<StudentDashboard />} />
        </Route>
      </Route>

      {/* Parent routes */}
      <Route element={<RoleRoute allowedRoles={['parent']} />}>
        <Route element={<AppLayout />}>
          <Route path="/parent" element={<ParentDashboard />} />
          <Route path="/parent/link-request" element={<ParentLinkRequestPage />} />
          <Route path="/parent/child/:studentId" element={<ChildProgressPage />} />
        </Route>
      </Route>

      {/* Admin routes */}
      <Route element={<RoleRoute allowedRoles={['admin']} />}>
        <Route element={<AppLayout />}>
          <Route path="/admin" element={<AdminDashboardPage />} />
          <Route path="/admin/questions" element={<AdminQuestionManagementPage />} />
        </Route>
      </Route>

      {/* Catch-all 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App