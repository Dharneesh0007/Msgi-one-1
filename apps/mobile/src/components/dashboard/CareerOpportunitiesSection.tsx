import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { JobOpportunity } from '../../types/business';
import { EmptyStateView } from '../common/StateViews';

export function CareerOpportunitiesSection({ jobs }: { jobs: JobOpportunity[] }) {
  const router = useRouter();

  return (
    <View style={styles.section}>
      <View style={styles.headerRow}>
        <Text style={styles.sectionTitle}>CareerBridge Opportunities</Text>
        <TouchableOpacity onPress={() => router.push('/(tabs)/opportunities')}>
          <Text style={styles.link}>Explore All</Text>
        </TouchableOpacity>
      </View>
      {jobs.length === 0 ? (
        <EmptyStateView icon="💼" title="No Active Job Postings" subtitle="Check back soon for alumni-referred roles." />
      ) : (
        jobs.slice(0, 2).map((job) => (
          <TouchableOpacity
            key={job.id}
            style={styles.card}
            onPress={() => router.push('/(tabs)/opportunities')}
          >
            <Text style={styles.title}>{job.title}</Text>
            <Text style={styles.company}>{job.company} • {job.location}</Text>
            <View style={styles.badgeRow}>
              <View style={styles.typeBadge}>
                <Text style={styles.typeText}>{job.opportunity_type.replace('_', ' ').toUpperCase()}</Text>
              </View>
              {job.alumni_referral_available ? (
                <View style={styles.referralBadge}>
                  <Text style={styles.referralText}>Alumni Referral</Text>
                </View>
              ) : null}
            </View>
          </TouchableOpacity>
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
  company: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  badgeRow: { flexDirection: 'row', gap: Spacing.xs, marginTop: Spacing.xs },
  typeBadge: { backgroundColor: '#F1F5F9', paddingHorizontal: 6, paddingVertical: 2, borderRadius: BorderRadius.sm },
  typeText: { fontSize: 10, fontWeight: 'bold', color: Colors.textSecondary },
  referralBadge: { backgroundColor: '#DCFCE7', paddingHorizontal: 6, paddingVertical: 2, borderRadius: BorderRadius.sm },
  referralText: { fontSize: 10, fontWeight: 'bold', color: '#15803D' },
});
