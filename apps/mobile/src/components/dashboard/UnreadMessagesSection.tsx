import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter, Href } from 'expo-router';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { ConversationItem } from '../../types/business';
import { EmptyStateView } from '../common/StateViews';

export function UnreadMessagesSection({
  threads = [],
}: {
  threads?: ConversationItem[];
}) {
  const router = useRouter();

  return (
    <View style={styles.section}>
      <View style={styles.headerRow}>
        <Text style={styles.sectionTitle}>Messages</Text>
        <TouchableOpacity onPress={() => router.push('/messages' as Href)}>
          <Text style={styles.link}>Open Inbox</Text>
        </TouchableOpacity>
      </View>
      {threads.length === 0 ? (
        <EmptyStateView
          icon="💬"
          title="No Unread Messages"
          subtitle="Start a private real-time conversation with a verified alumnus or student."
          actionLabel="Open Messages"
          onAction={() => router.push('/messages' as Href)}
        />
      ) : (
        threads.slice(0, 3).map((t) => (
          <TouchableOpacity key={t.id} style={styles.card} onPress={() => router.push('/messages' as Href)}>
            <View style={styles.row}>
              <Text style={styles.peer}>{t.peer_name} {t.peer_online ? '🟢' : ''}</Text>
              {t.unread_count > 0 ? <Text style={styles.unread}>{t.unread_count} unread</Text> : null}
            </View>
            <Text style={styles.preview} numberOfLines={1}>{t.last_message_preview || 'Active conversation'}</Text>
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
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  peer: { fontSize: Typography.fontSize.sm, fontWeight: 'bold', color: Colors.text },
  unread: { fontSize: 11, fontWeight: 'bold', color: Colors.primary },
  preview: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
});
