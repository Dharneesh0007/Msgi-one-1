/**
 * MSGI One — CareerBridge Opportunities Screen
 * Connects to live backend API: GET /api/v1/jobs, POST /api/v1/jobs/{id}/applications
 * Features: Job listings, skill-overlap analysis, alumni referral indicators, and application submission.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  TextInput,
  RefreshControl,
  Alert,
} from 'react-native';
import { FlashList } from '@shopify/flash-list';
import { api } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import { loadOfflineReadCache, saveOfflineReadCache } from '../../lib/offlineQueue';
import { JobOpportunity, JobApplication } from '../../types/business';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';

export default function OpportunitiesScreen() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'all' | 'internships' | 'full_time' | 'my_apps'>('all');
  const [jobs, setJobs] = useState<JobOpportunity[]>([]);
  const [myApplications, setMyApplications] = useState<JobApplication[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [selectedJob, setSelectedJob] = useState<JobOpportunity | null>(null);
  const [coverNote, setCoverNote] = useState('');
  const [isApplying, setIsApplying] = useState(false);
  const [applyMessage, setApplyMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchJobs = useCallback(async () => {
    try {
      setIsLoading(true);
      const params: Record<string, any> = {};
      if (activeTab === 'internships') params.opportunity_type = 'internship';
      if (activeTab === 'full_time') params.opportunity_type = 'full_time';

      const res = await api.listJobs(params);
      const loadedJobs = res || [];
      setJobs(loadedJobs);
      if (user?.id && activeTab === 'all') {
        saveOfflineReadCache(user.id, 'jobs_feed', loadedJobs).catch(() => null);
      }

      const apps = await api.getMyApplications();
      setMyApplications(apps || []);
    } catch (err: any) {
      console.warn('[Opportunities] Failed to fetch jobs:', err.message);
      if (user?.id && activeTab === 'all') {
        const cached = await loadOfflineReadCache<JobOpportunity[]>(user.id, 'jobs_feed');
        if (cached) setJobs(cached);
      }
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, [activeTab, user?.id]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchJobs();
  };

  const handleApply = async (jobId: string) => {
    setIsApplying(true);
    setApplyMessage(null);
    try {
      await api.applyToJob(jobId, { cover_note: coverNote.trim() || undefined });
      setApplyMessage({
        type: 'success',
        text: 'Application successfully submitted and recorded in your institutional profile.',
      });
      fetchJobs();
    } catch (err: any) {
      setApplyMessage({
        type: 'error',
        text: err.message || 'Failed to submit application.',
      });
    } finally {
      setIsApplying(false);
    }
  };

  const appliedJobIds = new Set(myApplications.map((a) => a.job_id));

  return (
    <View style={styles.container}>
      {/* Category Tabs */}
      <View style={styles.filterRow}>
        <TouchableOpacity
          style={[styles.filterPill, activeTab === 'all' && styles.filterPillActive]}
          onPress={() => setActiveTab('all')}
        >
          <Text style={[styles.filterText, activeTab === 'all' && styles.filterTextActive]}>
            All Opportunities
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

        <TouchableOpacity
          style={[styles.filterPill, activeTab === 'full_time' && styles.filterPillActive]}
          onPress={() => setActiveTab('full_time')}
        >
          <Text style={[styles.filterText, activeTab === 'full_time' && styles.filterTextActive]}>
            Full-Time
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.filterPill, activeTab === 'my_apps' && styles.filterPillActive]}
          onPress={() => setActiveTab('my_apps')}
        >
          <Text style={[styles.filterText, activeTab === 'my_apps' && styles.filterTextActive]}>
            My Applications ({myApplications.length})
          </Text>
        </TouchableOpacity>
      </View>

      <View style={{ flex: 1 }}>
        {isLoading && !refreshing ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>Loading career opportunities...</Text>
          </View>
        ) : activeTab === 'my_apps' ? (
          <FlashList
            data={myApplications}
            keyExtractor={(item) => item.id}
            estimatedItemSize={120}
            contentContainerStyle={styles.scrollContent}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.primary]} />}
            ListEmptyComponent={
              <View style={styles.emptyBox}>
                <Text style={styles.emptyIcon}>📄</Text>
                <Text style={styles.emptyTitle}>No Applications Submitted</Text>
                <Text style={styles.emptySubtitle}>Explore open listings and apply with one click.</Text>
              </View>
            }
            renderItem={({ item: appItem }) => (
              <View style={styles.card}>
                <View style={styles.cardHeader}>
                  <View>
                    <Text style={styles.jobTitle}>{appItem.job_title}</Text>
                    <Text style={styles.companyName}>{appItem.company}</Text>
                  </View>
                  <View style={styles.statusBadge}>
                    <Text style={styles.statusText}>{appItem.status.toUpperCase()}</Text>
                  </View>
                </View>
                <Text style={styles.appliedDate}>
                  Submitted: {new Date(appItem.submitted_at).toLocaleDateString()}
                </Text>
                {appItem.cover_note && (
                  <Text style={styles.coverNotePreview}>Note: "{appItem.cover_note}"</Text>
                )}
              </View>
            )}
          />
        ) : (
          <FlashList
            data={jobs}
            keyExtractor={(item) => item.id}
            estimatedItemSize={210}
            contentContainerStyle={styles.scrollContent}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.primary]} />}
            renderItem={({ item: job }) => {
              const hasApplied = appliedJobIds.has(job.id);
              return (
                <View style={styles.card}>
                  <View style={styles.cardHeader}>
                    <View style={styles.titleArea}>
                      <Text style={styles.jobTitle}>{job.title}</Text>
                      <Text style={styles.companyName}>{job.company}</Text>
                    </View>
                    <View style={styles.typeBadge}>
                      <Text style={styles.typeText}>{job.opportunity_type.replace('_', ' ').toUpperCase()}</Text>
                    </View>
                  </View>

                  <Text style={styles.locationText}>📍 {job.location}</Text>

                  {job.skill_overlap && (
                    <View style={styles.skillMatchContainer}>
                      <View style={styles.matchBadge}>
                        <Text style={styles.matchScoreText}>
                          {job.skill_overlap.match_percentage}% Skill Overlap
                        </Text>
                      </View>
                      <Text style={styles.matchSkillsSummary}>
                        Matched: {job.skill_overlap.matched_skills.join(', ') || 'None'}
                      </Text>
                    </View>
                  )}

                  {job.alumni_referral_available && (
                    <View style={styles.referralBox}>
                      <Text style={styles.referralText}>
                        🤝 {job.alumni_count_at_company} verified alumni work at {job.company}
                      </Text>
                    </View>
                  )}

                  <View style={styles.cardFooter}>
                    <TouchableOpacity
                      style={styles.detailsButton}
                      onPress={() => {
                        setSelectedJob(job);
                        setCoverNote('');
                        setApplyMessage(null);
                      }}
                    >
                      <Text style={styles.detailsButtonText}>View Details</Text>
                    </TouchableOpacity>

                    {hasApplied ? (
                      <View style={styles.appliedPill}>
                        <Text style={styles.appliedPillText}>✓ Applied</Text>
                      </View>
                    ) : (
                      <TouchableOpacity
                        style={styles.applyButton}
                        onPress={() => {
                          setSelectedJob(job);
                          setCoverNote('');
                          setApplyMessage(null);
                        }}
                      >
                        <Text style={styles.applyButtonText}>Apply Now</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                </View>
              );
            }}
          />
        )}
      </View>

      {/* Application & Details Modal Sheet */}
      {selectedJob && (
        <View style={styles.modalOverlay}>
          <ScrollView contentContainerStyle={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{selectedJob.title}</Text>
              <TouchableOpacity onPress={() => setSelectedJob(null)}>
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.modalCompany}>{selectedJob.company} • {selectedJob.location}</Text>

            <View style={styles.modalSection}>
              <Text style={styles.modalSectionTitle}>Role Overview</Text>
              <Text style={styles.modalDescription}>{selectedJob.description}</Text>
            </View>

            <View style={styles.modalSection}>
              <Text style={styles.modalSectionTitle}>Required Skills</Text>
              <View style={styles.skillsRow}>
                {selectedJob.required_skills.map((skill) => (
                  <View key={skill} style={styles.skillBadge}>
                    <Text style={styles.skillText}>{skill}</Text>
                  </View>
                ))}
              </View>
            </View>

            {applyMessage && (
              <View style={[styles.messageBanner, applyMessage.type === 'error' ? styles.errorBanner : styles.successBanner]}>
                <Text style={[styles.messageText, applyMessage.type === 'error' ? styles.errorText : styles.successText]}>
                  {applyMessage.text}
                </Text>
              </View>
            )}

            {!appliedJobIds.has(selectedJob.id) && !applyMessage?.text.includes('successfully') ? (
              <View style={styles.applicationSection}>
                <Text style={styles.modalSectionTitle}>Submit Application</Text>
                <TextInput
                  style={styles.coverNoteInput}
                  placeholder="Optional cover note or reason for application..."
                  placeholderTextColor={Colors.textMuted}
                  value={coverNote}
                  onChangeText={setCoverNote}
                  multiline
                  numberOfLines={3}
                />
                <TouchableOpacity
                  style={[styles.confirmApplyButton, isApplying && styles.buttonDisabled]}
                  onPress={() => handleApply(selectedJob.id)}
                  disabled={isApplying}
                >
                  {isApplying ? (
                    <ActivityIndicator color="#FFFFFF" />
                  ) : (
                    <Text style={styles.confirmApplyButtonText}>Confirm & Submit Application</Text>
                  )}
                </TouchableOpacity>
              </View>
            ) : (
              <View style={styles.appliedConfirmationBox}>
                <Text style={styles.appliedConfirmationText}>✓ You have applied for this position</Text>
              </View>
            )}

            <TouchableOpacity style={styles.modalCloseBtn} onPress={() => setSelectedJob(null)}>
              <Text style={styles.modalCloseBtnText}>Close</Text>
            </TouchableOpacity>
          </ScrollView>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  filterRow: {
    flexDirection: 'row',
    backgroundColor: Colors.card,
    padding: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    gap: Spacing.xs,
  },
  filterPill: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.background,
  },
  filterPillActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  filterText: {
    fontSize: 11,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  filterTextActive: {
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: Spacing.xxl,
  },
  loadingBox: {
    paddingVertical: Spacing.xl,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textSecondary,
    marginTop: Spacing.sm,
  },
  emptyBox: {
    alignItems: 'center',
    paddingVertical: Spacing.xxl,
  },
  emptyIcon: {
    fontSize: 40,
    marginBottom: Spacing.sm,
  },
  emptyTitle: {
    fontSize: Typography.fontSize.md,
    fontWeight: 'bold',
    color: Colors.text,
  },
  emptySubtitle: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textSecondary,
    marginTop: 2,
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
  titleArea: {
    flex: 1,
    marginRight: Spacing.sm,
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
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.primaryLight,
  },
  locationText: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textMuted,
    marginTop: 4,
  },
  skillMatchContainer: {
    marginTop: Spacing.sm,
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.sm,
    padding: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.borderLight,
  },
  matchBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
    marginBottom: 4,
  },
  matchScoreText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#15803D',
  },
  matchSkillsSummary: {
    fontSize: 11,
    color: Colors.textSecondary,
  },
  referralBox: {
    backgroundColor: '#FFFBEB',
    borderRadius: BorderRadius.sm,
    padding: Spacing.xs,
    marginTop: Spacing.xs,
    borderLeftWidth: 3,
    borderLeftColor: Colors.accent,
  },
  referralText: {
    fontSize: 11,
    color: '#92400E',
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
  detailsButton: {
    paddingVertical: 6,
    paddingHorizontal: Spacing.sm,
  },
  detailsButtonText: {
    color: Colors.textSecondary,
    fontSize: Typography.fontSize.xs,
    fontWeight: '600',
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
  appliedPill: {
    backgroundColor: '#DCFCE7',
    borderRadius: BorderRadius.sm,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
  },
  appliedPillText: {
    color: '#15803D',
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
  },
  statusBadge: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  statusText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#92400E',
  },
  appliedDate: {
    fontSize: 11,
    color: Colors.textMuted,
    marginTop: 4,
  },
  coverNotePreview: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    marginTop: 4,
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: Colors.card,
    borderTopLeftRadius: BorderRadius.lg,
    borderTopRightRadius: BorderRadius.lg,
    padding: Spacing.lg,
    maxHeight: '85%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: Typography.fontSize.lg,
    fontWeight: 'bold',
    color: Colors.text,
    flex: 1,
  },
  modalCloseText: {
    fontSize: Typography.fontSize.lg,
    color: Colors.textSecondary,
    padding: Spacing.xs,
  },
  modalCompany: {
    fontSize: Typography.fontSize.sm,
    color: Colors.textSecondary,
    marginTop: 2,
    marginBottom: Spacing.md,
  },
  modalSection: {
    marginBottom: Spacing.md,
  },
  modalSectionTitle: {
    fontSize: Typography.fontSize.sm,
    fontWeight: 'bold',
    color: Colors.text,
    marginBottom: 4,
  },
  modalDescription: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textSecondary,
    lineHeight: 18,
  },
  skillsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  skillBadge: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    borderRadius: BorderRadius.sm,
  },
  skillText: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  applicationSection: {
    marginTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
    paddingTop: Spacing.sm,
  },
  coverNoteInput: {
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: BorderRadius.md,
    padding: Spacing.sm,
    fontSize: Typography.fontSize.xs,
    color: Colors.text,
    textAlignVertical: 'top',
    marginBottom: Spacing.sm,
  },
  confirmApplyButton: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.md,
    paddingVertical: Spacing.sm,
    alignItems: 'center',
  },
  confirmApplyButtonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: Typography.fontSize.sm,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  appliedConfirmationBox: {
    backgroundColor: '#DCFCE7',
    padding: Spacing.sm,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
    marginVertical: Spacing.sm,
  },
  appliedConfirmationText: {
    color: '#15803D',
    fontWeight: 'bold',
    fontSize: Typography.fontSize.xs,
  },
  messageBanner: {
    padding: Spacing.sm,
    borderRadius: BorderRadius.sm,
    marginBottom: Spacing.sm,
  },
  errorBanner: {
    backgroundColor: '#FEE2E2',
  },
  successBanner: {
    backgroundColor: '#DCFCE7',
  },
  messageText: {
    fontSize: 11,
    fontWeight: '500',
  },
  errorText: {
    color: Colors.error,
  },
  successText: {
    color: '#15803D',
  },
  modalCloseBtn: {
    marginTop: Spacing.sm,
    alignItems: 'center',
    paddingVertical: Spacing.sm,
  },
  modalCloseBtnText: {
    color: Colors.textSecondary,
    fontSize: Typography.fontSize.xs,
  },
});
