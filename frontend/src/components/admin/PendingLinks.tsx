import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link2, CheckCircle, XCircle, Loader2, UserCircle, GraduationCap } from 'lucide-react';
import { getPendingLinks, approveParentLink, rejectParentLink } from '../../services/admin';
import type { PendingParentLink } from '../../types/admin';

export function PendingLinks() {
  const [links, setLinks] = useState<PendingParentLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<number | null>(null);

  useEffect(() => {
    loadLinks();
  }, []);

  async function loadLinks() {
    try {
      setLoading(true);
      const data = await getPendingLinks();
      setLinks(data);
    } catch (err) {
      console.error('Failed to load pending links:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(linkId: number) {
    setProcessing(linkId);
    try {
      await approveParentLink(linkId);
      loadLinks();
    } catch (err) {
      console.error('Failed to approve link:', err);
    } finally {
      setProcessing(null);
    }
  }

  async function handleReject(linkId: number) {
    setProcessing(linkId);
    try {
      await rejectParentLink(linkId);
      loadLinks();
    } catch (err) {
      console.error('Failed to reject link:', err);
    } finally {
      setProcessing(null);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link2 className="w-6 h-6 text-sage-600" />
          <h2 className="text-xl font-display font-semibold text-text">Pending Parent Links</h2>
        </div>
        <span className="px-3 py-1 bg-coral-100 text-coral-700 rounded-full text-sm font-medium">
          {links.length} pending
        </span>
      </div>

      {/* Links List */}
      {loading ? (
        <div className="text-center py-12">
          <Loader2 className="w-8 h-8 text-sage-600 animate-spin mx-auto" />
        </div>
      ) : links.length === 0 ? (
        <div className="bg-surface-elevated rounded-2xl border border-border p-12 text-center">
          <Link2 className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-display font-medium text-text">No Pending Links</h3>
          <p className="text-text-muted mt-2">All parent-student link requests have been processed.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {links.map((link) => (
            <motion.div
              key={link.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-surface-elevated rounded-2xl border border-border p-6"
            >
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                {/* Parent Info */}
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <UserCircle className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-text">{link.parent_name}</p>
                    <p className="text-sm text-text-muted">{link.parent_email}</p>
                    <p className="text-xs text-text-muted">@{link.parent_username}</p>
                  </div>
                </div>

                {/* Arrow */}
                <div className="hidden md:flex items-center text-text-muted">
                  <span className="text-sm">wants to view</span>
                </div>

                {/* Student Info */}
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-sage-100 rounded-lg">
                    <GraduationCap className="w-5 h-5 text-sage-600" />
                  </div>
                  <div>
                    <p className="font-medium text-text">{link.student_name}</p>
                    <p className="text-sm text-text-muted">{link.student_email}</p>
                    <p className="text-xs text-text-muted">@{link.student_username}</p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleApprove(link.id)}
                    disabled={processing === link.id}
                    className="flex items-center gap-1.5 px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors disabled:opacity-50"
                  >
                    {processing === link.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <CheckCircle className="w-4 h-4" />
                    )}
                    Approve
                  </button>
                  <button
                    onClick={() => handleReject(link.id)}
                    disabled={processing === link.id}
                    className="flex items-center gap-1.5 px-4 py-2 bg-coral-100 text-coral-700 rounded-lg hover:bg-coral-200 transition-colors disabled:opacity-50"
                  >
                    {processing === link.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <XCircle className="w-4 h-4" />
                    )}
                    Reject
                  </button>
                </div>
              </div>

              <p className="text-xs text-text-muted mt-4">
                Requested {new Date(link.requested_at).toLocaleDateString()} at{' '}
                {new Date(link.requested_at).toLocaleTimeString()}
              </p>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
