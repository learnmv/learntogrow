import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Users,
  UserPlus,
  Search,
  Loader2,
  CheckCircle,
  XCircle,
  Shield,
  GraduationCap,
  UserCircle,
} from 'lucide-react';
import { getUsers, createUser, updateUserStatus, deleteUser } from '../../services/admin';
import { getErrorMessage } from '../../lib/errors';
import type { User } from '../../types/auth';
import type { UserCreateRequest } from '../../types/admin';

export function UserManagement() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getUsers(roleFilter || undefined);
      setUsers(data);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setLoading(false);
    }
  }, [roleFilter]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const filteredUsers = users.filter(
    (user) =>
      user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.full_name && user.full_name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  async function handleToggleStatus(userId: number, currentStatus: boolean) {
    try {
      await updateUserStatus(userId, { is_active: !currentStatus });
      loadUsers();
    } catch (err) {
      console.error('Failed to update user status:', err);
    }
  }

  async function handleDeleteUser(userId: number) {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      return;
    }

    try {
      await deleteUser(userId);
      loadUsers();
    } catch (err) {
      console.error('Failed to delete user:', err);
    }
  }

  function getRoleIcon(role: string) {
    switch (role) {
      case 'admin':
        return Shield;
      case 'student':
        return GraduationCap;
      case 'parent':
        return UserCircle;
      default:
        return UserCircle;
    }
  }

  function getRoleColor(role: string) {
    switch (role) {
      case 'admin':
        return 'text-coral-600 bg-coral-100';
      case 'student':
        return 'text-sage-600 bg-sage-100';
      case 'parent':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-text-muted bg-surface';
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Users className="w-6 h-6 text-sage-600" />
          <h2 className="text-xl font-display font-semibold text-text">User Management</h2>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-sage-600 text-white rounded-xl font-display font-medium hover:bg-sage-700 transition-colors"
        >
          <UserPlus className="w-4 h-4" />
          Create User
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
          <input
            type="text"
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 focus:border-transparent"
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="px-4 py-2 border border-border rounded-xl bg-surface focus:ring-2 focus:ring-sage-500 focus:border-transparent"
        >
          <option value="">All Roles</option>
          <option value="student">Student</option>
          <option value="parent">Parent</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      {/* Users Table */}
      {loading ? (
        <div className="text-center py-12">
          <Loader2 className="w-8 h-8 text-sage-600 animate-spin mx-auto" />
        </div>
      ) : (
        <div className="bg-surface-elevated rounded-2xl border border-border overflow-hidden">
          <table className="w-full">
            <thead className="bg-sage-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-text">User</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-text">Role</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-text">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-text">Created</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-text">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredUsers.map((user) => {
                const RoleIcon = getRoleIcon(user.role);
                return (
                  <tr key={user.id} className="hover:bg-sage-50/50">
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-text">{user.full_name || user.username}</p>
                        <p className="text-sm text-text-muted">{user.email}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${getRoleColor(
                          user.role
                        )}`}
                      >
                        <RoleIcon className="w-3.5 h-3.5" />
                        {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1.5 text-sm ${
                          user.is_active ? 'text-green-600' : 'text-text-muted'
                        }`}
                      >
                        {user.is_active ? (
                          <>
                            <CheckCircle className="w-4 h-4" />
                            Active
                          </>
                        ) : (
                          <>
                            <XCircle className="w-4 h-4" />
                            Inactive
                          </>
                        )}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-text-muted">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleToggleStatus(user.id, user.is_active)}
                          className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                            user.is_active
                              ? 'text-coral-600 hover:bg-coral-50'
                              : 'text-green-600 hover:bg-green-50'
                          }`}
                        >
                          {user.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button
                          onClick={() => handleDeleteUser(user.id)}
                          className="px-3 py-1.5 text-sm text-coral-600 hover:bg-coral-50 rounded-lg transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {filteredUsers.length === 0 && (
            <div className="text-center py-12">
              <Users className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <p className="text-text-muted">No users found</p>
            </div>
          )}
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <CreateUserModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadUsers();
          }}
        />
      )}
    </div>
  );
}

interface CreateUserModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

function CreateUserModal({ onClose, onSuccess }: CreateUserModalProps) {
  const [formData, setFormData] = useState<UserCreateRequest>({
    username: '',
    email: '',
    password: '',
    role: 'student',
    full_name: '',
    is_active: true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await createUser(formData);
      onSuccess();
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to create user'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-surface rounded-2xl p-6 max-w-md w-full shadow-xl"
      >
        <h3 className="text-xl font-display font-semibold text-text mb-4">Create User</h3>

        {error && (
          <div className="mb-4 p-3 bg-coral-50 text-coral-700 rounded-lg text-sm">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text mb-1">Username *</label>
            <input
              type="text"
              required
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              className="w-full px-4 py-2 border border-border rounded-xl bg-surface"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-1">Email *</label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-2 border border-border rounded-xl bg-surface"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-1">Password *</label>
            <input
              type="password"
              required
              minLength={8}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-2 border border-border rounded-xl bg-surface"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-1">Full Name</label>
            <input
              type="text"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className="w-full px-4 py-2 border border-border rounded-xl bg-surface"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-1">Role *</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value as 'student' | 'parent' | 'admin' })}
              className="w-full px-4 py-2 border border-border rounded-xl bg-surface"
            >
              <option value="student">Student</option>
              <option value="parent">Parent</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-border text-text rounded-xl hover:bg-surface-elevated transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-sage-600 text-white rounded-xl hover:bg-sage-700 transition-colors disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create User'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
