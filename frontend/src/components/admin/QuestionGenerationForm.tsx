import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, Play, CheckCircle, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { generateQuestions } from '../../services/admin';
import { fetchSubjects } from '../../services/standards';
import { fetchGradesBySubject } from '../../services/standards';
import { fetchDomainsByGrade } from '../../services/standards';
import { fetchStandards } from '../../services/standards';
import type { Subject, Grade, Domain, Standard } from '../../types/standards';
import type { QuestionGenerateRequest } from '../../types/admin';

interface QuestionGenerationFormProps {
  onSuccess?: () => void;
}

export function QuestionGenerationForm({ onSuccess }: QuestionGenerationFormProps) {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [grades, setGrades] = useState<Grade[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [standards, setStandards] = useState<Standard[]>([]);

  const [selectedSubject, setSelectedSubject] = useState<number | ''>('');
  const [selectedGrade, setSelectedGrade] = useState<number | ''>('');
  const [selectedDomains, setSelectedDomains] = useState<number[]>([]);
  const [selectedStandards, setSelectedStandards] = useState<number[]>([]);

  const [questionsPerStandard, setQuestionsPerStandard] = useState(1);
  const [questionType, setQuestionType] = useState<'multiple_choice' | 'open_ended'>('multiple_choice');
  const [difficultyMin, setDifficultyMin] = useState<number | ''>('');
  const [difficultyMax, setDifficultyMax] = useState<number | ''>('');
  const [timeout, setTimeout] = useState(300);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    success: boolean;
    message: string;
    details?: {
      standards_matched: number;
      standards_completed: number;
      standards_failed: number;
      questions_created: number;
      errors: string[] | null;
    };
  } | null>(null);

  // Load subjects on mount
  useEffect(() => {
    loadSubjects();
  }, []);

  // Load grades when subject changes
  useEffect(() => {
    if (selectedSubject) {
      loadGrades(selectedSubject);
      setSelectedGrade('');
      setSelectedDomains([]);
      setSelectedStandards([]);
    }
  }, [selectedSubject]);

  // Load domains when grade changes
  useEffect(() => {
    if (selectedGrade) {
      loadDomains(selectedGrade);
      setSelectedDomains([]);
      setSelectedStandards([]);
    }
  }, [selectedGrade]);

  // Load standards when subject/grade/domains change
  useEffect(() => {
    if (selectedSubject && selectedGrade) {
      loadStandards();
    }
  }, [selectedSubject, selectedGrade, selectedDomains]);

  async function loadSubjects() {
    try {
      const data = await fetchSubjects();
      setSubjects(data);
    } catch (err) {
      console.error('Failed to load subjects:', err);
    }
  }

  async function loadGrades(subjectId: number) {
    try {
      const data = await fetchGradesBySubject(subjectId);
      setGrades(data);
    } catch (err) {
      console.error('Failed to load grades:', err);
    }
  }

  async function loadDomains(gradeId: number) {
    try {
      const data = await fetchDomainsByGrade(gradeId);
      setDomains(data);
    } catch (err) {
      console.error('Failed to load domains:', err);
    }
  }

  async function loadStandards() {
    try {
      const filters: { subject_id?: number; grade_id?: number; domain_ids?: number[] } = {
        subject_id: selectedSubject as number,
        grade_id: selectedGrade as number,
      };

      if (selectedDomains.length > 0) {
        filters.domain_ids = selectedDomains;
      }

      const data = await fetchStandards(filters);
      setStandards(data);
    } catch (err) {
      console.error('Failed to load standards:', err);
    }
  }

  function handleDomainToggle(domainId: number) {
    setSelectedDomains(prev =>
      prev.includes(domainId)
        ? prev.filter(id => id !== domainId)
        : [...prev, domainId]
    );
  }

  function handleStandardToggle(standardId: number) {
    setSelectedStandards(prev =>
      prev.includes(standardId)
        ? prev.filter(id => id !== standardId)
        : [...prev, standardId]
    );
  }

  function selectAllStandards() {
    setSelectedStandards(standards.map(s => s.id));
  }

  function clearAllStandards() {
    setSelectedStandards([]);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!selectedSubject || !selectedGrade) {
      setResult({
        success: false,
        message: 'Please select a subject and grade',
      });
      return;
    }

    const request: QuestionGenerateRequest = {
      subject_id: selectedSubject as number,
      grade_id: selectedGrade ? Number(selectedGrade) : undefined,
      domain_ids: selectedDomains.length > 0 ? selectedDomains : undefined,
      standard_ids: selectedStandards.length > 0 ? selectedStandards : undefined,
      difficulty_min: difficultyMin !== '' ? Number(difficultyMin) : undefined,
      difficulty_max: difficultyMax !== '' ? Number(difficultyMax) : undefined,
      questions_per_standard: questionsPerStandard,
      question_type: questionType,
      timeout,
    };

    setLoading(true);
    setResult(null);

    try {
      const response = await generateQuestions(request);
      setResult({
        success: response.questions_created > 0,
        message: response.message,
        details: {
          standards_matched: response.standards_matched,
          standards_completed: response.standards_completed,
          standards_failed: response.standards_failed,
          questions_created: response.questions_created,
          errors: response.errors,
        },
      });

      if (response.questions_created > 0) {
        toast.success(`Generated ${response.questions_created} question(s)`, {
          description: `${response.standards_completed} standard(s) completed`,
        });
        if (onSuccess) onSuccess();
      } else {
        toast.error('No questions generated', {
          description: response.message || 'No matching standards found',
        });
      }
    } catch (err: any) {
      const message = err.message || 'Failed to generate questions';
      setResult({
        success: false,
        message,
      });
      toast.error('Failed to generate questions', {
        description: message,
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-surface-elevated rounded-2xl p-6 shadow-sm border border-border">
      <h2 className="text-xl font-display font-semibold text-text mb-6">Generate Questions</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Subject Selection */}
        <div>
          <label className="block text-sm font-medium text-text mb-2">Subject *</label>
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value === '' ? '' : Number(e.target.value))}
            className="w-full px-4 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 focus:border-transparent"
            required
          >
            <option value="">Select a subject</option>
            {subjects.map(subject => (
              <option key={subject.id} value={subject.id}>{subject.name}</option>
            ))}
          </select>
        </div>

        {/* Grade Selection */}
        <div>
          <label className="block text-sm font-medium text-text mb-2">Grade *</label>
          <select
            value={selectedGrade}
            onChange={(e) => setSelectedGrade(e.target.value === '' ? '' : Number(e.target.value))}
            className="w-full px-4 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 focus:border-transparent"
            required
            disabled={!selectedSubject}
          >
            <option value="">Select a grade</option>
            {grades.map(grade => (
              <option key={grade.id} value={grade.id}>
                Grade {grade.level}
              </option>
            ))}
          </select>
        </div>

        {/* Domain Filter */}
        {domains.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-text mb-2">Filter by Domain (optional)</label>
            <div className="flex flex-wrap gap-2">
              {domains.map(domain => (
                <button
                  key={domain.id}
                  type="button"
                  onClick={() => handleDomainToggle(domain.id)}
                  className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                    selectedDomains.includes(domain.id)
                      ? 'bg-sage-100 border-sage-500 text-sage-700'
                      : 'bg-surface border-border text-text-muted hover:border-sage-300'
                  }`}
                >
                  {domain.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Standards Selection */}
        {standards.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-text">
                Standards ({selectedStandards.length} selected)
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={selectAllStandards}
                  className="text-xs text-sage-600 hover:text-sage-700"
                >
                  Select All
                </button>
                <button
                  type="button"
                  onClick={clearAllStandards}
                  className="text-xs text-text-muted hover:text-text"
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="max-h-48 overflow-y-auto border border-border rounded-xl p-3 space-y-1">
              {standards.map(standard => (
                <label
                  key={standard.id}
                  className="flex items-center gap-3 p-2 hover:bg-sage-50 rounded-lg cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedStandards.includes(standard.id)}
                    onChange={() => handleStandardToggle(standard.id)}
                    className="w-4 h-4 text-sage-600 border-border rounded focus:ring-sage-500"
                  />
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-text">{standard.code}</span>
                    <span className="text-sm text-text-muted ml-2 truncate">
                      {standard.description.substring(0, 60)}...
                    </span>
                  </div>
                </label>
              ))}
            </div>
            <p className="text-xs text-text-muted mt-1">
              If none selected, questions will be generated for all matching standards
            </p>
          </div>
        )}

        {/* Question Settings */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-text mb-2">Questions per Standard</label>
            <input
              type="number"
              min={1}
              max={10}
              value={questionsPerStandard}
              onChange={(e) => setQuestionsPerStandard(Number(e.target.value))}
              className="w-full px-4 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-2">Question Type</label>
            <select
              value={questionType}
              onChange={(e) => setQuestionType(e.target.value as 'multiple_choice' | 'open_ended')}
              className="w-full px-4 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 focus:border-transparent"
            >
              <option value="multiple_choice">Multiple Choice</option>
              <option value="open_ended">Open Ended</option>
            </select>
          </div>
        </div>

        {/* Difficulty Range */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-text mb-2">Min Difficulty (0-1)</label>
            <input
              type="number"
              min={0}
              max={1}
              step={0.1}
              value={difficultyMin}
              onChange={(e) => setDifficultyMin(e.target.value ? Number(e.target.value) : '')}
              className="w-full px-4 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-2">Max Difficulty (0-1)</label>
            <input
              type="number"
              min={0}
              max={1}
              step={0.1}
              value={difficultyMax}
              onChange={(e) => setDifficultyMax(e.target.value ? Number(e.target.value) : '')}
              className="w-full px-4 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Timeout */}
        <div>
          <label className="block text-sm font-medium text-text mb-2">Timeout (seconds)</label>
          <input
            type="number"
            min={30}
            max={600}
            value={timeout}
            onChange={(e) => setTimeout(Number(e.target.value))}
            className="w-full px-4 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 focus:border-transparent"
          />
        </div>

        {/* Submit Button */}
        <motion.button
          type="submit"
          disabled={loading || !selectedSubject || !selectedGrade}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-coral-500 text-white rounded-xl font-display font-semibold hover:bg-coral-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Generate Questions
            </>
          )}
        </motion.button>
      </form>

      {/* Result */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`mt-6 p-4 rounded-xl ${
              result.success
                ? 'bg-green-50 border border-green-200'
                : 'bg-coral-50 border border-coral-200'
            }`}
          >
            <div className="flex items-start gap-3">
              {result.success ? (
                <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              ) : (
                <AlertCircle className="w-5 h-5 text-coral-600 mt-0.5" />
              )}
              <div>
                <p className={`font-medium ${result.success ? 'text-green-700' : 'text-coral-700'}`}>
                  {result.message}
                </p>
                {result.details && (
                  <div className="mt-2 text-sm text-text-muted">
                    <p>Standards matched: {result.details.standards_matched}</p>
                    <p>Completed: {result.details.standards_completed}</p>
                    <p>Failed: {result.details.standards_failed}</p>
                    <p>Questions created: {result.details.questions_created}</p>
                    {result.details.errors && result.details.errors.length > 0 && (
                      <div className="mt-2">
                        <p className="text-coral-600 font-medium">Errors:</p>
                        <ul className="list-disc list-inside text-xs">
                          {result.details.errors.map((error, i) => (
                            <li key={i}>{error}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
