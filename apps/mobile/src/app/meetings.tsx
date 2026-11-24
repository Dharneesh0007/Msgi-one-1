/**
 * MSGI One — Meetings & Scheduling Hub (Phase 5)
 * Supports:
 *   - Requesting meetings with verified alumni (selecting up to 3 UTC slots from live availability)
 *   - Alumni reviewing incoming requests: Accept slot, Decline, or Counter-propose
 *   - Student confirming counter-proposed slots
 *   - Confirmed meetings calendar, Cancel, Feedback, and Join LiveKit Video Room
 */

import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams, useRouter, Href } from 'expo-router';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import { MeetingItem, MeetingRequestItem, OpenSlotDTO } from '../types/business';
import { Colors, Typography, Spacing, BorderRadius } from '../constants/theme';
import { FeedbackBanner, EmptyStateView, ErrorRecoveryBanner } from '../components/common/StateViews';

export default function MeetingsScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ alumniId?: string; alumniName?: string }>();
  const { user, primaryRole } = useAuth();

  const [requests, setRequests] = useState<MeetingRequestItem[]>([]);
  const [meetings, setMeetings] = useState<MeetingItem[]>([]);
  const [openSlots, setOpenSlots] = useState<OpenSlotDTO[]>([]);
  const [selectedSlotIndexes, setSelectedSlotIndexes] = useState<number[]>([]);
  const [targetAlumniId, setTargetAlumniId] = useState(params.alumniId || 'user-kenji-001');
  const [title, setTitle] = useState('Career & Technical Mentorship Session');
  const [purpose, setPurpose] = useState('Discuss career roadmap, projects, and industry preparation.');
  const [duration, setDuration] = useState(30);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRequestForm, setShowRequestForm] = useState(Boolean(params.alumniId));

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [reqs, mtgs, avail] = await Promise.all([
        api.listMeetingRequests(),
        api.listMeetings(),
        api.getAlumniAvailability(targetAlumniId, 14).catch(() => ({ open_slots: [] })),
      ]);
      setRequests(reqs || []);
      setMeetings(mtgs || []);
      setOpenSlots(avail?.open_slots || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load scheduling data.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [targetAlumniId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const toggleSlot = (idx: number) => {
    setSelectedSlotIndexes((prev) => {
      if (prev.includes(idx)) return prev.filter((i) => i !== idx);
      if (prev.length >= 3) return prev;
      return [...prev, idx];
    });
  };

  const handleSubmitRequest = async () => {
    if (selectedSlotIndexes.length === 0) {
      setFeedback('Please select 1 to 3 available time slots.');
      return;
    }
    try {
      setFeedback(null);
      const chosen = selectedSlotIndexes.map((i) => ({
        start_utc: openSlots[i].start_utc,
        end_utc: openSlots[i].end_utc,
      }));
      const studentTz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
      await api.createMeetingRequest(
        {
          alumni_id: targetAlumniId,
          title: title.trim(),
          purpose: purpose.trim(),
          duration_minutes: duration,
          student_timezone: studentTz,
          proposed_slots: chosen,
        },
        `mobile-${Date.now()}`
      );
      setFeedback('Meeting request submitted successfully.');
      setSelectedSlotIndexes([]);
      setShowRequestForm(false);
      await loadData();
    } catch (err: any) {
      setFeedback(err.message || 'Failed to submit meeting request.');
    }
  };

  const handleAcceptSlot = async (reqId: string, slotId: string) => {
    try {
      await api.acceptMeetingRequest(reqId, slotId);
      setFeedback('Meeting confirmed and added to both calendars.');
      await loadData();
    } catch (err: any) {
      setFeedback(err.message || 'Failed to accept slot.');
    }
  };

  const handleConfirmCounter = async (reqId: string, slotId: string) => {
    try {
      await api.confirmMeetingCounterProposal(reqId, slotId);
      setFeedback('Counter-proposed slot confirmed!');
      await loadData();
    } catch (err: any) {
      setFeedback(err.message || 'Failed to confirm slot.');
    }
  };

  const handleDecline = async (reqId: string) => {
    try {
      await api.declineMeetingRequest(reqId, 'Unavailable during proposed times.');
      setFeedback('Meeting request declined.');
      await loadData();
    } catch (err: any) {
      setFeedback(err.message || 'Failed to decline request.');
    }
  };

  const handleCancelMeeting = async (mtgId: string) => {
    try {
      await api.cancelMeeting(mtgId, 'Cancelled by participant.');
      setFeedback('Meeting cancelled.');
      await loadData();
    } catch (err: any) {
      setFeedback(err.message || 'Failed to cancel meeting.');
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.headerBar}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Meetings & Scheduling</Text>
        <TouchableOpacity onPress={() => setShowRequestForm(!showRequestForm)}>
          <Text style={styles.newBtn}>{showRequestForm ? 'Close' : '+ Request'}</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadData(); }} />}
      >
        {error ? <ErrorRecoveryBanner message={error} onRetry={loadData} /> : null}
        {feedback ? <FeedbackBanner message={feedback} /> : null}

        {showRequestForm ? (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Request Consultation {params.alumniName ? `with ${params.alumniName}` : ''}</Text>
            <TextInput style={styles.input} value={targetAlumniId} onChangeText={setTargetAlumniId} placeholder="Alumni ID" />
            <TextInput style={styles.input} value={title} onChangeText={setTitle} placeholder="Meeting Title" />
            <TextInput style={styles.input} value={purpose} onChangeText={setPurpose} placeholder="Purpose / Agenda" multiline />
            <Text style={styles.subLabel}>Select up to 3 open UTC slots ({selectedSlotIndexes.length}/3):</Text>
            {openSlots.length === 0 ? (
              <Text style={styles.muted}>No recurring availability slots found for this alumnus.</Text>
            ) : (
              openSlots.slice(0, 6).map((slot, idx) => {
                const selected = selectedSlotIndexes.includes(idx);
                return (
                  <TouchableOpacity
                    key={slot.start_utc}
                    style={[styles.slotOption, selected && styles.slotSelected]}
                    onPress={() => toggleSlot(idx)}
                  >
                    <Text style={[styles.slotText, selected && { color: '#FFFFFF' }]}>
                      {slot.local_label} ({new Date(slot.start_utc).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})
                    </Text>
                  </TouchableOpacity>
                );
              })
            )}
            <TouchableOpacity style={styles.primaryBtn} onPress={handleSubmitRequest}>
              <Text style={styles.primaryBtnText}>Submit Meeting Request</Text>
            </TouchableOpacity>
          </View>
        ) : null}

        <Text style={styles.sectionTitle}>Confirmed Meetings ({meetings.length})</Text>
        {loading ? (
          <ActivityIndicator color={Colors.primary} />
        ) : meetings.length === 0 ? (
          <EmptyStateView icon="📅" title="No Scheduled Meetings" subtitle="Confirmed consultations will appear here with room join access." />
        ) : (
          meetings.map((m) => (
            <View key={m.id} style={styles.card}>
              <Text style={styles.cardTitle}>{m.title}</Text>
              <Text style={styles.muted}>
                {m.student_name} ↔ {m.alumni_name} • {new Date(m.scheduled_start).toLocaleString()}
              </Text>
              <Text style={styles.statusText}>Status: {m.status.toUpperCase()}</Text>
              {(m.status === 'scheduled' || m.status === 'in_progress') ? (
                <View style={styles.row}>
                  <TouchableOpacity
                    style={[styles.actionBtn, { backgroundColor: Colors.success }]}
                    onPress={() => router.push(`/room/${m.id}` as Href)}
                  >
                    <Text style={styles.actionBtnText}>🎥 Join Room</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.actionBtn, { backgroundColor: Colors.error }]}
                    onPress={() => handleCancelMeeting(m.id)}
                  >
                    <Text style={styles.actionBtnText}>Cancel</Text>
                  </TouchableOpacity>
                </View>
              ) : null}
            </View>
          ))
        )}

        <Text style={[styles.sectionTitle, { marginTop: Spacing.md }]}>Meeting Requests ({requests.length})</Text>
        {requests.length === 0 ? (
          <EmptyStateView icon="🗓️" title="No Meeting Requests" subtitle="Propose slots with a verified alumnus to get started." />
        ) : (
          requests.map((r) => {
            const isAlumniRecipient = r.alumni_id === user?.id || primaryRole === 'alumni';
            return (
              <View key={r.id} style={styles.card}>
                <Text style={styles.cardTitle}>{r.title} ({r.status.toUpperCase()})</Text>
                <Text style={styles.muted}>{r.student_name} → {r.alumni_name} • {r.duration_minutes} min</Text>
                <Text style={styles.body}>{r.purpose}</Text>
                {r.slots.filter((s) => s.status === 'proposed').map((slot) => (
                  <View key={slot.id} style={styles.slotRow}>
                    <Text style={styles.slotMeta}>{new Date(slot.start_utc).toLocaleString()}</Text>
                    {isAlumniRecipient && r.status === 'pending' ? (
                      <TouchableOpacity style={styles.smallBtn} onPress={() => handleAcceptSlot(r.id, slot.id)}>
                        <Text style={styles.actionBtnText}>Accept Slot</Text>
                      </TouchableOpacity>
                    ) : null}
                    {!isAlumniRecipient && r.status === 'counter_proposed' ? (
                      <TouchableOpacity style={styles.smallBtn} onPress={() => handleConfirmCounter(r.id, slot.id)}>
                        <Text style={styles.actionBtnText}>Confirm</Text>
                      </TouchableOpacity>
                    ) : null}
                  </View>
                ))}
                {isAlumniRecipient && r.status === 'pending' ? (
                  <TouchableOpacity
                    style={[styles.actionBtn, { backgroundColor: Colors.error, alignSelf: 'flex-start', marginTop: 6 }]}
                    onPress={() => handleDecline(r.id)}
                  >
                    <Text style={styles.actionBtnText}>Decline Request</Text>
                  </TouchableOpacity>
                ) : null}
              </View>
            );
          })
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  headerBar: {
    backgroundColor: Colors.primary,
    paddingTop: 48,
    paddingBottom: 14,
    paddingHorizontal: Spacing.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  backText: { color: '#FFFFFF', fontWeight: '600' },
  headerTitle: { color: '#FFFFFF', fontSize: 16, fontWeight: 'bold' },
  newBtn: { color: Colors.accent, fontWeight: 'bold' },
  scrollContent: { padding: Spacing.md, paddingBottom: Spacing.xxl },
  sectionTitle: { fontSize: 15, fontWeight: 'bold', color: Colors.text, marginBottom: Spacing.xs },
  card: { backgroundColor: Colors.card, borderRadius: BorderRadius.md, padding: Spacing.md, marginBottom: Spacing.sm, borderWidth: 1, borderColor: Colors.border },
  cardTitle: { fontSize: 14, fontWeight: 'bold', color: Colors.text },
  muted: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  body: { fontSize: 12, color: Colors.text, marginTop: 4 },
  statusText: { fontSize: 11, fontWeight: 'bold', color: Colors.primary, marginTop: 4 },
  input: { backgroundColor: Colors.background, borderWidth: 1, borderColor: Colors.border, borderRadius: BorderRadius.sm, padding: Spacing.sm, marginBottom: Spacing.xs, color: Colors.text },
  subLabel: { fontSize: 12, fontWeight: '600', color: Colors.text, marginBottom: 6 },
  slotOption: { padding: Spacing.sm, borderRadius: BorderRadius.sm, borderWidth: 1, borderColor: Colors.border, marginBottom: 4 },
  slotSelected: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  slotText: { fontSize: 12, color: Colors.text },
  primaryBtn: { backgroundColor: Colors.primary, paddingVertical: 10, borderRadius: BorderRadius.sm, alignItems: 'center', marginTop: Spacing.xs },
  primaryBtnText: { color: '#FFFFFF', fontWeight: 'bold' },
  row: { flexDirection: 'row', gap: Spacing.xs, marginTop: Spacing.sm },
  actionBtn: { paddingHorizontal: Spacing.md, paddingVertical: 7, borderRadius: BorderRadius.sm },
  smallBtn: { backgroundColor: Colors.success, paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: BorderRadius.sm },
  actionBtnText: { color: '#FFFFFF', fontSize: 11, fontWeight: 'bold' },
  slotRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 6, paddingTop: 4, borderTopWidth: 1, borderTopColor: Colors.borderLight },
  slotMeta: { fontSize: 11, color: Colors.textSecondary },
});
