import './index.css'
import { SubjectSelector } from './components/ui/SubjectSelector'

function App() {
  return (
    <div className="min-h-screen bg-surface flex flex-col items-center justify-center gap-8">
      <h1 className="font-display text-6xl font-semibold text-text tracking-tight">
        LearnToGrow
      </h1>
      <SubjectSelector />
    </div>
  )
}

export default App
