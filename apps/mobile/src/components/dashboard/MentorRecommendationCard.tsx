import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { MentorProfile } from '../../types/business';

export function MentorRecommendationCard({
  mentor,
  onRequestMentorship,
}: {
  mentor: MentorProfile;
  onRequestMentorship: (mentor: MentorProfile) => void;
}) {
  return (
    <View style={styles.mentorCard}>
      <View style={styles.mentorHeader}>
        <View style={styles.avatarSmall}>
          <Text style={styles.avatarSmallText}>{mentor.full_name[0]}</Text>
        </View>
        <View style={styles.mentorMeta}>
          <Text style={styles.mentorName}>{mentor.full_name}</Text>
          <Text style={styles.mentorHeadline}>{mentor.headline}</Text>
          <Text style={styles.mentorLocation}>📍 {mentor.country}</Text>
        </View>
        {mentor.match_score ? (
          <View style={styles.scoreBadge}>
            <Text style={styles.scoreText}>{mentor.match_score}% Match</Text>
          </View>
        ) : null}
      </View>

      <View style={styles.topicsRow}>
        {mentor.advisory_topics.map((t) => (
          <View key={t} style={styles.topicBadge}>
            <Text style={styles.topicText}>{t}</Text>
          </View>
        ))}
      </View>

      <View style={styles.mentorFooter}>
        <Text style={styles.slotsText}>
          {mentor.available_slots} of {mentor.max_active_mentees} slots open
        </Text>
        <TouchableOpacity
          style={styles.requestButton}
          onPress={() => onRequestMentorship(mentor)}
        >
          <Text style={styles.requestButtonText}>Request Mentorship</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  mentorCard: {
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  mentorHeader: { flexDirection: 'row', alignItems: 'flex-start' },
  avatarSmall: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Spacing.sm,
  },
  avatarSmallText: { color: '#FFFFFF', fontWeight: 'bold', fontSize: Typography.fontSize.md },
  mentorMeta: { flex: 1 },
  mentorName: { fontSize: Typography.fontSize.sm, fontWeight: 'bold', color: Colors.text },
  mentorHeadline: { fontSize: 11, color: Colors.textSecondary },
  mentorLocation: { fontSize: 10, color: Colors.textMuted, marginTop: 2 },
  scoreBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  scoreText: { fontSize: 10, fontWeight: 'bold', color: '#15803D' },
  topicsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginTop: Spacing.sm },
  topicBadge: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  topicText: { fontSize: 10, color: Colors.textSecondary },
  mentorFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: Spacing.md,
    paddingTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
  },
  slotsText: { fontSize: 11, color: Colors.textSecondary },
  requestButton: {
    backgroundColor: Colors.primary,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
    borderRadius: BorderRadius.sm,
  },
  requestButtonText: { color: '#FFFFFF', fontSize: 11, fontWeight: 'bold' },
});
