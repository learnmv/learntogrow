import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play, Loader2, CheckCircle, AlertCircle, Zap, RefreshCw,
  ChevronDown, ChevronUp, Clock, Box, List, ShieldCheck, Layers, Gauge,
} from 'lucide-react';
import { toast } from 'sonner';
import {
  createGenerationJob,
  getGenerationJob,
  listGenerationJobs,
  retryFailedStandards,
  cancelGenerationJob,
  getSmartFillSuggestions,
} from '../../services/admin';
import { fetchSubjects, fetchGradesBySubject, fetchStandards } from '../../services/standards';
import type { Subject, Grade, Standard } from '../../types/standards';
import type {
  GenerationJob,
  CreateGenerationJobRequest,
  SmartFillRequest,
  SmartFillSuggestion,
} from '../../types/admin';

type GenMode =
  | 'custom'
  | 'smart-gaps'
  | 'smart-struggling'
  | 'smart-balanced'
  | 'smart-difficulty'
  | 'smart-diagrams';
type QualityMode = 'reviewed' | 'quality';
type DisplayStandard = Pick<Standard, 'id' | 'code' | 'description'>;

const POLL_INTERVAL = 2000;
const TERMINAL_STATUSES = new Set(['completed', 'failed', 'cancelled']);
const MAX_SMART_STANDARDS = 10;

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export function QuestionGenerationPanel() {
  // -- Curriculum state --
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [grades, setGrades] = useState<Grade[]>([]);
  const [standards, setStandards] = useState<Standard[]>([]);

  const [selectedSubject, setSelectedSubject] = useState<number | ''>('');
  const [selectedGrade, setSelectedGrade] = useState<number | ''>('');
  const [selectedStandards, setSelectedStandards] = useState<number[]>([]);

  // -- Settings --
  const [mode, setMode] = useState<GenMode>('custom');
  const [questionsPerStandard, setQuestionsPerStandard] = useState(1);
  const [questionType, setQuestionType] = useState<'multiple_choice' | 'open_ended'>('multiple_choice');
  const [timeout, setTimeout] = useState(300);
  const [qualityMode, setQualityMode] = useState<QualityMode>('reviewed');
  const [candidateCount, setCandidateCount] = useState(3);
  const [repairAttempts, setRepairAttempts] = useState(0);
  const [minReviewScore, setMinReviewScore] = useState(0.75);

  // -- Job state --
  const [activeJob, setActiveJob] = useState<GenerationJob | null>(null);
  const [recentJobs, setRecentJobs] = useState<GenerationJob[]>([]);
  const [jobListOpen, setJobListOpen] = useState(false);

  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<SmartFillSuggestion[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const displayStandards: DisplayStandard[] = mode === 'custom'
    ? standards
    : suggestions.map((s) => ({
      id: s.standard_id,
      code: s.standard_code,
      description: s.standard_description,
    }));

  // -- Load subjects on mount --
  useEffect(() => {
    fetchSubjects().then(setSubjects).catch(console.error);
    loadRecentJobs();
  }, []);

  // -- Load grades when subject changes --
  useEffect(() => {
    if (selectedSubject) {
      fetchGradesBySubject(selectedSubject).then(setGrades).catch(console.error);
      setSelectedGrade('');
      setSelectedStandards([]);
      setStandards([]);
    }
  }, [selectedSubject]);

  // -- Load standards when subject/grade changes --
  useEffect(() => {
    if (selectedSubject && selectedGrade) {
      fetchStandards({ subject_id: selectedSubject, grade_id: selectedGrade })
        .then(setStandards)
        .catch(console.error);
    }
  }, [selectedSubject, selectedGrade]);

  const loadSuggestions = useCallback(async () => {
    if (!selectedSubject) return;
    const fillMode = mode.replace('smart-', '') as SmartFillRequest['fill_mode'];
    try {
      setSuggestionsLoading(true);
      const res = await getSmartFillSuggestions({
        subject_id: selectedSubject,
        grade_id: selectedGrade ? Number(selectedGrade) : undefined,
        fill_mode: fillMode,
        max_standards: MAX_SMART_STANDARDS,
      });
      setSuggestions(res.suggestions);
      setSelectedStandards(res.suggestions.map((s) => s.standard_id));
    } catch (err: unknown) {
      toast.error('Failed to load suggestions', { description: getErrorMessage(err) });
    } finally {
      setSuggestionsLoading(false);
    }
  }, [mode, selectedGrade, selectedSubject]);

  // -- Load suggestions when smart mode is selected --
  useEffect(() => {
    if (mode.startsWith('smart-') && selectedSubject) {
      loadSuggestions();
    } else {
      setSuggestions([]);
      setSelectedStandards([]);
    }
  }, [loadSuggestions, mode, selectedSubject]);

  async function loadRecentJobs() {
    try {
      const jobs = await listGenerationJobs();
      setRecentJobs(jobs.slice(0, 10));
    } catch (err) {
      console.error('Failed to load jobs', err);
    }
  }

  // -- Polling for active job --
  const startPolling = useCallback((jobId: number) => {
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      try {
        const job = await getGenerationJob(jobId);
        setActiveJob(job);
        setRecentJobs((prev) => {
          const filtered = prev.filter((j) => j.id !== jobId);
          return [job, ...filtered].slice(0, 10);
        });

        if (TERMINAL_STATUSES.has(job.status)) {
          if (pollRef.current) clearInterval(pollRef.current);
          if (job.status === 'completed') {
            toast.success('Generation complete', {
              description: `${job.questions_created} questions created across ${job.completed_standards} standards`,
            });
          } else if (job.status === 'failed') {
            toast.error('Generation finished with failures', {
              description: `${job.failed_standards} standards failed`,
            });
          }
        }
      } catch (err) {
        console.error('Poll error', err);
      }
    }, POLL_INTERVAL);
  }, []);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  // -- Standard selection helpers --
  function toggleStandard(id: number) {
    setSelectedStandards((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  function selectAll() {
    setSelectedStandards(standards.map((s) => s.id));
  }

  function clearAll() {
    setSelectedStandards([]);
  }

  // -- Submit --
  async function handleStart() {
    if (!selectedSubject || !selectedGrade) {
      toast.error('Please select a subject and grade');
      return;
    }

    const standardIds =
      mode.startsWith('smart-') && suggestions.length > 0
        ? suggestions.map((s) => s.standard_id)
        : selectedStandards;

    if (standardIds.length === 0) {
      toast.error('Please select at least one standard');
      return;
    }

    const request: CreateGenerationJobRequest = {
      standard_ids: standardIds,
      questions_per_standard: questionsPerStandard,
      question_type: questionType,
      subject_id: Number(selectedSubject),
      grade_id: selectedGrade ? Number(selectedGrade) : undefined,
      timeout: timeout,
      quality_mode: qualityMode,
      candidate_count: qualityMode === 'quality' ? candidateCount : 1,
      max_repair_attempts: repairAttempts,
      min_review_score: minReviewScore,
    };

    setLoading(true);
    try {
      const job = await createGenerationJob(request);
      setActiveJob(job);
      setRecentJobs((prev) => [job, ...prev].slice(0, 10));
      toast.success('Generation started', {
        description: `Job #${job.id}: ${job.total_standards} standards queued`,
      });
      startPolling(job.id);
    } catch (err: unknown) {
      toast.error('Failed to start generation', { description: getErrorMessage(err) });
    } finally {
      setLoading(false);
    }
  }

  async function handleRetry(jobId: number) {
    try {
      const job = await retryFailedStandards(jobId);
      setActiveJob(job);
      setRecentJobs((prev) => [job, ...prev].slice(0, 10));
      toast.success('Retry started', { description: `Job #${job.id}` });
      startPolling(job.id);
    } catch (err: unknown) {
      toast.error('Retry failed', { description: getErrorMessage(err) });
    }
  }

  async function handleCancel(jobId: number) {
    try {
      await cancelGenerationJob(jobId);
      toast.success('Job cancelled');
      const job = await getGenerationJob(jobId);
      setActiveJob(job);
    } catch (err: unknown) {
      toast.error('Cancel failed', { description: getErrorMessage(err) });
    }
  }

  // -- Render helpers --
  const isRunning = !!activeJob && !TERMINAL_STATUSES.has(activeJob.status);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left column: controls */}
      <div className="lg:col-span-2 space-y-6">
        {/* Mode selector */}
        <div className="bg-surface-elevated rounded-2xl p-5 shadow-sm border border-border">
          <h3 className="text-sm font-display font-semibold text-text mb-3">Generation Mode</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {[
              { key: 'custom' as GenMode, label: 'Custom', icon: Box },
              { key: 'smart-gaps' as GenMode, label: 'Fill Gaps', icon: Zap },
              { key: 'smart-struggling' as GenMode, label: 'Struggling', icon: AlertCircle },
              { key: 'smart-balanced' as GenMode, label: 'Balanced', icon: List },
              { key: 'smart-difficulty' as GenMode, label: 'Difficulty', icon: Gauge },
              { key: 'smart-diagrams' as GenMode, label: 'Diagrams', icon: Layers },
            ].map((m) => (
              <button
                key={m.key}
                onClick={() => setMode(m.key)}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-display font-medium transition-all border ${
                  mode === m.key
                    ? 'bg-sage-100 border-sage-500 text-sage-700'
                    : 'bg-surface border-border text-text-muted hover:border-sage-300'
                }`}
              >
                <m.icon className="w-4 h-4" />
                {m.label}
              </button>
            ))}
          </div>
        </div>

        {/* Curriculum filters */}
        <div className="bg-surface-elevated rounded-2xl p-5 shadow-sm border border-border space-y-4">
          <h3 className="text-sm font-display font-semibold text-text">Curriculum</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-text-muted mb-1.5">Subject *</label>
              <select
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(Number(e.target.value) || '')}
                className="w-full px-3 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 text-sm"
              >
                <option value="">Select...</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1.5">Grade *</label>
              <select
                value={selectedGrade}
                onChange={(e) => setSelectedGrade(Number(e.target.value) || '')}
                disabled={!selectedSubject}
                className="w-full px-3 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 text-sm disabled:opacity-50"
              >
                <option value="">Select...</option>
                {grades.map((g) => (
                  <option key={g.id} value={g.id}>Grade {g.level}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Standards selection */}
        <div className="bg-surface-elevated rounded-2xl p-5 shadow-sm border border-border">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-display font-semibold text-text">
              Standards ({selectedStandards.length} selected)
            </h3>
            {mode === 'custom' && (
              <div className="flex gap-2">
                <button onClick={selectAll} className="text-xs text-sage-600 hover:text-sage-700 font-medium">
                  Select all
                </button>
                <button onClick={clearAll} className="text-xs text-text-muted hover:text-text font-medium">
                  Clear
                </button>
              </div>
            )}
          </div>

          {mode.startsWith('smart-') && suggestionsLoading && (
            <div className="flex items-center gap-2 py-8 text-text-muted text-sm">
              <Loader2 className="w-4 h-4 animate-spin" />
              Finding gaps...
            </div>
          )}

          {mode.startsWith('smart-') && !suggestionsLoading && suggestions.length === 0 && (
            <div className="text-center py-8 text-text-muted text-sm">
              No suggestions found. Try a different grade or mode.
            </div>
          )}

          {mode === 'custom' && standards.length === 0 && (
            <div className="text-center py-8 text-text-muted text-sm">
              Select a subject and grade to load standards.
            </div>
          )}

          {displayStandards.length > 0 && (
            <div className="max-h-56 overflow-y-auto border border-border rounded-xl">
              <div className="divide-y divide-border">
                {displayStandards.map((s) => (
                  <label
                    key={s.id}
                    className="flex items-center gap-3 p-3 hover:bg-sage-50 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedStandards.includes(s.id)}
                      onChange={() => toggleStandard(s.id)}
                      className="w-4 h-4 text-sage-600 rounded border-border focus:ring-sage-500"
                    />
                    <div className="flex-1 min-w-0">
                      <span className="text-sm font-medium text-text">{s.code}</span>
                      <p className="text-xs text-text-muted truncate">{s.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Settings */}
        <div className="bg-surface-elevated rounded-2xl p-5 shadow-sm border border-border">
          <h3 className="text-sm font-display font-semibold text-text mb-3">Settings</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-text-muted mb-1.5">Per Standard</label>
              <input
                type="number"
                min={1}
                max={10}
                value={questionsPerStandard}
                onChange={(e) => setQuestionsPerStandard(Number(e.target.value))}
                className="w-full px-3 py-2 border border-border rounded-xl bg-surface text-sm focus:ring-2 focus:ring-sage-500"
              />
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1.5">Type</label>
              <select
                value={questionType}
                onChange={(e) => setQuestionType(e.target.value as 'multiple_choice' | 'open_ended')}
                className="w-full px-3 py-2 border border-border rounded-xl bg-surface text-sm focus:ring-2 focus:ring-sage-500"
              >
                <option value="multiple_choice">Multiple Choice</option>
                <option value="open_ended">Open Ended</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1.5">Review Mode</label>
              <select
                value={qualityMode}
                onChange={(e) => setQualityMode(e.target.value as QualityMode)}
                className="w-full px-3 py-2 border border-border rounded-xl bg-surface text-sm focus:ring-2 focus:ring-sage-500"
              >
                <option value="reviewed">Auto Review</option>
                <option value="quality">Best Reviewed</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1.5">Timeout (s)</label>
              <input
                type="number"
                min={30}
                max={600}
                step={30}
                value={timeout}
                onChange={(e) => setTimeout(Number(e.target.value))}
                className="w-full px-3 py-2 border border-border rounded-xl bg-surface text-sm focus:ring-2 focus:ring-sage-500"
              />
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1.5">Candidates</label>
              <input
                type="number"
                min={1}
                max={5}
                value={qualityMode === 'quality' ? candidateCount : 1}
                disabled={qualityMode !== 'quality'}
                onChange={(e) => setCandidateCount(Number(e.target.value))}
                className="w-full px-3 py-2 border border-border rounded-xl bg-surface text-sm focus:ring-2 focus:ring-sage-500 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1.5">Review Retries</label>
              <input
                type="number"
                min={0}
                max={3}
                value={repairAttempts}
                onChange={(e) => setRepairAttempts(Number(e.target.value))}
                className="w-full px-3 py-2 border border-border rounded-xl bg-surface text-sm focus:ring-2 focus:ring-sage-500"
              />
            </div>
            <div>
              <label className="block text-sm text-text-muted mb-1.5">Min Score</label>
              <input
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={minReviewScore}
                onChange={(e) => setMinReviewScore(Number(e.target.value))}
                className="w-full px-3 py-2 border border-border rounded-xl bg-surface text-sm focus:ring-2 focus:ring-sage-500"
              />
            </div>
          </div>
        </div>

        {/* Start button */}
        <motion.button
          onClick={handleStart}
          disabled={loading || isRunning}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-coral-500 text-white rounded-xl font-display font-semibold hover:bg-coral-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Starting...
            </>
          ) : isRunning ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Job #{activeJob?.id} running...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Start Generation
            </>
          )}
        </motion.button>
      </div>

      {/* Right column: progress + history */}
      <div className="space-y-4">
        {/* Active job */}
        <AnimatePresence>
          {activeJob && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-surface-elevated rounded-2xl p-5 shadow-sm border border-border"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-display font-semibold text-text">
                    Job #{activeJob.id}
                  </h3>
                  <p className="text-xs text-text-muted capitalize">{activeJob.status}</p>
                </div>
                <StatusBadge status={activeJob.status} />
              </div>

              {/* Progress bar */}
              <div className="mb-4">
                <div className="flex justify-between text-xs text-text-muted mb-1">
                  <span>{activeJob.completed_standards} / {activeJob.total_standards} standards</span>
                  <span>{activeJob.questions_created} questions</span>
                </div>
                <div className="h-2 bg-surface-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-sage-500 rounded-full transition-all duration-500"
                    style={{
                      width: `${activeJob.total_standards > 0
                        ? ((activeJob.completed_standards + activeJob.failed_standards) / activeJob.total_standards) * 100
                        : 0}%`,
                    }}
                  />
                </div>
              </div>

              <div className="mb-4 grid grid-cols-3 gap-2 text-xs">
                <div className="rounded-xl bg-surface-muted px-3 py-2">
                  <div className="text-text-subtle">Mode</div>
                  <div className="font-medium text-text capitalize">{activeJob.quality_mode}</div>
                </div>
                <div className="rounded-xl bg-surface-muted px-3 py-2">
                  <div className="text-text-subtle">Candidates</div>
                  <div className="font-medium text-text">{activeJob.candidate_count}</div>
                </div>
                <div className="rounded-xl bg-surface-muted px-3 py-2">
                  <div className="text-text-subtle">Min Score</div>
                  <div className="font-medium text-text">{Math.round(activeJob.min_review_score * 100)}%</div>
                </div>
              </div>

              {/* Per-standard mini list */}
              {activeJob.job_standards && activeJob.job_standards.length > 0 && (
                <div className="max-h-48 overflow-y-auto space-y-1 mb-4">
                  {activeJob.job_standards.map((js) => (
                    <div
                      key={js.id}
                      className="flex items-center gap-2 text-xs px-2 py-1 rounded-lg"
                    >
                      {js.status === 'done' && <CheckCircle className="w-3.5 h-3.5 text-green-500 shrink-0" />}
                      {js.status === 'failed' && <AlertCircle className="w-3.5 h-3.5 text-coral-500 shrink-0" />}
                      {js.status === 'running' && <Loader2 className="w-3.5 h-3.5 text-sage-500 animate-spin shrink-0" />}
                      {js.status === 'pending' && <Clock className="w-3.5 h-3.5 text-text-subtle shrink-0" />}
                      <span className="text-text-muted">{js.standard_code ?? `Standard ${js.standard_id}`}</span>
                      {js.avg_quality_score !== null && js.avg_quality_score !== undefined && (
                        <span className="ml-auto inline-flex items-center gap-1 text-sage-700">
                          <ShieldCheck className="w-3 h-3" />
                          {Math.round(js.avg_quality_score * 100)}%
                        </span>
                      )}
                      {js.error && <span className="text-coral-500 ml-auto truncate max-w-[120px]">{js.error}</span>}
                    </div>
                  ))}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2">
                {!TERMINAL_STATUSES.has(activeJob.status) && (
                  <button
                    onClick={() => handleCancel(activeJob.id)}
                    className="flex-1 px-3 py-2 text-xs bg-surface-muted border border-border rounded-xl text-text-muted hover:text-text transition-colors"
                  >
                    Cancel
                  </button>
                )}
                {activeJob.status === 'failed' && (
                  <button
                    onClick={() => handleRetry(activeJob.id)}
                    className="flex-1 px-3 py-2 text-xs bg-sage-600 text-white rounded-xl hover:bg-sage-700 transition-colors flex items-center justify-center gap-1"
                  >
                    <RefreshCw className="w-3 h-3" />
                    Retry Failed
                  </button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Recent jobs */}
        <div className="bg-surface-elevated rounded-2xl p-5 shadow-sm border border-border">
          <button
            onClick={() => setJobListOpen((v) => !v)}
            className="w-full flex items-center justify-between"
          >
            <h3 className="text-sm font-display font-semibold text-text">Recent Jobs</h3>
            {jobListOpen ? <ChevronUp className="w-4 h-4 text-text-muted" /> : <ChevronDown className="w-4 h-4 text-text-muted" />}
          </button>

          <AnimatePresence>
            {jobListOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-3 space-y-2 max-h-64 overflow-y-auto">
                  {recentJobs.length === 0 && (
                    <p className="text-xs text-text-muted text-center py-4">No jobs yet</p>
                  )}
                  {recentJobs.map((job) => (
                    <div
                      key={job.id}
                      className={`p-3 rounded-xl border text-xs cursor-pointer transition-colors ${
                        activeJob?.id === job.id
                          ? 'bg-sage-50 border-sage-300'
                          : 'bg-surface border-border hover:border-sage-200'
                      }`}
                      onClick={() => {
                        setActiveJob(job);
                        if (!TERMINAL_STATUSES.has(job.status)) {
                          startPolling(job.id);
                        }
                      }}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium">Job #{job.id}</span>
                        <StatusBadge status={job.status} size="sm" />
                      </div>
                      <div className="text-text-muted">
                        {job.completed_standards}/{job.total_standards} standards · {job.questions_created} questions
                      </div>
                      <div className="text-text-subtle mt-1 capitalize">
                        {job.quality_mode} mode · {job.candidate_count} candidate{job.candidate_count === 1 ? '' : 's'}
                      </div>
                      {job.errors && job.errors.length > 0 && (
                        <div className="text-coral-500 mt-1">{job.errors.length} errors</div>
                      )}
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status, size = 'md' }: { status: string; size?: 'sm' | 'md' }) {
  const styles: Record<string, string> = {
    pending: 'bg-surface-muted text-text-muted',
    running: 'bg-sage-100 text-sage-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-coral-100 text-coral-700',
    cancelled: 'bg-surface-muted text-text-subtle',
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full font-medium capitalize ${size === 'sm' ? 'text-[10px]' : 'text-xs'} ${styles[status] || styles.pending}`}
    >
      {status}
    </span>
  );
}
