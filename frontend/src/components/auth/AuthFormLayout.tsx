import { motion } from 'framer-motion'
import { BookOpen } from 'lucide-react'

interface AuthFormLayoutProps {
  title: string
  subtitle?: string
  children: React.ReactNode
  footer?: React.ReactNode
}

export function AuthFormLayout({ title, subtitle, children, footer }: AuthFormLayoutProps) {
  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="bg-surface-elevated rounded-3xl p-8 shadow-lg w-full max-w-md"
      >
        {/* Brand */}
        <div className="flex items-center justify-center gap-2 mb-6">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-sage-100 rounded-full">
            <BookOpen className="w-4 h-4 text-sage-600" />
            <span className="text-sm font-display font-medium text-sage-700">
              Learn<span className="text-sage-600">To</span>Grow
            </span>
          </div>
        </div>

        {/* Title */}
        <h1 className="font-display text-2xl font-semibold text-text text-center">
          {title}
        </h1>

        {/* Subtitle */}
        {subtitle && (
          <p className="text-text-muted mt-1 text-center">{subtitle}</p>
        )}

        {/* Content */}
        <div className="mt-6">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="mt-6 pt-6 border-t border-border text-center text-sm text-text-muted">
            {footer}
          </div>
        )}
      </motion.div>
    </div>
  )
}