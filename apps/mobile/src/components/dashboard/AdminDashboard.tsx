import React, { useState } from 'react';
import { View, Text, TouchableOpacity, TextInput, StyleSheet } from 'react-native';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { UserProfileResponse } from '../../types/auth';
import { WelcomeBanner } from './WelcomeBanner';
import { AIActionCard } from './AIActionCard';
import { FeedbackBanner, EmptyStateView, ErrorRecoveryBanner } from '../common/StateViews';
import { useDashboardData } from '../../hooks/useDashboardData';

export function AdminDashboard({
  user,
  dashboard,
}: {
  user: UserProfileResponse | null;
  dashboard: ReturnType<typeof useDashboardData>;
}) {
  const [annTitle, setAnnTitle] = useState('');
  const [annBody, setAnnBody] = useState('');

  const submitAnnouncement = async () => {
    if (annTitle.trim().length < 3 || annBody.trim().length < 10) return;
    await dashboard.handleCreateAnnouncement(annTitle.trim(), annBody.trim());
    setAnnTitle('');
    setAnnBody('');
  };

  return (
    <View>
      <WelcomeBanner user={user} primaryRole="admin" subtitle="Institutional Administration & Governance" />

      {dashboard.loadError ? (
        <ErrorRecoveryBanner message={dashboard.loadError} onRetry={dashboard.loadDashboardData} />
      ) : null}
      {dashboard.actionFeedback ? <FeedbackBanner message={dashboard.actionFeedback} /> : null}

      {/* Summary KPIs */}
      {dashboard.adminSummary ? (
        <View style={styles.kpiRow}>
          <View style={styles.kpiCard}>
            <Text style={styles.kpiValue}>{dashboard.adminSummary.pending_verifications_count}</Text>
            <Text style={styles.kpiLabel}>Pending Verify</Text>
          </View>
          <View style={styles.kpiCard}>
            <Text style={styles.kpiValue}>{dashboard.adminSummary.active_alumni_count}</Text>
            <Text style={styles.kpiLabel}>Alumni</Text>
          </View>
          <View style={styles.kpiCard}>
            <Text style={styles.kpiValue}>{dashboard.adminStatus?.open_reports ?? 0}</Text>
            <Text style={styles.kpiLabel}>Open Reports</Text>
          </View>
        </View>
      ) : null}

      {/* Operational Status */}
      {dashboard.adminStatus ? (
        <View style={styles.statusBox}>
          <Text style={styles.statusTitle}>Operational Health: {dashboard.adminStatus.api_status.toUpperCase()}</Text>
          <Text style={styles.statusMeta}>
            Audit Entries: {dashboard.adminStatus.audit_log_entries} • user_skills RLS Active: {dashboard.adminStatus.user_skills_rls_enabled ? 'Yes' : 'Disabled (Awaiting Remote Migration)'}
          </Text>
        </View>
      ) : null}

      <AIActionCard
        title="Admin Ops & AI Provider Governance"
        subtitle="Analyze verification queues, audit metrics, and external AI provider usage."
      />

      {/* Verification Queue */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Credential Verification Queue ({dashboard.pendingVerifications.length})</Text>
        {dashboard.pendingVerifications.length === 0 ? (
          <EmptyStateView icon="🛡️" title="Queue Clear" subtitle="All verification requests have been processed." />
        ) : (
          dashboard.pendingVerifications.map((vReq) => (
            <View key={vReq.id} style={styles.card}>
              <Text style={styles.cardTitle}>{vReq.user_name} ({vReq.user_email})</Text>
              <Text style={styles.cardMeta}>Requested Role: {vReq.requested_role.toUpperCase()}</Text>
              <View style={styles.actionRow}>
                <TouchableOpacity
                  style={[styles.btn, styles.approveBtn]}
                  onPress={() => dashboard.handleDecideVerification(vReq.id, 'approved')}
                >
                  <Text style={styles.btnText}>Approve</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.btn, styles.rejectBtn]}
                  onPress={() => dashboard.handleDecideVerification(vReq.id, 'rejected')}
                >
                  <Text style={styles.btnText}>Reject</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))
        )}
      </View>

      {/* Moderation Reports */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Moderation Reports ({dashboard.adminReports.length})</Text>
        {dashboard.adminReports.length === 0 ? (
          <EmptyStateView icon="✅" title="No Pending Reports" subtitle="No abuse or safety reports require action." />
        ) : (
          dashboard.adminReports.map((rep) => (
            <View key={rep.id} style={styles.card}>
              <Text style={styles.cardTitle}>{rep.category.toUpperCase()} — {rep.status.toUpperCase()}</Text>
              <Text style={styles.cardMeta}>{rep.description}</Text>
              {rep.status === 'pending' ? (
                <View style={styles.actionRow}>
                  <TouchableOpacity style={[styles.btn, styles.approveBtn]} onPress={() => dashboard.handleResolveReport(rep.id, 'resolved')}>
                    <Text style={styles.btnText}>Resolve</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={[styles.btn, styles.rejectBtn]} onPress={() => dashboard.handleResolveReport(rep.id, 'dismissed')}>
                    <Text style={styles.btnText}>Dismiss</Text>
                  </TouchableOpacity>
                </View>
              ) : null}
            </View>
          ))
        )}
      </View>

      {/* Publish Announcement */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Publish Institutional Announcement</Text>
        <View style={styles.card}>
          <TextInput
            style={styles.input}
            placeholder="Announcement title"
            value={annTitle}
            onChangeText={setAnnTitle}
          />
          <TextInput
            style={[styles.input, { minHeight: 60 }]}
            placeholder="Message body (min 10 chars)"
            value={annBody}
            onChangeText={setAnnBody}
            multiline
          />
          <TouchableOpacity style={styles.publishBtn} onPress={submitAnnouncement}>
            <Text style={styles.btnText}>Publish Announcement</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* User Directory Role Summary */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Role Directory ({dashboard.adminUsers.length})</Text>
        {dashboard.adminUsers.slice(0, 5).map((u) => (
          <View key={u.user_id} style={styles.card}>
            <Text style={styles.cardTitle}>{u.full_name} ({u.email})</Text>
            <Text style={styles.cardMeta}>Roles: {u.roles.join(', ')} • {u.is_verified ? 'Verified' : 'Unverified'}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  kpiRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.md },
  kpiCard: {
    flex: 1,
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  kpiValue: { fontSize: Typography.fontSize.xl, fontWeight: 'bold', color: Colors.primary },
  kpiLabel: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  statusBox: { backgroundColor: '#ECFDF5', borderWidth: 1, borderColor: '#A7F3D0', borderRadius: BorderRadius.md, padding: Spacing.sm, marginBottom: Spacing.md },
  statusTitle: { fontSize: 12, fontWeight: 'bold', color: '#065F46' },
  statusMeta: { fontSize: 11, color: '#047857', marginTop: 2 },
  section: { marginBottom: Spacing.lg },
  sectionTitle: { fontSize: Typography.fontSize.md, fontWeight: 'bold', color: Colors.text, marginBottom: Spacing.sm },
  card: { backgroundColor: Colors.card, borderRadius: BorderRadius.md, padding: Spacing.md, marginBottom: Spacing.xs, borderWidth: 1, borderColor: Colors.border },
  cardTitle: { fontSize: 13, fontWeight: 'bold', color: Colors.text },
  cardMeta: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  actionRow: { flexDirection: 'row', gap: Spacing.xs, marginTop: Spacing.sm },
  btn: { flex: 1, paddingVertical: 6, borderRadius: BorderRadius.sm, alignItems: 'center' },
  approveBtn: { backgroundColor: Colors.success },
  rejectBtn: { backgroundColor: Colors.error },
  publishBtn: { backgroundColor: Colors.primary, paddingVertical: 8, borderRadius: BorderRadius.sm, alignItems: 'center' },
  btnText: { color: '#FFFFFF', fontSize: 11, fontWeight: 'bold' },
  input: { backgroundColor: Colors.background, borderWidth: 1, borderColor: Colors.border, borderRadius: BorderRadius.sm, padding: Spacing.sm, marginBottom: Spacing.xs, color: Colors.text },
});
