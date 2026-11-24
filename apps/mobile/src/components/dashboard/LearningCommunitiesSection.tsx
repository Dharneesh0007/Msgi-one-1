import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { LearningResourceItem, CourseEnrollmentItem, CommunityItem } from '../../types/business';

export function LearningCommunitiesSection({
  courses,
  enrollments,
  communities,
  updatingEnrollmentId,
  onEnrollCourse,
  onUpdateProgress,
  onJoinCommunity,
}: {
  courses: LearningResourceItem[];
  enrollments: CourseEnrollmentItem[];
  communities: CommunityItem[];
  updatingEnrollmentId: string | null;
  onEnrollCourse: (resourceId: string) => void;
  onUpdateProgress: (enrollmentId: string, progress: number) => void;
  onJoinCommunity: (communityId: string) => void;
}) {
  const [tab, setTab] = useState<'learning' | 'communities'>('learning');

  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Learning Academy & Guilds</Text>
      <View style={styles.tabRow}>
        <TouchableOpacity
          style={[styles.tabBtn, tab === 'learning' && styles.tabBtnActive]}
          onPress={() => setTab('learning')}
        >
          <Text style={[styles.tabText, tab === 'learning' && styles.tabTextActive]}>🎓 Learning</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabBtn, tab === 'communities' && styles.tabBtnActive]}
          onPress={() => setTab('communities')}
        >
          <Text style={[styles.tabText, tab === 'communities' && styles.tabTextActive]}>👥 Communities</Text>
        </TouchableOpacity>
      </View>

      {tab === 'learning' ? (
        <View>
          {enrollments.map((enr) => (
            <View key={enr.id} style={styles.card}>
              <Text style={styles.title}>{enr.course_title} ({enr.progress_percentage}%)</Text>
              <View style={styles.progressTrack}>
                <View style={[styles.progressFill, { width: `${enr.progress_percentage}%` }]} />
              </View>
              {enr.status !== 'completed' ? (
                <TouchableOpacity
                  style={styles.actionBtn}
                  onPress={() => onUpdateProgress(enr.id, enr.progress_percentage)}
                  disabled={updatingEnrollmentId === enr.id}
                >
                  <Text style={styles.actionBtnText}>
                    {updatingEnrollmentId === enr.id ? 'Saving...' : 'Mark +25% Progress'}
                  </Text>
                </TouchableOpacity>
              ) : null}
            </View>
          ))}
          {courses.slice(0, 3).map((course) => {
            const isEnrolled = enrollments.some((e) => e.resource_id === course.resource_id);
            return (
              <View key={course.resource_id} style={styles.card}>
                <Text style={styles.title}>{course.title}</Text>
                <Text style={styles.meta}>{course.provider} • {course.target_skill} • {course.duration_hours}h</Text>
                {!isEnrolled ? (
                  <TouchableOpacity style={styles.actionBtn} onPress={() => onEnrollCourse(course.resource_id)}>
                    <Text style={styles.actionBtnText}>Enroll Free</Text>
                  </TouchableOpacity>
                ) : (
                  <Text style={styles.enrolledText}>✓ Enrolled</Text>
                )}
              </View>
            );
          })}
        </View>
      ) : (
        <View>
          {communities.map((comm) => (
            <View key={comm.id} style={styles.card}>
              <Text style={styles.title}>{comm.name}</Text>
              <Text style={styles.meta}>{comm.description}</Text>
              <View style={styles.footerRow}>
                <Text style={styles.meta}>👥 {comm.member_count} Members</Text>
                {comm.is_member ? (
                  <Text style={styles.enrolledText}>✓ Member</Text>
                ) : (
                  <TouchableOpacity style={styles.actionBtn} onPress={() => onJoinCommunity(comm.id)}>
                    <Text style={styles.actionBtnText}>{comm.is_private ? 'Request Access' : 'Join Group'}</Text>
                  </TouchableOpacity>
                )}
              </View>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  section: { marginBottom: Spacing.lg },
  sectionTitle: { fontSize: Typography.fontSize.md, fontWeight: 'bold', color: Colors.text, marginBottom: Spacing.sm },
  tabRow: { flexDirection: 'row', gap: Spacing.xs, marginBottom: Spacing.sm },
  tabBtn: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: BorderRadius.sm,
    backgroundColor: Colors.card,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
  },
  tabBtnActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  tabText: { fontSize: 12, fontWeight: '600', color: Colors.textSecondary },
  tabTextActive: { color: '#FFFFFF' },
  card: {
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.xs,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  title: { fontSize: 13, fontWeight: 'bold', color: Colors.text },
  meta: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  progressTrack: { height: 6, backgroundColor: '#E2E8F0', borderRadius: 3, marginVertical: 6, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: Colors.success },
  actionBtn: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.primary,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 5,
    borderRadius: BorderRadius.sm,
    marginTop: 6,
  },
  actionBtnText: { color: '#FFFFFF', fontSize: 11, fontWeight: 'bold' },
  enrolledText: { fontSize: 11, fontWeight: 'bold', color: Colors.success, marginTop: 4 },
  footerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 },
});
