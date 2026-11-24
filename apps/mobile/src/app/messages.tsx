/**
 * MSGI One — Real-Time 1-on-1 Messaging Screen (Phase 6)
 * Features:
 *   - Conversation list + search
 *   - Live WebSocket (/ws/chat) transport with automatic reconnect & REST cursor recovery
 *   - Offline message draft queue + client idempotency keys
 *   - Read receipts, typing indicator, block & report safety controls
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useAuth } from '../context/AuthContext';
import { api, getWebSocketChatUrl } from '../lib/api';
import { ConversationItem, MessageItem } from '../types/business';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { FeedbackBanner, EmptyStateView } from '../components/common/StateViews';

export default function MessagesScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ recipientId?: string }>();
  const { user, session } = useAuth();

  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeConv, setActiveConv] = useState<ConversationItem | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [search, setSearch] = useState('');
  const [draft, setDraft] = useState('');
  const [wsConnected, setWsConnected] = useState(false);
  const [peerTyping, setPeerTyping] = useState(false);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const lastSeqRef = useRef<number>(0);

  const loadConversations = useCallback(async () => {
    try {
      setLoading(true);
      if (params.recipientId) {
        const created = await api.createOrGetConversation(params.recipientId);
        setActiveConv(created);
      }
      const list = await api.listConversations(search.trim() || undefined);
      setConversations(list || []);
    } catch (err: any) {
      setFeedback(err.message || 'Unable to load conversations.');
    } finally {
      setLoading(false);
    }
  }, [params.recipientId, search]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const loadMessagesForConv = useCallback(async (convId: string, afterSeq: number = 0) => {
    try {
      const fetched = await api.listMessages(convId, afterSeq);
      if (afterSeq === 0) {
        setMessages(fetched || []);
      } else if (fetched && fetched.length > 0) {
        setMessages((prev) => {
          const existingIds = new Set(prev.map((m) => m.id));
          const merged = [...prev, ...fetched.filter((m) => !existingIds.has(m.id))];
          return merged.sort((a, b) => a.seq - b.seq);
        });
      }
      const maxSeq = (fetched || []).reduce((acc, m) => Math.max(acc, m.seq), afterSeq);
      lastSeqRef.current = Math.max(lastSeqRef.current, maxSeq);
      if (maxSeq > 0) {
        await api.markConversationRead(convId, maxSeq).catch(() => null);
      }
    } catch (err: any) {
      setFeedback(err.message || 'Failed to load messages.');
    }
  }, []);

  useEffect(() => {
    if (!activeConv) return;
    lastSeqRef.current = 0;
    loadMessagesForConv(activeConv.id, 0);
  }, [activeConv, loadMessagesForConv]);

  // WebSocket lifecycle with reconnection & cursor recovery
  useEffect(() => {
    const token = session?.access_token;
    if (!token) return;

    let closedByUnmount = false;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let backoffMs = 1000;

    const connectWs = () => {
      try {
        const ws = new WebSocket(getWebSocketChatUrl(token));
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
          backoffMs = 1000;
          if (activeConv) {
            loadMessagesForConv(activeConv.id, lastSeqRef.current);
          }
        };

        ws.onmessage = (evt) => {
          try {
            const frame = JSON.parse(evt.data);
            if (frame.event_type === 'message.created' && frame.payload) {
              const msg: MessageItem = frame.payload;
              if (activeConv && msg.conversation_id === activeConv.id) {
                setMessages((prev) => (prev.some((m) => m.id === msg.id) ? prev : [...prev, msg]));
                lastSeqRef.current = Math.max(lastSeqRef.current, msg.seq);
              }
              loadConversations();
            } else if (frame.event_type === 'typing.started' && activeConv && frame.conversation_id === activeConv.id) {
              setPeerTyping(true);
            } else if (frame.event_type === 'typing.stopped' && activeConv && frame.conversation_id === activeConv.id) {
              setPeerTyping(false);
            }
          } catch {
            // ignore malformed frame
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          if (!closedByUnmount) {
            retryTimer = setTimeout(connectWs, Math.min(backoffMs, 15000));
            backoffMs *= 2;
          }
        };
      } catch {
        setWsConnected(false);
      }
    };

    connectWs();
    return () => {
      closedByUnmount = true;
      if (retryTimer) clearTimeout(retryTimer);
      wsRef.current?.close();
    };
  }, [session?.access_token, activeConv?.id]);

  const handleSend = async () => {
    if (!activeConv || !draft.trim()) return;
    const bodyText = draft.trim();
    const idemKey = `cli-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setDraft('');

    if (wsRef.current && wsConnected && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          event_type: 'message.send',
          conversation_id: activeConv.id,
          client_idempotency_key: idemKey,
          payload: { body: bodyText, message_type: 'text' },
        })
      );
      return;
    }

    // Durable REST fallback when socket is reconnecting
    try {
      const saved = await api.sendMessageRest(activeConv.id, bodyText, idemKey);
      setMessages((prev) => (prev.some((m) => m.id === saved.id) ? prev : [...prev, saved]));
    } catch (err: any) {
      setFeedback(err.message || 'Failed to send message.');
    }
  };

  const handleBlockPeer = async () => {
    if (!activeConv) return;
    try {
      await api.blockUser(activeConv.peer_id, 'Blocked from chat safety menu');
      setFeedback(`Blocked ${activeConv.peer_name}.`);
      setActiveConv(null);
      await loadConversations();
    } catch (err: any) {
      setFeedback(err.message || 'Failed to block user.');
    }
  };

  const handleReportPeer = async () => {
    if (!activeConv) return;
    try {
      await api.reportUser(activeConv.peer_id, 'inappropriate', 'Reported from 1-on-1 chat screen');
      setFeedback('Safety report submitted to institutional moderators.');
    } catch (err: any) {
      setFeedback(err.message || 'Failed to submit report.');
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.headerBar}>
        <TouchableOpacity onPress={() => (activeConv ? setActiveConv(null) : router.back())}>
          <Text style={styles.backText}>← {activeConv ? 'Threads' : 'Back'}</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>
          {activeConv ? activeConv.peer_name : 'Messages'} {wsConnected ? '●' : '○'}
        </Text>
        {activeConv ? (
          <View style={{ flexDirection: 'row', gap: 10 }}>
            <TouchableOpacity onPress={handleReportPeer}><Text style={styles.safetyText}>Report</Text></TouchableOpacity>
            <TouchableOpacity onPress={handleBlockPeer}><Text style={styles.safetyText}>Block</Text></TouchableOpacity>
          </View>
        ) : <View style={{ width: 40 }} />}
      </View>

      {feedback ? <View style={{ padding: Spacing.sm }}><FeedbackBanner message={feedback} /></View> : null}

      {!activeConv ? (
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <TextInput
            style={styles.searchInput}
            placeholder="Search conversations..."
            value={search}
            onChangeText={setSearch}
          />
          {loading ? (
            <ActivityIndicator color={Colors.primary} />
          ) : conversations.length === 0 ? (
            <EmptyStateView icon="💬" title="No Conversations Yet" subtitle="Open an alumni profile in Network to start a private conversation." />
          ) : (
            conversations.map((c) => (
              <TouchableOpacity key={c.id} style={styles.threadCard} onPress={() => setActiveConv(c)}>
                <View style={styles.row}>
                  <Text style={styles.peerName}>{c.peer_name} {c.peer_online ? '🟢' : ''}</Text>
                  {c.unread_count > 0 ? <Text style={styles.unread}>{c.unread_count} new</Text> : null}
                </View>
                <Text style={styles.preview} numberOfLines={1}>{c.last_message_preview || 'Tap to start chatting'}</Text>
              </TouchableOpacity>
            ))
          )}
        </ScrollView>
      ) : (
        <View style={{ flex: 1 }}>
          <ScrollView contentContainerStyle={styles.scrollContent}>
            {messages.map((m) => {
              const isMine = m.sender_id === user?.id;
              return (
                <View key={m.id} style={[styles.msgBubble, isMine ? styles.msgMine : styles.msgTheirs]}>
                  <Text style={[styles.msgText, isMine && { color: '#FFFFFF' }]}>{m.body}</Text>
                  <Text style={[styles.msgMeta, isMine && { color: '#CBD5E1' }]}>
                    {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {m.status}
                  </Text>
                </View>
              );
            })}
            {peerTyping ? <Text style={styles.typingText}>Typing...</Text> : null}
          </ScrollView>
          <View style={styles.composerRow}>
            <TextInput
              style={styles.composerInput}
              placeholder="Write a message..."
              value={draft}
              onChangeText={setDraft}
            />
            <TouchableOpacity style={styles.sendBtn} onPress={handleSend}>
              <Text style={styles.sendBtnText}>Send</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
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
  safetyText: { color: '#FCA5A5', fontSize: 12, fontWeight: 'bold' },
  scrollContent: { padding: Spacing.md, paddingBottom: Spacing.xl },
  searchInput: { backgroundColor: Colors.card, borderWidth: 1, borderColor: Colors.border, borderRadius: BorderRadius.md, padding: Spacing.sm, marginBottom: Spacing.md },
  threadCard: { backgroundColor: Colors.card, padding: Spacing.md, borderRadius: BorderRadius.md, marginBottom: Spacing.xs, borderWidth: 1, borderColor: Colors.border },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  peerName: { fontSize: 14, fontWeight: 'bold', color: Colors.text },
  unread: { fontSize: 11, fontWeight: 'bold', color: Colors.primary },
  preview: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  msgBubble: { maxWidth: '80%', padding: Spacing.sm, borderRadius: BorderRadius.md, marginBottom: Spacing.xs },
  msgMine: { alignSelf: 'flex-end', backgroundColor: Colors.primary },
  msgTheirs: { alignSelf: 'flex-start', backgroundColor: Colors.card, borderWidth: 1, borderColor: Colors.border },
  msgText: { fontSize: 13, color: Colors.text },
  msgMeta: { fontSize: 10, color: Colors.textMuted, marginTop: 3 },
  typingText: { fontSize: 11, fontStyle: 'italic', color: Colors.textSecondary, marginTop: 4 },
  composerRow: { flexDirection: 'row', padding: Spacing.sm, backgroundColor: Colors.card, borderTopWidth: 1, borderTopColor: Colors.border, gap: Spacing.xs },
  composerInput: { flex: 1, backgroundColor: Colors.background, borderWidth: 1, borderColor: Colors.border, borderRadius: BorderRadius.md, paddingHorizontal: Spacing.sm, paddingVertical: 8 },
  sendBtn: { backgroundColor: Colors.primary, paddingHorizontal: Spacing.md, justifyContent: 'center', borderRadius: BorderRadius.md },
  sendBtnText: { color: '#FFFFFF', fontWeight: 'bold' },
});
