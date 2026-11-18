/**
 * MSGI One — Alumni Network Directory Screen (Phase 2 Preview)
 * Complies with FERPA/GDPR privacy: contact details masked; public headline & skills displayed.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  FlatList,
} from 'react-native';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';

interface AlumniCard {
  id: string;
  fullName: string;
  headline: string;
  company: string;
  location: string;
  skills: string[];
  isVerified: boolean;
  graduationYear: number;
}

const SAMPLE_ALUMNI: AlumniCard[] = [
  {
    id: 'alumni-1',
    fullName: 'Kenji Sato',
    headline: 'Staff AI Engineer at Rakuten',
    company: 'Rakuten Symphony',
    location: 'Tokyo, Japan',
    skills: ['PyTorch', 'NLP', 'FastAPI', 'Distributed Systems'],
    isVerified: true,
    graduationYear: 2021,
  },
  {
    id: 'alumni-2',
    fullName: 'Ananya Sharma',
    headline: 'Senior Product Manager at Microsoft',
    company: 'Microsoft',
    location: 'Bengaluru, India',
    skills: ['Cloud Architecture', 'Product Strategy', 'Azure', 'AI Ops'],
    isVerified: true,
    graduationYear: 2019,
  },
  {
    id: 'alumni-3',
    fullName: 'David Chen',
    headline: 'Founding Engineer at Stealth Robotics',
    company: 'Stealth Robotics',
    location: 'San Francisco, USA',
    skills: ['ROS 2', 'Embedded C++', 'Computer Vision', 'Robotics'],
    isVerified: true,
    graduationYear: 2022,
  },
];

export default function NetworkScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  const filterTags = ['All', 'Tokyo', 'Bengaluru', 'San Francisco', 'AI / ML', 'Product'];

  const filteredAlumni = SAMPLE_ALUMNI.filter((alumnus) => {
    const matchesSearch =
      alumnus.fullName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alumnus.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alumnus.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alumnus.skills.some((s) => s.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesTag =
      !selectedTag ||
      selectedTag === 'All' ||
      alumnus.location.includes(selectedTag) ||
      alumnus.skills.some((s) => s.includes(selectedTag));

    return matchesSearch && matchesTag;
  });

  return (
    <View style={styles.container}>
      {/* Search Header */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search by name, company, skill or city..."
          placeholderTextColor={Colors.textMuted}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />

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
      <ScrollView contentContainerStyle={styles.listContent}>
        <View style={styles.phase2Notice}>
          <Text style={styles.phase2Badge}>PHASE 2 DIRECTORY PREVIEW</Text>
          <Text style={styles.phase2Text}>
            Direct messaging, 1-on-1 mentorship scheduling, and pgvector semantic search will be
            fully enabled in Phase 2.
          </Text>
        </View>

        {filteredAlumni.map((alumnus) => (
          <View key={alumnus.id} style={styles.alumniCard}>
            <View style={styles.cardHeader}>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>{alumnus.fullName[0]}</Text>
              </View>
              <View style={styles.cardInfo}>
                <View style={styles.nameRow}>
                  <Text style={styles.nameText}>{alumnus.fullName}</Text>
                  {alumnus.isVerified && (
                    <View style={styles.verifiedBadge}>
                      <Text style={styles.verifiedText}>✓ Verified</Text>
                    </View>
                  )}
                </View>
                <Text style={styles.headlineText}>{alumnus.headline}</Text>
                <Text style={styles.locationText}>
                  📍 {alumnus.location} • Class of {alumnus.graduationYear}
                </Text>
              </View>
            </View>

            <View style={styles.skillsRow}>
              {alumnus.skills.map((skill) => (
                <View key={skill} style={styles.skillBadge}>
                  <Text style={styles.skillText}>{skill}</Text>
                </View>
              ))}
            </View>

            <View style={styles.cardActions}>
              <TouchableOpacity style={styles.connectButton}>
                <Text style={styles.connectButtonText}>View Full Profile</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))}
      </ScrollView>
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
  phase2Notice: {
    backgroundColor: '#EFF6FF',
    borderWidth: 1,
    borderColor: '#BFDBFE',
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.md,
  },
  phase2Badge: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: '#1E40AF',
    marginBottom: 4,
  },
  phase2Text: {
    fontSize: Typography.fontSize.xs,
    color: '#3B82F6',
    lineHeight: 16,
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
  connectButton: {
    paddingVertical: 6,
    paddingHorizontal: Spacing.md,
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.sm,
  },
  connectButtonText: {
    color: '#FFFFFF',
    fontSize: Typography.fontSize.xs,
    fontWeight: '600',
  },
});
