import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from 'sonner'
import './index.css'
import App from './App.tsx'
import { loadConfig, isDebugEnabled } from './lib/config.ts'
import { AuthProvider } from './contexts/AuthContext.tsx'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
})

// Load config before rendering with error handling
async function init() {
  try {
    await loadConfig()
  } catch (error) {
    console.error('Failed to load configuration:', error)
    createRoot(document.getElementById('root')!).render(
      <div className="min-h-screen bg-surface flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <h1 className="text-2xl font-display font-bold text-red-600 mb-4">
            Configuration Error
          </h1>
          <p className="text-text-muted mb-2">
            The application failed to load its runtime configuration.
          </p>
          <p className="text-sm text-text-muted/70">
            {error instanceof Error ? error.message : String(error)}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-6 px-6 py-3 bg-sage-600 text-white rounded-xl font-display font-semibold hover:bg-sage-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>,
    )
    return
  }

  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Toaster position="top-right" richColors />
          <BrowserRouter>
            <App />
            {isDebugEnabled() && <ReactQueryDevtools initialIsOpen={false} />}
          </BrowserRouter>
        </AuthProvider>
      </QueryClientProvider>
    </StrictMode>,
  )
}

init()