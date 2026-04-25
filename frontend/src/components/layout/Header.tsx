import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { BookOpen, Menu, X, LogOut } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import type { UserRole } from '../../types/auth'

interface NavItem {
  to: string
  label: string
}

function getNavItems(role: UserRole): NavItem[] {
  switch (role) {
    case 'student':
      return [
        { to: '/student', label: 'Dashboard' },
        { to: '/quiz', label: 'Quiz' },
      ]
    case 'parent':
      return [
        { to: '/parent', label: 'Dashboard' },
        { to: '/parent/link-request', label: 'Request Link' },
      ]
    case 'admin':
      return [
        { to: '/admin', label: 'Dashboard' },
        { to: '/admin/questions', label: 'Questions' },
      ]
  }
}

const roleBadgeStyles: Record<UserRole, string> = {
  student: 'bg-sage-100 text-sage-700',
  parent: 'bg-blue-100 text-blue-700',
  admin: 'bg-coral-100 text-coral-700',
}

const roleLabels: Record<UserRole, string> = {
  student: 'Student',
  parent: 'Parent',
  admin: 'Admin',
}

function RoleBadge({ role }: { role: UserRole }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-display font-medium ${roleBadgeStyles[role]}`}
    >
      {roleLabels[role]}
    </span>
  )
}

export function Header() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const navItems = user ? getNavItems(user.role) : []

  function isActive(to: string): boolean {
    return location.pathname === to
  }

  function handleLogout() {
    logout()
    navigate('/')
    setIsMobileMenuOpen(false)
  }

  function handleMobileNavClick() {
    setIsMobileMenuOpen(false)
  }

  return (
    <header className="sticky top-0 z-50 bg-surface-elevated border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-2 font-display font-semibold text-text text-lg shrink-0"
          >
            <BookOpen className="w-5 h-5 text-sage-600" />
            LearnToGrow
          </Link>

          {/* Desktop Navigation */}
          {user ? (
            <div className="hidden md:flex items-center gap-6">
              <nav className="flex items-center gap-6">
                {navItems.map((item) => (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`font-display text-sm font-medium transition-colors ${
                      isActive(item.to)
                        ? 'text-sage-600'
                        : 'text-text-muted hover:text-text'
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
              <div className="h-6 w-px bg-border" />
              <div className="flex items-center gap-3">
                <span className="font-display text-sm text-text-muted">
                  {user.full_name || user.username}
                </span>
                <RoleBadge role={user.role} />
                <button
                  onClick={handleLogout}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-display font-medium text-text-muted hover:text-coral-600 transition-colors"
                  aria-label="Logout"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            </div>
          ) : (
            <div className="hidden md:flex items-center gap-3">
              <Link
                to="/login"
                className="font-display text-sm font-medium text-text-muted hover:text-text transition-colors"
              >
                Login
              </Link>
              <Link
                to="/register/student"
                className="px-4 py-1.5 bg-sage-600 text-white rounded-xl font-display text-sm font-medium hover:bg-sage-700 transition-colors"
              >
                Register
              </Link>
            </div>
          )}

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 text-text-muted hover:text-text transition-colors"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-border bg-surface-elevated">
          {user ? (
            <>
              <nav className="px-4 py-3 space-y-1">
                {navItems.map((item) => (
                  <Link
                    key={item.to}
                    to={item.to}
                    onClick={handleMobileNavClick}
                    className={`block px-3 py-2 rounded-xl font-display text-sm font-medium transition-colors ${
                      isActive(item.to)
                        ? 'bg-sage-50 text-sage-600'
                        : 'text-text-muted hover:text-text hover:bg-surface-muted'
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
              <div className="px-4 py-3 border-t border-border">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-display text-sm text-text">
                      {user.full_name || user.username}
                    </span>
                    <RoleBadge role={user.role} />
                  </div>
                  <button
                    onClick={handleLogout}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-display font-medium text-coral-600 hover:text-coral-700 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="px-4 py-3 space-y-2">
              <Link
                to="/login"
                onClick={handleMobileNavClick}
                className="block px-3 py-2 rounded-xl font-display text-sm font-medium text-text-muted hover:text-text hover:bg-surface-muted transition-colors text-center"
              >
                Login
              </Link>
              <Link
                to="/register/student"
                onClick={handleMobileNavClick}
                className="block px-4 py-2 bg-sage-600 text-white rounded-xl font-display text-sm font-medium hover:bg-sage-700 transition-colors text-center"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  )
}