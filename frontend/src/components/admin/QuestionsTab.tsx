import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Filter,
  Trash2,
  Edit3,
  ToggleLeft,
  ToggleRight,
  Loader2,
  AlertTriangle,
  CheckSquare,
  Square,
  X,
} from 'lucide-react';
import { getAdminQuestions, updateQuestion, deleteQuestion, toggleQuestionStatus, bulkDeleteQuestions } from '../../services/admin';
import { fetchSubjects } from '../../services/standards';
import { fetchGradesBySubject } from '../../services/standards';
import { fetchDomainsBySubject } from '../../services/standards';
import { fetchStandards } from '../../services/standards';
import type { QuestionFromDB } from '../../types/questions';
import type { Subject } from '../../types/standards';
import type { Grade } from '../../types/standards';
import type { Domain } from '../../types/standards';
import type { Standard } from '../../types/standards';

export function QuestionsTab() {
  const [questions, setQuestions] = useState<QuestionFromDB[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [grades, setGrades] = useState<Grade[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [standards, setStandards] = useState<Standard[]>([]);

  const [selectedSubject, setSelectedSubject] = useState<number | ''>('');
  const [selectedGrade, setSelectedGrade] = useState<number | ''>('');
  const [selectedDomain, setSelectedDomain] = useState<number | ''>('');
  const [selectedStandard, setSelectedStandard] = useState<number | ''>('');
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);

  // Selection
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [selectAll, setSelectAll] = useState(false);

  // Edit modal
  const [editingQuestion, setEditingQuestion] = useState<QuestionFromDB | null>(null);
  const [editText, setEditText] = useState('');
  const [editAnswer, setEditAnswer] = useState('');
  const [editExplanation, setEditExplanation] = useState('');
  const [editDifficulty, setEditDifficulty] = useState<number>(0.5);

  // Delete confirmation
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<number | null>(null);

  // Load subjects on mount
  useEffect(() => {
    fetchSubjects().then(setSubjects).catch(() => {});
  }, []);

  // Load grades when subject changes
  useEffect(() => {
    if (selectedSubject) {
      fetchGradesBySubject(selectedSubject).then(setGrades).catch(() => {});
    } else {
      setGrades([]);
      setSelectedGrade('');
    }
  }, [selectedSubject]);

  // Load domains when subject changes
  useEffect(() => {
    if (selectedSubject) {
      fetchDomainsBySubject(selectedSubject).then(setDomains).catch(() => {});
    } else {
      setDomains([]);
      setSelectedDomain('');
    }
  }, [selectedSubject]);

  // Load standards when grade/domain changes
  useEffect(() => {
    if (selectedGrade) {
      const params: any = { grade_id: selectedGrade };
      if (selectedDomain) params.domain_id = selectedDomain;
      if (selectedSubject) params.subject_id = selectedSubject;
      fetchStandards(params).then(setStandards).catch(() => {});
    } else {
      setStandards([]);
      setSelectedStandard('');
    }
  }, [selectedGrade, selectedDomain, selectedSubject]);

  // Load questions when filters change
  const loadQuestions = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getAdminQuestions(
        selectedStandard || undefined,
        selectedDomain || undefined,
        selectedGrade || undefined,
        filterActive
      );
      setQuestions(data);
      setSelectedIds(new Set());
      setSelectAll(false);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load questions');
    } finally {
      setLoading(false);
    }
  }, [selectedSubject, selectedGrade, selectedDomain, selectedStandard, filterActive]);

  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(questions.map(q => q.id)));
    }
    setSelectAll(!selectAll);
  };

  const toggleSelection = (id: number) => {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedIds(next);
    setSelectAll(next.size === questions.length && questions.length > 0);
  };

  const handleToggleStatus = async (id: number) => {
    try {
      await toggleQuestionStatus(id);
      loadQuestions();
    } catch (err: any) {
      setError(err.message || 'Failed to toggle status');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteQuestion(id);
      setShowDeleteConfirm(null);
      loadQuestions();
    } catch (err: any) {
      setError(err.message || 'Failed to delete question');
    }
  };

  const handleBulkDelete = async () => {
    try {
      await bulkDeleteQuestions({
        question_ids: Array.from(selectedIds),
      });
      setShowBulkDeleteConfirm(false);
      loadQuestions();
    } catch (err: any) {
      setError(err.message || 'Failed to delete questions');
    }
  };

  const handleBulkDeleteMatching = async () => {
    try {
      await bulkDeleteQuestions({
        standard_id: selectedStandard || undefined,
        domain_id: selectedDomain || undefined,
        grade_id: selectedGrade || undefined,
        is_active: filterActive,
        all_matching: true,
      });
      setShowBulkDeleteConfirm(false);
      loadQuestions();
    } catch (err: any) {
      setError(err.message || 'Failed to delete questions');
    }
  };

  const openEdit = (q: QuestionFromDB) => {
    setEditingQuestion(q);
    setEditText(q.question_text);
    setEditAnswer(q.correct_answer);
    setEditExplanation(q.explanation || '');
    setEditDifficulty(q.difficulty ?? 0.5);
  };

  const handleSaveEdit = async () => {
    if (!editingQuestion) return;
    try {
      await updateQuestion(editingQuestion.id, {
        question_text: editText,
        correct_answer: editAnswer,
        explanation: editExplanation,
        difficulty: editDifficulty,
      });
      setEditingQuestion(null);
      loadQuestions();
    } catch (err: any) {
      setError(err.message || 'Failed to update question');
    }
  };

  const clearFilters = () => {
    setSelectedSubject('');
    setSelectedGrade('');
    setSelectedDomain('');
    setSelectedStandard('');
    setFilterActive(undefined);
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-surface-elevated rounded-2xl p-4 shadow-sm border border-border">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-sage-600" />
          <h3 className="font-display font-semibold text-text">Filters</h3>
          <button
            onClick={clearFilters}
            className="ml-auto text-sm text-sage-600 hover:text-sage-700 font-medium"
          >
            Clear all
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value ? Number(e.target.value) : '')}
            className="px-3 py-2 rounded-xl border border-border bg-white text-text font-body text-sm focus:outline-none focus:ring-2 focus:ring-sage-300"
          >
            <option value="">All Subjects</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <select
            value={selectedGrade}
            onChange={(e) => setSelectedGrade(e.target.value ? Number(e.target.value) : '')}
            className="px-3 py-2 rounded-xl border border-border bg-white text-text font-body text-sm focus:outline-none focus:ring-2 focus:ring-sage-300"
            disabled={!selectedSubject}
          >
            <option value="">All Grades</option>
            {grades.map((g) => (
              <option key={g.id} value={g.id}>{g.display_name || `Grade ${g.level}`}</option>
            ))}
          </select>
          <select
            value={selectedDomain}
            onChange={(e) => setSelectedDomain(e.target.value ? Number(e.target.value) : '')}
            className="px-3 py-2 rounded-xl border border-border bg-white text-text font-body text-sm focus:outline-none focus:ring-2 focus:ring-sage-300"
            disabled={!selectedSubject}
          >
            <option value="">All Domains</option>
            {domains.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
          <select
            value={selectedStandard}
            onChange={(e) => setSelectedStandard(e.target.value ? Number(e.target.value) : '')}
            className="px-3 py-2 rounded-xl border border-border bg-white text-text font-body text-sm focus:outline-none focus:ring-2 focus:ring-sage-300"
            disabled={!selectedGrade}
          >
            <option value="">All Standards</option>
            {standards.map((s) => (
              <option key={s.id} value={s.id}>{s.code}</option>
            ))}
          </select>
          <select
            value={filterActive === undefined ? '' : filterActive ? 'true' : 'false'}
            onChange={(e) => {
              const v = e.target.value;
              setFilterActive(v === '' ? undefined : v === 'true');
            }}
            className="px-3 py-2 rounded-xl border border-border bg-white text-text font-body text-sm focus:outline-none focus:ring-2 focus:ring-sage-300"
          >
            <option value="">All Status</option>
            <option value="true">Active Only</option>
            <option value="false">Inactive Only</option>
          </select>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedIds.size > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-coral-50 border border-coral-200 rounded-xl p-3 flex items-center gap-3"
        >
          <CheckSquare className="w-5 h-5 text-coral-600" />
          <span className="text-coral-700 font-medium text-sm flex-1">
            {selectedIds.size} question{selectedIds.size > 1 ? 's' : ''} selected
          </span>
          <button
            onClick={() => setShowBulkDeleteConfirm(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-coral-600 text-white rounded-lg text-sm font-medium hover:bg-coral-700 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Delete Selected
          </button>
        </motion.div>
      )}

      {error && (
        <div className="bg-coral-50 border border-coral-200 rounded-xl p-3 flex items-center gap-2 text-coral-700 text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Table */}
      <div className="bg-surface-elevated rounded-2xl shadow-sm border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-sage-50/50">
                <th className="px-4 py-3 text-left w-10">
                  <button onClick={handleSelectAll} className="text-sage-600">
                    {selectAll ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
                  </button>
                </th>
                <th className="px-4 py-3 text-left font-display font-semibold text-text w-16">ID</th>
                <th className="px-4 py-3 text-left font-display font-semibold text-text">Question</th>
                <th className="px-4 py-3 text-left font-display font-semibold text-text w-24">Type</th>
                <th className="px-4 py-3 text-left font-display font-semibold text-text w-20">Diff</th>
                <th className="px-4 py-3 text-left font-display font-semibold text-text w-24">Status</th>
                <th className="px-4 py-3 text-right font-display font-semibold text-text w-32">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center">
                    <Loader2 className="w-6 h-6 text-sage-600 animate-spin mx-auto" />
                    <p className="text-text-muted mt-2 text-sm">Loading questions...</p>
                  </td>
                </tr>
              ) : questions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-text-muted">
                    No questions found. Try adjusting your filters.
                  </td>
                </tr>
              ) : (
                questions.map((q) => (
                  <tr key={q.id} className="border-b border-border last:border-0 hover:bg-sage-50/30 transition-colors">
                    <td className="px-4 py-3">
                      <button onClick={() => toggleSelection(q.id)} className="text-sage-600">
                        {selectedIds.has(q.id) ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-text-muted font-mono">{q.id}</td>
                    <td className="px-4 py-3">
                      <p className="text-text font-medium line-clamp-2 max-w-md">{q.question_text}</p>
                      <p className="text-text-muted text-xs mt-0.5">Answer: {q.correct_answer}</p>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded-md bg-sage-100 text-sage-700 text-xs font-medium">
                        {q.question_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-text-muted">{q.difficulty?.toFixed(1) ?? '-'}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleToggleStatus(q.id)}
                        className={q.is_active ? 'text-sage-600' : 'text-text-muted'}
                      >
                        {q.is_active ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => openEdit(q)}
                          className="p-1.5 rounded-lg hover:bg-sage-100 text-sage-600 transition-colors"
                          title="Edit"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setShowDeleteConfirm(q.id)}
                          className="p-1.5 rounded-lg hover:bg-coral-100 text-coral-600 transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Modal */}
      <AnimatePresence>
        {editingQuestion && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
            onClick={() => setEditingQuestion(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-surface-elevated rounded-2xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto border border-border"
            >
              <div className="p-6">
                <h3 className="text-lg font-display font-semibold text-text mb-4">Edit Question</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-text-muted mb-1">Question Text</label>
                    <textarea
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 rounded-xl border border-border bg-white text-text text-sm focus:outline-none focus:ring-2 focus:ring-sage-300"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-muted mb-1">Correct Answer</label>
                    <input
                      value={editAnswer}
                      onChange={(e) => setEditAnswer(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl border border-border bg-white text-text text-sm focus:outline-none focus:ring-2 focus:ring-sage-300"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-muted mb-1">Explanation</label>
                    <textarea
                      value={editExplanation}
                      onChange={(e) => setEditExplanation(e.target.value)}
                      rows={2}
                      className="w-full px-3 py-2 rounded-xl border border-border bg-white text-text text-sm focus:outline-none focus:ring-2 focus:ring-sage-300"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-muted mb-1">Difficulty: {editDifficulty.toFixed(1)}</label>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.1}
                      value={editDifficulty}
                      onChange={(e) => setEditDifficulty(Number(e.target.value))}
                      className="w-full accent-sage-600"
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-3 mt-6">
                  <button
                    onClick={() => setEditingQuestion(null)}
                    className="px-4 py-2 rounded-xl border border-border text-text-muted font-medium hover:bg-sage-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveEdit}
                    className="px-4 py-2 rounded-xl bg-sage-600 text-white font-medium hover:bg-sage-700 transition-colors"
                  >
                    Save Changes
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Single Delete Confirm */}
      <AnimatePresence>
        {showDeleteConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
            onClick={() => setShowDeleteConfirm(null)}
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-surface-elevated rounded-2xl shadow-xl p-6 max-w-sm w-full border border-border"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-coral-100 rounded-xl">
                  <AlertTriangle className="w-5 h-5 text-coral-600" />
                </div>
                <h3 className="font-display font-semibold text-text">Delete Question?</h3>
              </div>
              <p className="text-text-muted text-sm mb-6">This action cannot be undone.</p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(null)}
                  className="px-4 py-2 rounded-xl border border-border text-text-muted font-medium hover:bg-sage-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDelete(showDeleteConfirm)}
                  className="px-4 py-2 rounded-xl bg-coral-600 text-white font-medium hover:bg-coral-700 transition-colors"
                >
                  Delete
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bulk Delete Confirm */}
      <AnimatePresence>
        {showBulkDeleteConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
            onClick={() => setShowBulkDeleteConfirm(false)}
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-surface-elevated rounded-2xl shadow-xl p-6 max-w-md w-full border border-border"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-coral-100 rounded-xl">
                  <AlertTriangle className="w-5 h-5 text-coral-600" />
                </div>
                <h3 className="font-display font-semibold text-text">Bulk Delete</h3>
              </div>
              <p className="text-text-muted text-sm mb-6">
                Delete {selectedIds.size} selected question{selectedIds.size > 1 ? 's' : ''}, or delete all questions matching current filters?
              </p>
              <div className="flex flex-col gap-2">
                <button
                  onClick={handleBulkDelete}
                  className="w-full px-4 py-2 rounded-xl bg-coral-600 text-white font-medium hover:bg-coral-700 transition-colors"
                >
                  Delete {selectedIds.size} Selected
                </button>
                <button
                  onClick={handleBulkDeleteMatching}
                  className="w-full px-4 py-2 rounded-xl border border-coral-300 text-coral-600 font-medium hover:bg-coral-50 transition-colors"
                >
                  Delete All Matching Filters
                </button>
                <button
                  onClick={() => setShowBulkDeleteConfirm(false)}
                  className="w-full px-4 py-2 rounded-xl border border-border text-text-muted font-medium hover:bg-sage-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
