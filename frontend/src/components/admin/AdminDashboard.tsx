import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Users,
  Shield,
  BookOpen,
  FileText,
  CheckSquare,
  Link2,
  Loader2,
} from 'lucide-react';
import { getDashboardStats } from '../../services/admin';
import { QuestionGenerationForm } from './QuestionGenerationForm';
import { UserManagement } from './UserManagement';
import { PendingLinks } from './PendingLinks';
import { PromptEditor } from './PromptEditor';
import type { AdminDashboardStats } from '../../types/admin';

type Tab = 'overview' | 'generate' | 'prompts' | 'users' | 'links';

export function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  async function loadStats() {
    try {
      setLoading(true);
      const data = await getDashboardStats();
      setStats(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard stats');
    } finally {
      setLoading(false);
    }
  }

  const tabs = [
    { id: 'overview' as Tab, label: 'Overview', icon: Shield },
    { id: 'generate' as Tab, label: 'Generate Questions', icon: BookOpen },
    { id: 'prompts' as Tab, label: 'Prompts', icon: FileText },
    { id: 'users' as Tab, label: 'User Management', icon: Users },
    { id: 'links' as Tab, label: 'Pending Links', icon: Link2 },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-sage-600 animate-spin mx-auto" />
          <p className="mt-4 text-text-muted">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="w-16 h-16 bg-coral-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Shield className="w-8 h-8 text-coral-600" />
          </div>
          <p className="text-coral-600 font-display text-lg mb-2">Error Loading Dashboard</p>
          <p className="text-text-muted mb-4">{error}</p>
          <button
            onClick={loadStats}
            className="px-6 py-2 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface">
      {/* Header */}
      <header className="bg-surface-elevated border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-sage-600" />
              <div>
                <h1 className="text-xl font-display font-semibold text-text">Admin Dashboard</h1>
                <p className="text-sm text-text-muted">Manage users, generate questions, and monitor progress</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl font-display font-medium transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-sage-100 text-sage-700'
                    : 'text-text-muted hover:text-text hover:bg-sage-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === 'overview' && stats && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
            >
              {/* Total Users */}
              <StatCard
                icon={Users}
                label="Total Users"
                value={stats.total_users}
                sublabel={`${stats.total_students} students, ${stats.total_parents} parents`}
              />

              {/* Questions */}
              <StatCard
                icon={BookOpen}
                label="Total Questions"
                value={stats.total_questions}
                sublabel="Generated questions in database"
              />

              {/* Quiz Attempts */}
              <StatCard
                icon={CheckSquare}
                label="Quiz Attempts"
                value={stats.total_quiz_attempts}
                sublabel={`${stats.recent_quiz_attempts} today`}
              />

              {/* Pending Links */}
              <StatCard
                icon={Link2}
                label="Pending Links"
                value={stats.pending_parent_links}
                sublabel="Parent-student requests"
                highlight={stats.pending_parent_links > 0}
              />
            </motion.div>
          )}

          {activeTab === 'generate' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <QuestionGenerationForm onSuccess={loadStats} />
            </motion.div>
          )}

          {activeTab === 'prompts' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <PromptEditor />
            </motion.div>
          )}

          {activeTab === 'users' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <UserManagement />
            </motion.div>
          )}

          {activeTab === 'links' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <PendingLinks />
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
  sublabel: string;
  highlight?: boolean;
}

function StatCard({ icon: Icon, label, value, sublabel, highlight }: StatCardProps) {
  return (
    <div
      className={`bg-surface-elevated rounded-2xl p-6 shadow-sm border ${
        highlight ? 'border-coral-300' : 'border-border'
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-text-muted">{label}</p>
          <p className={`text-3xl font-display font-bold mt-2 ${highlight ? 'text-coral-600' : 'text-text'}`}>
            {value}
          </p>
        </div>
        <div className={`p-3 rounded-xl ${highlight ? 'bg-coral-100' : 'bg-sage-100'}`}>
          <Icon className={`w-6 h-6 ${highlight ? 'text-coral-600' : 'text-sage-600'}`} />
        </div>
      </div>
      <p className="text-sm text-text-muted mt-4">{sublabel}</p>
    </div>
  );
}
