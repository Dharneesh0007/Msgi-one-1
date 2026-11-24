/**
 * MSGI One — Alumni Network Directory Screen
 * Connects to live backend API: GET /api/v1/alumni
 * Features: Debounced search, country & skill filters, verified badges, privacy contact masking.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { api } from '../../lib/api';
import { AlumniDirectoryItem } from '../../types/business';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';

export default function NetworkScreen() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [batchFilter, setBatchFilter] = useState('');
  const [mentorsOnly, setMentorsOnly] = useState(false);
  const [savedIds, setSavedIds] = useState<string[]>([]);
  const [alumniList, setAlumniList] = useState<AlumniDirectoryItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [selectedAlumni, setSelectedAlumni] = useState<AlumniDirectoryItem | null>(null);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  const filterTags = ['All', 'Japan', 'India', 'United States', 'AI / ML', 'Cloud'];

  const fetchAlumni = useCallback(async () => {
    try {
      setIsLoading(true);
      const params: Record<string, any> = { verified_only: true };

      if (searchQuery.trim()) {
        params.query = searchQuery.trim();
      }
      if (batchFilter.trim() && /^\d{4}$/.test(batchFilter.trim())) {
        params.graduation_year = Number(batchFilter.trim());
      }
      if (mentorsOnly) {
        params.mentor_opt_in = true;
      }

      if (selectedTag && selectedTag !== 'All') {
        if (['Japan', 'India', 'United States'].includes(selectedTag)) {
          params.country = selectedTag;
        } else if (selectedTag === 'AI / ML') {
          params.skill = 'Python';
        } else if (selectedTag === 'Cloud') {
          params.skill = 'Cloud Architecture';
        }
      }

      const res = await api.searchAlumni(params);
      setAlumniList(res?.items || []);
    } catch (err: any) {
      console.warn('[Network] Failed to fetch alumni:', err.message);
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, [searchQuery, selectedTag, batchFilter, mentorsOnly]);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchAlumni();
    }, 250);
    return () => clearTimeout(timer);
  }, [fetchAlumni]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchAlumni();
  };

  return (
    <View style={styles.container}>
      {/* Search Header */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search by name, company, title, skill or city..."
          placeholderTextColor={Colors.textMuted}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />

        <View style={{ flexDirection: 'row', gap: Spacing.xs, marginTop: Spacing.xs }}>
          <TextInput
            style={[styles.searchInput, { flex: 1 }]}
            placeholder="Batch Year (e.g. 2021)"
            placeholderTextColor={Colors.textMuted}
            keyboardType="number-pad"
            maxLength={4}
            value={batchFilter}
            onChangeText={setBatchFilter}
          />
          <TouchableOpacity
            style={[styles.tagPill, mentorsOnly && styles.tagPillActive, { justifyContent: 'center' }]}
            onPress={() => setMentorsOnly(!mentorsOnly)}
          >
            <Text style={[styles.tagText, mentorsOnly && styles.tagTextActive]}>
              {mentorsOnly ? '✓ Mentors Only' : 'Mentors Only'}
            </Text>
          </TouchableOpacity>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tagsScroll}>
          {filterTags.map((tag) => (
            <TouchableOpacity
              key={tag}
              style={[
                styles.tagPill,
                (selectedTag === tag || (!selectedTag && tag === 'All')) && styles.tagPillActive,
              ]}
              onPress={() => setSelectedTag(tag === 'All' ? null : tag)}
            >
              <Text
                style={[
                  styles.tagText,
                  (selectedTag === tag || (!selectedTag && tag === 'All')) && styles.tagTextActive,
                ]}
              >
                {tag}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Directory List */}
      <ScrollView
        contentContainerStyle={styles.listContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.primary]} />}
      >
        <View style={styles.privacyBanner}>
          <Text style={styles.privacyBannerText}>
            🔒 Institutional Directory: Direct emails and phone numbers are protected under FERPA/GDPR compliance.
          </Text>
        </View>

        {isLoading && !refreshing ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>Searching verified institutional alumni...</Text>
          </View>
        ) : alumniList.length === 0 ? (
          <View style={styles.emptyBox}>
            <Text style={styles.emptyIcon}>🔍</Text>
            <Text style={styles.emptyTitle}>No Alumni Matches Found</Text>
            <Text style={styles.emptySubtitle}>Try adjusting your search filters or tags.</Text>
          </View>
        ) : (
          alumniList.map((alumnus) => (
            <View key={alumnus.id} style={styles.alumniCard}>
              <View style={styles.cardHeader}>
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>{alumnus.full_name[0]}</Text>
                </View>
                <View style={styles.cardInfo}>
                  <View style={styles.nameRow}>
                    <Text style={styles.nameText}>{alumnus.full_name}</Text>
                    {alumnus.is_verified && (
                      <View style={styles.verifiedBadge}>
                        <Text style={styles.verifiedText}>✓ Verified</Text>
                      </View>
                    )}
                    {alumnus.mentor_opt_in && (
                      <View style={styles.mentorBadge}>
                        <Text style={styles.mentorText}>Mentor</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.headlineText}>{alumnus.headline}</Text>
                  <Text style={styles.locationText}>
                    📍 {alumnus.city ? `${alumnus.city}, ` : ''}{alumnus.country} • Class of {alumnus.graduation_year} ({alumnus.major})
                  </Text>
                </View>
              </View>

              <View style={styles.skillsRow}>
                {alumnus.skills.slice(0, 4).map((skill) => (
                  <View key={skill} style={styles.skillBadge}>
                    <Text style={styles.skillText}>{skill}</Text>
                  </View>
                ))}
              </View>

              <View style={styles.cardActions}>
                <TouchableOpacity
                  style={styles.detailButton}
                  onPress={() => setSelectedAlumni(alumnus)}
                >
                  <Text style={styles.detailButtonText}>View Full Profile</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))
        )}
      </ScrollView>

      {/* Alumni Detail Modal Sheet */}
      {selectedAlumni && (
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{selectedAlumni.full_name}</Text>
              <TouchableOpacity onPress={() => setSelectedAlumni(null)}>
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.modalHeadline}>{selectedAlumni.headline}</Text>
            <Text style={styles.modalMeta}>
              {selectedAlumni.major} • Class of {selectedAlumni.graduation_year}
            </Text>
            <Text style={styles.modalLocation}>
              📍 {selectedAlumni.city}, {selectedAlumni.country}
            </Text>

            <View style={styles.modalSection}>
              <Text style={styles.modalSectionTitle}>Verified Skills</Text>
              <View style={styles.modalSkillsRow}>
                {selectedAlumni.skills.map((s) => (
                  <View key={s} style={styles.skillBadge}>
                    <Text style={styles.skillText}>{s}</Text>
                  </View>
                ))}
              </View>
            </View>

            <View style={styles.modalComplianceNotice}>
              <Text style={styles.modalComplianceText}>
                Contact details are masked to safeguard alumni privacy. Connect requests can be
                initiated through MentorMatch or institutional reunion events.
              </Text>
            </View>

            {actionFeedback ? (
              <Text style={{ fontSize: 12, color: Colors.primary, marginBottom: Spacing.sm }}>{actionFeedback}</Text>
            ) : null}

            <View style={{ flexDirection: 'row', gap: Spacing.xs, marginBottom: Spacing.sm, flexWrap: 'wrap' }}>
              <TouchableOpacity
                style={[styles.detailButton, { flex: 1, alignItems: 'center' }]}
                onPress={() => {
                  const isSaved = savedIds.includes(selectedAlumni.id);
                  setSavedIds((prev) => (isSaved ? prev.filter((x) => x !== selectedAlumni.id) : [...prev, selectedAlumni.id]));
                  setActionFeedback(isSaved ? 'Removed from saved profiles.' : 'Saved profile locally.');
                }}
              >
                <Text style={styles.detailButtonText}>
                  {savedIds.includes(selectedAlumni.id) ? '★ Saved' : '☆ Save Profile'}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.detailButton, { flex: 1, alignItems: 'center', backgroundColor: Colors.accentDark }]}
                onPress={() => {
                  setSelectedAlumni(null);
                  router.push('/(tabs)/ai');
                }}
              >
                <Text style={styles.detailButtonText}>Ask AI Suitability</Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity
              style={styles.modalCloseButton}
              onPress={() => {
                setActionFeedback(null);
                setSelectedAlumni(null);
              }}
            >
              <Text style={styles.modalCloseButtonText}>Close Profile</Text>
            </TouchableOpacity>
          </View>
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
  searchContainer: {
    backgroundColor: Colors.card,
    padding: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  searchInput: {
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: BorderRadius.md,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    fontSize: Typography.fontSize.sm,
    color: Colors.text,
  },
  tagsScroll: {
    marginTop: Spacing.sm,
  },
  tagPill: {
    backgroundColor: Colors.background,
    borderRadius: BorderRadius.full,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
    marginRight: Spacing.xs,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  tagPillActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  tagText: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  tagTextActive: {
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  listContent: {
    padding: Spacing.md,
    paddingBottom: Spacing.xxl,
  },
  privacyBanner: {
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: '#BBF7D0',
    borderRadius: BorderRadius.md,
    padding: Spacing.sm,
    marginBottom: Spacing.md,
  },
  privacyBannerText: {
    fontSize: Typography.fontSize.xs,
    color: '#166534',
    lineHeight: 16,
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
  alumniCard: {
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
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: BorderRadius.full,
    backgroundColor: Colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Spacing.md,
  },
  avatarText: {
    fontSize: Typography.fontSize.lg,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  cardInfo: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
    flexWrap: 'wrap',
  },
  nameText: {
    fontSize: Typography.fontSize.md,
    fontWeight: 'bold',
    color: Colors.text,
  },
  verifiedBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: BorderRadius.sm,
  },
  verifiedText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#15803D',
  },
  mentorBadge: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: BorderRadius.sm,
  },
  mentorText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#B45309',
  },
  headlineText: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  locationText: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textMuted,
    marginTop: 4,
  },
  skillsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: Spacing.md,
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
  cardActions: {
    marginTop: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
    paddingTop: Spacing.sm,
    alignItems: 'flex-end',
  },
  detailButton: {
    paddingVertical: 6,
    paddingHorizontal: Spacing.md,
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.sm,
  },
  detailButtonText: {
    color: '#FFFFFF',
    fontSize: Typography.fontSize.xs,
    fontWeight: '600',
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
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  modalTitle: {
    fontSize: Typography.fontSize.xl,
    fontWeight: 'bold',
    color: Colors.text,
  },
  modalCloseText: {
    fontSize: Typography.fontSize.lg,
    color: Colors.textSecondary,
    padding: Spacing.xs,
  },
  modalHeadline: {
    fontSize: Typography.fontSize.sm,
    color: Colors.primary,
    fontWeight: '600',
  },
  modalMeta: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  modalLocation: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textMuted,
    marginTop: 2,
  },
  modalSection: {
    marginTop: Spacing.md,
  },
  modalSectionTitle: {
    fontSize: Typography.fontSize.sm,
    fontWeight: 'bold',
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  modalSkillsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  modalComplianceNotice: {
    backgroundColor: '#EFF6FF',
    borderRadius: BorderRadius.md,
    padding: Spacing.sm,
    marginVertical: Spacing.md,
  },
  modalComplianceText: {
    fontSize: Typography.fontSize.xs,
    color: '#1D4ED8',
    lineHeight: 16,
  },
  modalCloseButton: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.md,
    paddingVertical: Spacing.sm,
    alignItems: 'center',
  },
  modalCloseButtonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: Typography.fontSize.sm,
  },
});
