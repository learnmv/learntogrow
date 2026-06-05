import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle, Loader2, RefreshCw } from 'lucide-react';
import { getQuestionInsights } from '../../services/admin';
import { getErrorMessage } from '../../lib/errors';
import type { QuestionInsightsResponse, DomainInsight } from '../../types/admin';

export function QuestionInsightsPanel() {
  const [insights, setInsights] = useState<QuestionInsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setLoading(true);
      const data = await getQuestionInsights();
      setInsights(data);
      setError(null);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to load insights'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 text-sage-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-coral-50 border border-coral-200 rounded-2xl p-6 text-center">
        <AlertCircle className="w-8 h-8 text-coral-600 mx-auto mb-2" />
        <p className="text-coral-700 mb-4">{error}</p>
        <button onClick={load} className="px-4 py-2 bg-sage-600 text-white rounded-xl hover:bg-sage-700">
          Retry
        </button>
      </div>
    );
  }

  if (!insights) return null;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        <SummaryCard
          label="Total Standards"
          value={insights.total_standards}
          color="sage"
        />
        <SummaryCard
          label="Total Questions"
          value={insights.total_questions}
          color="blue"
        />
        <SummaryCard
          label="Coverage"
          value={`${insights.coverage_percent}%`}
          color={insights.coverage_percent >= 70 ? 'sage' : insights.coverage_percent >= 40 ? 'amber' : 'coral'}
        />
      </motion.div>

      {/* Domain Breakdown */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-surface-elevated rounded-2xl border border-border overflow-hidden"
      >
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="font-display font-semibold text-text">Domain Coverage</h3>
          <button onClick={load} className="text-text-muted hover:text-sage-600 transition-colors">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
        <div className="divide-y divide-border">
          {insights.domains.map((domain) => (
            <DomainRow key={domain.domain_id} domain={domain} />
          ))}
        </div>
      </motion.div>
    </div>
  );
}

function SummaryCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  const colorMap: Record<string, string> = {
    sage: 'bg-sage-100 text-sage-700 border-sage-200',
    blue: 'bg-blue-100 text-blue-700 border-blue-200',
    amber: 'bg-amber-100 text-amber-700 border-amber-200',
    coral: 'bg-coral-100 text-coral-700 border-coral-200',
  };

  return (
    <div className={`rounded-2xl p-5 border ${colorMap[color] || colorMap.sage}`}>
      <p className="text-sm font-medium opacity-80">{label}</p>
      <p className="text-3xl font-display font-bold mt-1">{value}</p>
    </div>
  );
}

function DomainRow({ domain }: { domain: DomainInsight }) {
  const statusConfig = {
    good: { icon: CheckCircle, color: 'text-sage-600', bg: 'bg-sage-100' },
    low: { icon: AlertCircle, color: 'text-amber-600', bg: 'bg-amber-100' },
    none: { icon: AlertCircle, color: 'text-coral-600', bg: 'bg-coral-100' },
  };

  const config = statusConfig[domain.coverage_status as keyof typeof statusConfig] || statusConfig.none;
  const StatusIcon = config.icon;

  return (
    <div className="p-4">
      <div className="flex items-center gap-4">
        <div className={`p-2 rounded-xl ${config.bg} shrink-0`}>
          <StatusIcon className={`w-5 h-5 ${config.color}`} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-display font-medium text-text truncate">{domain.domain_name}</p>
          <p className="text-xs text-text-muted">{domain.domain_code}</p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-sm font-medium text-text">{domain.question_count} / {domain.standard_count}</p>
          <p className="text-xs text-text-muted">questions</p>
        </div>
      </div>
      {domain.coverage_status !== 'good' && (
        <div className="mt-2 ml-12">
          <div className="w-full h-2 bg-sage-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-sage-400 rounded-full transition-all"
              style={{ width: `${Math.min(100, (domain.question_count / Math.max(domain.standard_count, 1)) * 100)}%` }}
            />
          </div>
          <p className="text-xs text-text-muted mt-1">
            {domain.coverage_status === 'none'
              ? 'No questions - generate some to fill the gap'
              : 'Low coverage - consider generating more questions'}
          </p>
        </div>
      )}
      {domain.accuracy !== null && (
        <p className="text-xs text-text-muted mt-1 ml-12">
          Student accuracy: {(domain.accuracy * 100).toFixed(0)}%
        </p>
      )}
    </div>
  );
}
