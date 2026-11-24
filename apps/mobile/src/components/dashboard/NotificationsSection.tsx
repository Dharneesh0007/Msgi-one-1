import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { NotificationRecord } from '../../types/business';
import { EmptyStateView } from '../common/StateViews';

export function NotificationsSection({
  notifications,
  unreadCount,
  onMarkRead,
}: {
  notifications: NotificationRecord[];
  unreadCount: number;
  onMarkRead: (id: string) => void;
}) {
  return (
    <View style={styles.section}>
      <View style={styles.headerRow}>
        <Text style={styles.sectionTitle}>Realtime Alerts</Text>
        {unreadCount > 0 ? (
          <View style={styles.unreadBadge}>
            <Text style={styles.unreadBadgeText}>{unreadCount} Unread</Text>
          </View>
        ) : null}
      </View>
      {notifications.length === 0 ? (
        <EmptyStateView icon="🔔" title="No Notifications" subtitle="You are all caught up." />
      ) : (
        notifications.slice(0, 4).map((notif) => (
          <View key={notif.id} style={[styles.notifCard, !notif.is_read && styles.notifUnread]}>
            <View style={styles.notifHeader}>
              <Text style={styles.notifTitle}>{notif.title}</Text>
              {!notif.is_read ? (
                <TouchableOpacity style={styles.markReadBtn} onPress={() => onMarkRead(notif.id)}>
                  <Text style={styles.markReadBtnText}>Mark Read</Text>
                </TouchableOpacity>
              ) : null}
            </View>
            <Text style={styles.notifMessage}>{notif.message}</Text>
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
  unreadBadge: { backgroundColor: Colors.error, paddingHorizontal: 8, paddingVertical: 2, borderRadius: BorderRadius.full },
  unreadBadgeText: { color: '#FFFFFF', fontSize: 10, fontWeight: 'bold' },
  notifCard: {
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.sm,
    marginBottom: Spacing.xs,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  notifUnread: { borderLeftWidth: 3, borderLeftColor: Colors.primary, backgroundColor: '#F8FAFF' },
  notifHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  notifTitle: { fontSize: 12, fontWeight: 'bold', color: Colors.text, flex: 1 },
  markReadBtn: { backgroundColor: Colors.primary, paddingHorizontal: 8, paddingVertical: 3, borderRadius: BorderRadius.sm },
  markReadBtnText: { color: '#FFFFFF', fontSize: 10, fontWeight: 'bold' },
  notifMessage: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
});
