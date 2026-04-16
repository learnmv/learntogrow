import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Edit3, Save, X, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'sonner';
import { getPrompts, updatePrompt, getPromptPlaceholders } from '../../services/prompts';
import type { PromptResponse, PromptPlaceholder } from '../../types/prompt';

export function PromptEditor() {
  const [prompts, setPrompts] = useState<PromptResponse[]>([]);
  const [placeholders, setPlaceholders] = useState<PromptPlaceholder[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingPrompt, setEditingPrompt] = useState<PromptResponse | null>(null);
  const [editContent, setEditContent] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [showPlaceholders, setShowPlaceholders] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const [promptsData, placeholdersData] = await Promise.all([
        getPrompts(),
        getPromptPlaceholders(),
      ]);
      setPrompts(promptsData);
      setPlaceholders(placeholdersData.placeholders);
    } catch (err: any) {
      toast.error('Failed to load prompts', { description: err.message });
    } finally {
      setLoading(false);
    }
  }

  function startEditing(prompt: PromptResponse) {
    setEditingPrompt(prompt);
    setEditContent(prompt.content);
    setEditDescription(prompt.description || '');
  }

  function cancelEdit() {
    setEditingPrompt(null);
    setEditContent('');
    setEditDescription('');
  }

  async function saveEdit() {
    if (!editingPrompt) return;

    try {
      setSaving(true);
      const updated = await updatePrompt(
        editingPrompt.name,
        editContent,
        editDescription || undefined
      );
      setPrompts((prev) =>
        prev.map((p) => (p.name === updated.name ? updated : p))
      );
      toast.success('Prompt saved successfully');
      cancelEdit();
    } catch (err: any) {
      toast.error('Failed to save prompt', { description: err.message });
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Placeholders Reference */}
      <div className="bg-surface-elevated rounded-2xl border border-border overflow-hidden">
        <button
          onClick={() => setShowPlaceholders(!showPlaceholders)}
          className="w-full flex items-center justify-between p-4 hover:bg-sage-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-sage-600" />
            <span className="font-display font-medium text-text">
              Available Placeholders
            </span>
          </div>
          {showPlaceholders ? (
            <ChevronUp className="w-5 h-5 text-text-muted" />
          ) : (
            <ChevronDown className="w-5 h-5 text-text-muted" />
          )}
        </button>
        <AnimatePresence>
          {showPlaceholders && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-t border-border"
            >
              <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {placeholders.map((p) => (
                  <div
                    key={p.placeholder}
                    className="bg-surface rounded-lg p-3 border border-border"
                  >
                    <code className="text-sm font-mono text-sage-700 bg-sage-50 px-1 rounded">
                      {p.placeholder}
                    </code>
                    <p className="text-sm text-text-muted mt-1">{p.description}</p>
                    <p className="text-xs text-text-muted/70 mt-1">
                      Example: {p.example}
                    </p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Prompt Cards */}
      <div className="grid grid-cols-1 gap-4">
        {prompts.map((prompt) => (
          <motion.div
            key={prompt.name}
            layout
            className="bg-surface-elevated rounded-2xl border border-border overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-sage-100 rounded-lg">
                  <FileText className="w-5 h-5 text-sage-600" />
                </div>
                <div>
                  <h3 className="font-display font-semibold text-text capitalize">
                    {prompt.name.replace(/_/g, ' ')}
                  </h3>
                  {prompt.description && (
                    <p className="text-sm text-text-muted">{prompt.description}</p>
                  )}
                </div>
              </div>
              <button
                onClick={() => startEditing(prompt)}
                className="flex items-center gap-2 px-3 py-1.5 bg-sage-100 text-sage-700 rounded-lg font-medium text-sm hover:bg-sage-200 transition-colors"
              >
                <Edit3 className="w-4 h-4" />
                Edit
              </button>
            </div>

            {/* Preview */}
            <div className="p-4">
              <pre className="text-sm font-mono text-text-muted bg-surface rounded-lg p-4 overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
                {prompt.content.slice(0, 500)}
                {prompt.content.length > 500 && '...'}
              </pre>
            </div>

            {/* Timestamp */}
            <div className="px-4 pb-4 text-xs text-text-muted">
              Last updated: {new Date(prompt.updated_at).toLocaleString()}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Edit Modal */}
      <AnimatePresence>
        {editingPrompt && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={cancelEdit}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-surface-elevated rounded-2xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between p-4 border-b border-border">
                <h2 className="font-display font-semibold text-lg text-text capitalize">
                  Edit {editingPrompt.name.replace(/_/g, ' ')} Prompt
                </h2>
                <button
                  onClick={cancelEdit}
                  className="p-2 hover:bg-sage-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-text-muted" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-4 space-y-4 overflow-y-auto max-h-[calc(90vh-140px)]">
                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-text mb-1">
                    Description
                  </label>
                  <input
                    type="text"
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    className="w-full px-3 py-2 bg-surface border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500"
                    placeholder="Brief description of this prompt template"
                  />
                </div>

                {/* Content */}
                <div>
                  <label className="block text-sm font-medium text-text mb-1">
                    Prompt Template
                  </label>
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={20}
                    className="w-full px-3 py-2 bg-surface border border-border rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-sage-500 resize-none"
                    placeholder="Enter prompt template with placeholders..."
                  />
                </div>

                {/* Quick placeholder reference */}
                <div className="bg-sage-50 rounded-lg p-3">
                  <p className="text-sm font-medium text-sage-700 mb-2">
                    Quick Reference:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {placeholders.slice(0, 5).map((p) => (
                      <code
                        key={p.placeholder}
                        className="text-xs bg-white px-2 py-1 rounded border border-sage-200"
                      >
                        {p.placeholder}
                      </code>
                    ))}
                    <span className="text-xs text-sage-600">
                      + {placeholders.length - 5} more
                    </span>
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="flex items-center justify-end gap-3 p-4 border-t border-border bg-surface">
                <button
                  onClick={cancelEdit}
                  className="px-4 py-2 text-text-muted hover:text-text transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={saveEdit}
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 bg-sage-600 text-white rounded-lg font-medium hover:bg-sage-700 transition-colors disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}