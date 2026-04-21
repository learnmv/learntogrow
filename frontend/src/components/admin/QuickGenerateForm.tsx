import { useState } from 'react';
import { motion } from 'framer-motion';
import { Zap, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { getSmartFillSuggestions, generateQuestions } from '../../services/admin';
import type { SmartFillSuggestion } from '../../types/admin';

type FillMode = 'gaps' | 'struggling' | 'balanced';

export function QuickGenerateForm() {
  const [mode, setMode] = useState<FillMode>('gaps');
  const [subjectId, setSubjectId] = useState<number | ''>(1); // Default to Math
  const [gradeId, setGradeId] = useState<number | ''>('');
  const [maxStandards, setMaxStandards] = useState(10);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<SmartFillSuggestion[]>([]);
  const [generating, setGenerating] = useState(false);
  const [results, setResults] = useState<{ completed: number; created: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadSuggestions() {
    try {
      setLoading(true);
      setError(null);
      setResults(null);
      const data = await getSmartFillSuggestions({
        subject_id: Number(subjectId),
        grade_id: gradeId ? Number(gradeId) : undefined,
        fill_mode: mode,
        max_standards: maxStandards,
      });
      setSuggestions(data.suggestions);
    } catch (err: any) {
      setError(err.message || 'Failed to load suggestions');
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerate() {
    try {
      setGenerating(true);
      setError(null);
      const standardIds = suggestions.map((s) => s.standard_id);
      const response = await generateQuestions({
        subject_id: Number(subjectId),
        grade_id: gradeId ? Number(gradeId) : undefined,
        standard_ids: standardIds,
        questions_per_standard: 2,
        question_type: 'multiple_choice',
      });
      setResults({
        completed: response.standards_completed,
        created: response.questions_created,
      });
    } catch (err: any) {
      setError(err.message || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  }

  const modeDescriptions: Record<FillMode, { title: string; description: string }> = {
    gaps: {
      title: 'Fill Gaps',
      description: 'Finds standards with the fewest questions and generates more for them.',
    },
    struggling: {
      title: 'Help Struggling Students',
      description: 'Focuses on standards where students have low accuracy. Generates easier questions.',
    },
    balanced: {
      title: 'Balanced Fill',
      description: 'Combines coverage gaps and student struggling areas for a balanced approach.',
    },
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Mode Selector */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
        <h3 className="font-display font-semibold text-text">Quick Generate Mode</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {(Object.keys(modeDescriptions) as FillMode[]).map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); setSuggestions([]); setResults(null); }}
              className={`p-4 rounded-2xl border text-left transition-all ${
                mode === m
                  ? 'border-sage-400 bg-sage-50 ring-2 ring-sage-300'
                  : 'border-border bg-surface-elevated hover:border-sage-200'
              }`}
            >
              <p className={`font-display font-semibold ${mode === m ? 'text-sage-700' : 'text-text'}`}>
                {modeDescriptions[m].title}
              </p>
              <p className="text-xs text-text-muted mt-1">{modeDescriptions[m].description}</p>
            </button>
          ))}
        </div>
      </motion.div>

      {/* Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-surface-elevated rounded-2xl p-5 border border-border space-y-4"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-text-muted mb-1">Subject</label>
            <select
              value={subjectId}
              onChange={(e) => setSubjectId(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-xl border border-border bg-white text-sm focus:outline-none focus:ring-2 focus:ring-sage-300"
            >
              <option value={1}>Mathematics</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-text-muted mb-1">Grade (optional)</label>
            <select
              value={gradeId}
              onChange={(e) => setGradeId(e.target.value ? Number(e.target.value) : '')}
              className="w-full px-3 py-2 rounded-xl border border-border bg-white text-sm focus:outline-none focus:ring-2 focus:ring-sage-300"
            >
              <option value="">All Grades</option>
              <option value={1}>Grade 6</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-text-muted mb-1">Max Standards: {maxStandards}</label>
            <input
              type="range"
              min={1}
              max={30}
              value={maxStandards}
              onChange={(e) => setMaxStandards(Number(e.target.value))}
              className="w-full accent-sage-600"
            />
          </div>
        </div>

        <button
          onClick={loadSuggestions}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 bg-sage-600 text-white rounded-xl font-medium hover:bg-sage-700 transition-colors disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
          Find Gaps
        </button>
      </motion.div>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-3"
        >
          <div className="flex items-center justify-between">
            <h3 className="font-display font-semibold text-text">Suggested Standards ({suggestions.length})</h3>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex items-center gap-2 px-4 py-2 bg-coral-500 text-white rounded-xl font-medium hover:bg-coral-600 transition-colors disabled:opacity-50 text-sm"
            >
              {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              Generate Questions
            </button>
          </div>

          <div className="space-y-2">
            {suggestions.map((s) => (
              <motion.div
                key={s.standard_id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-surface-elevated rounded-xl p-4 border border-border"
              >
                <div className="flex items-start gap-3">
                  <div className="p-1.5 bg-sage-100 rounded-lg shrink-0 mt-0.5">
                    <AlertCircle className="w-4 h-4 text-sage-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-display font-medium text-text">{s.standard_code}</p>
                    <p className="text-sm text-text-muted">{s.standard_description}</p>
                    <p className="text-xs text-sage-600 mt-1 font-medium">{s.reason}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-xs text-text-muted">{s.suggested_count} questions</span>
                    <div className="text-xs text-text-muted">Difficulty: {s.suggested_difficulty.toFixed(1)}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {suggestions.length === 0 && !loading && !results && (
        <div className="text-center py-8 text-text-muted text-sm">
          Click "Find Gaps" to see which standards need more questions.
        </div>
      )}

      {results && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-sage-50 border border-sage-200 rounded-2xl p-6 text-center"
        >
          <CheckCircle className="w-10 h-10 text-sage-600 mx-auto mb-3" />
          <p className="font-display font-semibold text-text text-lg">Generation Complete!</p>
          <p className="text-text-muted">
            {results.completed} standards processed · {results.created} questions created
          </p>
        </motion.div>
      )}

      {error && (
        <div className="bg-coral-50 border border-coral-200 rounded-xl p-4 flex items-center gap-2 text-coral-700 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}
    </div>
  );
}
