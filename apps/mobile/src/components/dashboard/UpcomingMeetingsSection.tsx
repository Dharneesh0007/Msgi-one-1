import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter, Href } from 'expo-router';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { MeetingItem } from '../../types/business';
import { EmptyStateView } from '../common/StateViews';

export function UpcomingMeetingsSection({
  meetings = [],
  title = 'Upcoming Consultations & Meetings',
}: {
  meetings?: MeetingItem[];
  title?: string;
}) {
  const router = useRouter();

  return (
    <View style={styles.section}>
      <View style={styles.headerRow}>
        <Text style={styles.sectionTitle}>{title}</Text>
        <TouchableOpacity onPress={() => router.push('/meetings' as Href)}>
          <Text style={styles.link}>Schedule / View All</Text>
        </TouchableOpacity>
      </View>
      {meetings.length === 0 ? (
        <EmptyStateView
          icon="📅"
          title="No Confirmed Meetings Scheduled"
          subtitle="Request a meeting slot with a verified alumnus."
          actionLabel="Open Scheduling"
          onAction={() => router.push('/meetings' as Href)}
        />
      ) : (
        meetings.slice(0, 3).map((m) => (
          <View key={m.id} style={styles.card}>
            <Text style={styles.title}>{m.title}</Text>
            <Text style={styles.meta}>
              {m.student_name} ↔ {m.alumni_name} • {new Date(m.scheduled_start).toLocaleString()}
            </Text>
            <View style={styles.footer}>
              <Text style={styles.badge}>{m.status.toUpperCase()}</Text>
              {(m.status === 'scheduled' || m.status === 'in_progress') ? (
                <TouchableOpacity
                  style={styles.joinBtn}
                  onPress={() => router.push(`/room/${m.id}` as Href)}
                >
                  <Text style={styles.joinBtnText}>Join Room</Text>
                </TouchableOpacity>
              ) : null}
            </View>
          </View>
        ))
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  section: { marginBottom: Spacing.lg },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.sm },
  sectionTitle: { fontSize: Typography.fontSize.md, fontWeight: 'bold', color: Colors.text },
  link: { fontSize: Typography.fontSize.xs, color: Colors.primary, fontWeight: 'bold' },
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
  footer: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 },
  badge: { fontSize: 10, fontWeight: 'bold', color: Colors.primary },
  joinBtn: { backgroundColor: Colors.success, paddingHorizontal: 10, paddingVertical: 4, borderRadius: BorderRadius.sm },
  joinBtnText: { color: '#FFFFFF', fontSize: 11, fontWeight: 'bold' },
});
