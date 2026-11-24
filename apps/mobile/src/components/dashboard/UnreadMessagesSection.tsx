import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { EmptyStateView } from '../common/StateViews';

export interface UnreadThreadSummary {
  conversation_id: string;
  peer_name: string;
  last_message_preview: string;
  unread_count: number;
}

export function UnreadMessagesSection({
  threads = [],
}: {
  threads?: UnreadThreadSummary[];
}) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Messages</Text>
      {threads.length === 0 ? (
        <EmptyStateView
          icon="💬"
          title="No Unread Messages"
          subtitle="Real-time 1-on-1 messaging threads with verified alumni and students will appear here (Phase 6)."
        />
      ) : (
        threads.map((t) => (
          <View key={t.conversation_id} style={styles.card}>
            <View style={styles.row}>
              <Text style={styles.peer}>{t.peer_name}</Text>
              <Text style={styles.unread}>{t.unread_count} unread</Text>
            </View>
            <Text style={styles.preview} numberOfLines={1}>{t.last_message_preview}</Text>
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
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  peer: { fontSize: Typography.fontSize.sm, fontWeight: 'bold', color: Colors.text },
  unread: { fontSize: 11, fontWeight: 'bold', color: Colors.primary },
  preview: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
});
