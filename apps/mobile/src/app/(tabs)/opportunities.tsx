/**
 * MSGI One — CareerBridge Opportunities Screen (Phase 3 Preview)
 * Displays institutional jobs, internships, and alumni referral opportunities.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';

interface JobCard {
  id: string;
  title: string;
  company: string;
  location: string;
  type: string;
  postedDaysAgo: number;
  alumniAtCompany: number;
}

const SAMPLE_JOBS: JobCard[] = [
  {
    id: 'job-1',
    title: 'Machine Learning Engineer — Platform',
    company: 'Rakuten Symphony',
    location: 'Tokyo, Japan (Hybrid)',
    type: 'Full-time',
    postedDaysAgo: 2,
    alumniAtCompany: 14,
  },
  {
    id: 'job-2',
    title: 'Cloud Solutions Architect',
    company: 'Microsoft',
    location: 'Bengaluru, India',
    type: 'Full-time',
    postedDaysAgo: 4,
    alumniAtCompany: 28,
  },
  {
    id: 'job-3',
    title: 'Autonomous Robotics Intern',
    company: 'Stealth Robotics',
    location: 'San Francisco, USA (On-site)',
    type: 'Internship',
    postedDaysAgo: 1,
    alumniAtCompany: 3,
  },
];

export default function OpportunitiesScreen() {
  const [activeTab, setActiveTab] = useState<'all' | 'referrals' | 'internships'>('all');

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      {/* Scope Notice */}
      <View style={styles.phaseNotice}>
        <Text style={styles.phaseBadge}>CAREERBRIDGE PREVIEW</Text>
        <Text style={styles.phaseText}>
          Job listings and alumni referral pipelines are demonstrated below. Automated resume matching
          and direct recruiter chats will go live in Phase 3.
        </Text>
      </View>

      {/* Filter Tabs */}
      <View style={styles.filterRow}>
        <TouchableOpacity
          style={[styles.filterPill, activeTab === 'all' && styles.filterPillActive]}
          onPress={() => setActiveTab('all')}
        >
          <Text style={[styles.filterText, activeTab === 'all' && styles.filterTextActive]}>
            All Roles
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterPill, activeTab === 'referrals' && styles.filterPillActive]}
          onPress={() => setActiveTab('referrals')}
        >
          <Text style={[styles.filterText, activeTab === 'referrals' && styles.filterTextActive]}>
            Alumni Referrals
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterPill, activeTab === 'internships' && styles.filterPillActive]}
          onPress={() => setActiveTab('internships')}
        >
          <Text style={[styles.filterText, activeTab === 'internships' && styles.filterTextActive]}>
            Internships
          </Text>
        </TouchableOpacity>
      </View>

      {/* Job Cards */}
      {SAMPLE_JOBS.map((job) => (
        <View key={job.id} style={styles.card}>
          <View style={styles.cardHeader}>
            <View>
              <Text style={styles.jobTitle}>{job.title}</Text>
              <Text style={styles.companyName}>{job.company}</Text>
            </View>
            <View style={styles.typeBadge}>
              <Text style={styles.typeText}>{job.type}</Text>
            </View>
          </View>

          <Text style={styles.locationText}>📍 {job.location}</Text>

          <View style={styles.referralBox}>
            <Text style={styles.referralText}>
              🤝 {job.alumniAtCompany} verified MSGI alumni work here
            </Text>
          </View>

          <View style={styles.cardFooter}>
            <Text style={styles.dateText}>Posted {job.postedDaysAgo}d ago</Text>
            <TouchableOpacity style={styles.applyButton}>
              <Text style={styles.applyButtonText}>Request Referral</Text>
            </TouchableOpacity>
          </View>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: Spacing.xxl,
  },
  phaseNotice: {
    backgroundColor: '#FEF3C7',
    borderWidth: 1,
    borderColor: '#F59E0B',
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.md,
  },
  phaseBadge: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: '#92400E',
    marginBottom: 4,
  },
  phaseText: {
    fontSize: Typography.fontSize.xs,
    color: '#B45309',
    lineHeight: 16,
  },
  filterRow: {
    flexDirection: 'row',
    gap: Spacing.xs,
    marginBottom: Spacing.md,
  },
  filterPill: {
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.full,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  filterPillActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  filterText: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  filterTextActive: {
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  card: {
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  jobTitle: {
    fontSize: Typography.fontSize.md,
    fontWeight: 'bold',
    color: Colors.text,
  },
  companyName: {
    fontSize: Typography.fontSize.sm,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  typeBadge: {
    backgroundColor: '#EFF6FF',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  typeText: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: Colors.primaryLight,
  },
  locationText: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textMuted,
    marginTop: Spacing.xs,
  },
  referralBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.sm,
    padding: Spacing.sm,
    marginTop: Spacing.sm,
    borderLeftWidth: 3,
    borderLeftColor: Colors.accent,
  },
  referralText: {
    fontSize: Typography.fontSize.xs,
    color: Colors.text,
    fontWeight: '500',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
    paddingTop: Spacing.sm,
  },
  dateText: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textMuted,
  },
  applyButton: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.sm,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
  },
  applyButtonText: {
    color: '#FFFFFF',
    fontSize: Typography.fontSize.xs,
    fontWeight: '600',
  },
});
