import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { EmptyStateView } from '../common/StateViews';

export interface UpcomingMeetingSummary {
  id: string;
  title: string;
  scheduled_start: string;
  counterpart_name: string;
  status: string;
}

export function UpcomingMeetingsSection({
  meetings = [],
  title = 'Upcoming Consultations & Meetings',
}: {
  meetings?: UpcomingMeetingSummary[];
  title?: string;
}) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {meetings.length === 0 ? (
        <EmptyStateView
          icon="📅"
          title="No Confirmed Meetings Scheduled"
          subtitle="Meeting scheduling & WebRTC rooms activate once a mentorship slot is confirmed (Phase 5 & 7)."
        />
      ) : (
        meetings.map((m) => (
          <View key={m.id} style={styles.card}>
            <Text style={styles.title}>{m.title}</Text>
            <Text style={styles.meta}>With {m.counterpart_name} • {new Date(m.scheduled_start).toLocaleString()}</Text>
            <Text style={styles.badge}>{m.status.toUpperCase()}</Text>
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
  title: { fontSize: Typography.fontSize.sm, fontWeight: 'bold', color: Colors.text },
  meta: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  badge: { fontSize: 10, fontWeight: 'bold', color: Colors.primary, marginTop: 4 },
});
