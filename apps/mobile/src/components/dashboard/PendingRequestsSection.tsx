import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { MentorRequest } from '../../types/business';
import { EmptyStateView } from '../common/StateViews';

export function PendingRequestsSection({
  requests,
  mode,
  onRespond,
}: {
  requests: MentorRequest[];
  mode: 'student' | 'alumni';
  onRespond?: (requestId: string, status: 'accepted' | 'rejected' | 'clarification_requested' | 'cancelled', notes?: string) => void;
}) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>
        {mode === 'alumni' ? 'Student Request Centre' : 'My Pending Mentorship Requests'}
      </Text>
      {requests.length === 0 ? (
        <EmptyStateView
          icon="🤝"
          title={mode === 'alumni' ? 'No Student Requests Yet' : 'No Active Requests'}
          subtitle={
            mode === 'alumni'
              ? 'Incoming mentorship and consultation requests from students will appear here.'
              : 'Discover verified alumni mentors to submit a request.'
          }
        />
      ) : (
        requests.map((req) => (
          <View key={req.id} style={styles.card}>
            <View style={styles.headerRow}>
              <Text style={styles.title}>
                {mode === 'alumni' ? req.student_name : `${req.mentor_name} (${req.mentor_company})`}
              </Text>
              <View style={styles.statusBadge}>
                <Text style={styles.statusText}>{req.status.toUpperCase()}</Text>
              </View>
            </View>
            <Text style={styles.topic}>Topic: {req.topic}</Text>
            <Text style={styles.goal}>{req.career_goal}</Text>
            {req.mentor_notes ? <Text style={styles.notes}>Note: {req.mentor_notes}</Text> : null}

            {mode === 'alumni' && (req.status === 'pending' || req.status === 'clarification_requested') && onRespond ? (
              <View style={styles.actionRow}>
                <TouchableOpacity
                  style={[styles.btn, styles.acceptBtn]}
                  onPress={() => onRespond(req.id, 'accepted', 'Accepted via Alumni Portal')}
                >
                  <Text style={styles.btnText}>Accept</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.btn, styles.clarifyBtn]}
                  onPress={() => onRespond(req.id, 'clarification_requested', 'Could you share specific topics or goals?')}
                >
                  <Text style={styles.btnText}>Clarify</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.btn, styles.declineBtn]}
                  onPress={() => onRespond(req.id, 'rejected', 'Currently at capacity')}
                >
                  <Text style={styles.btnText}>Decline</Text>
                </TouchableOpacity>
              </View>
            ) : null}

            {mode === 'student' && req.status === 'pending' && onRespond ? (
              <TouchableOpacity
                style={[styles.btn, styles.declineBtn, { alignSelf: 'flex-end', marginTop: Spacing.xs }]}
                onPress={() => onRespond(req.id, 'cancelled')}
              >
                <Text style={styles.btnText}>Cancel Request</Text>
              </TouchableOpacity>
            ) : null}
          </View>
        ))
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  section: { marginBottom: Spacing.lg },
  sectionTitle: { fontSize: Typography.fontSize.md, fontWeight: 'bold', color: Colors.text, marginBottom: Spacing.sm },
  card: {
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: Spacing.xs },
  title: { fontSize: Typography.fontSize.sm, fontWeight: 'bold', color: Colors.text, flex: 1 },
  statusBadge: { backgroundColor: '#FEF3C7', paddingHorizontal: 6, paddingVertical: 2, borderRadius: BorderRadius.sm },
  statusText: { fontSize: 10, fontWeight: 'bold', color: '#92400E' },
  topic: { fontSize: 12, fontWeight: '600', color: Colors.primary, marginTop: 4 },
  goal: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  notes: { fontSize: 11, color: Colors.textMuted, fontStyle: 'italic', marginTop: 4 },
  actionRow: { flexDirection: 'row', gap: Spacing.xs, marginTop: Spacing.sm },
  btn: { paddingHorizontal: Spacing.sm, paddingVertical: 6, borderRadius: BorderRadius.sm },
  acceptBtn: { backgroundColor: Colors.success },
  clarifyBtn: { backgroundColor: Colors.info },
  declineBtn: { backgroundColor: Colors.error },
  btnText: { color: '#FFFFFF', fontSize: 11, fontWeight: 'bold' },
});
