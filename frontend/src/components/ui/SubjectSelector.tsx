import { useState, useEffect } from 'react'
import { fetchSubjects, fetchGrades } from '../../services/standards'
import type { Subject, Grade } from '../../types/standards'

interface SubjectSelectorProps {
  onGradeSelect?: (subjectId: string, gradeId: string) => void
}

export function SubjectSelector({ onGradeSelect }: SubjectSelectorProps) {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [grades, setGrades] = useState<Grade[]>([])
  const [selectedSubject, setSelectedSubject] = useState<string>('')
  const [selectedGrade, setSelectedGrade] = useState<string>('')
  const [loadingSubjects, setLoadingSubjects] = useState(true)
  const [loadingGrades, setLoadingGrades] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load subjects on mount
  useEffect(() => {
    async function loadSubjects() {
      try {
        const data = await fetchSubjects()
        setSubjects(data)
        setError(null)
      } catch (err) {
        setError('Failed to load subjects')
      } finally {
        setLoadingSubjects(false)
      }
    }

    loadSubjects()
  }, [])

  // Load grades when subject changes
  useEffect(() => {
    if (!selectedSubject) {
      setGrades([])
      setSelectedGrade('')
      return
    }

    async function loadGrades() {
      setLoadingGrades(true)
      try {
        const data = await fetchGrades(parseInt(selectedSubject))
        setGrades(data)
        setError(null)
      } catch (err) {
        setError('Failed to load grades')
      } finally {
        setLoadingGrades(false)
      }
    }

    loadGrades()
  }, [selectedSubject])

  // Notify parent when grade is selected
  useEffect(() => {
    if (selectedSubject && selectedGrade && onGradeSelect) {
      onGradeSelect(selectedSubject, selectedGrade)
    }
  }, [selectedSubject, selectedGrade, onGradeSelect])

  if (loadingSubjects) {
    return (
      <div className="w-72 space-y-4">
        <div>
          <label className="block font-display font-medium text-text mb-2">
            Subject
          </label>
          <div className="w-full h-12 bg-surface-muted rounded-xl animate-pulse" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-72">
        <label className="block font-display font-medium text-text mb-2">
          Subject
        </label>
        <div className="text-coral-600 text-sm">{error}</div>
      </div>
    )
  }

  const selectStyles = {
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%236b6a69' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 12px center',
    backgroundSize: '20px',
  }

  return (
    <div className="w-72 space-y-4">
      {/* Subject Dropdown */}
      <div>
        <label className="block font-display font-medium text-text mb-2">
          Subject
        </label>
        <select
          value={selectedSubject}
          onChange={(e) => {
            setSelectedSubject(e.target.value)
            setSelectedGrade('')
          }}
          className="w-full h-12 px-4 bg-surface-elevated border border-border rounded-xl font-body text-text focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent cursor-pointer appearance-none"
          style={selectStyles}
        >
          <option value="">Select a subject...</option>
          {subjects.map((subject) => (
            <option key={subject.id} value={subject.id}>
              {subject.name}
            </option>
          ))}
        </select>
      </div>

      {/* Grades Dropdown - shown when subject is selected */}
      {selectedSubject && (
        <div>
          <label className="block font-display font-medium text-text mb-2">
            Grades
          </label>
          {loadingGrades ? (
            <div className="w-full h-12 bg-surface-muted rounded-xl animate-pulse" />
          ) : (
            <select
              value={selectedGrade}
              onChange={(e) => setSelectedGrade(e.target.value)}
              className="w-full h-12 px-4 bg-surface-elevated border border-border rounded-xl font-body text-text focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent cursor-pointer appearance-none"
              style={selectStyles}
            >
              <option value="">Select a grade...</option>
              {grades.map((grade) => (
                <option key={grade.id} value={grade.id}>
                  {grade.display_name}
                </option>
              ))}
            </select>
          )}
        </div>
      )}
    </div>
  )
}
