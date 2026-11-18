/**
 * MSGI One — MSGI AI Command Centre Screen (Phase 3)
 * Full interface for LangGraph Agentic AI orchestration, skill-gap analysis,
 * sequenced learning roadmaps, and Human-In-The-Loop (HITL) approval gateways.
 * Principles: Sommerville Requirements Traceability & Pressman Usability.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  Alert,
} from 'react-native';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { api } from '../../lib/api';

interface Message {
  id: string;
  role: 'ai' | 'user';
  text: string;
  timestamp: string;
  aiData?: any;
}

export default function AiScreen() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingApproval, setPendingApproval] = useState<any | null>(null);
  const [approvalSubmitting, setApprovalSubmitting] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome-001',
      role: 'ai',
      text: 'Welcome to MSGI AI Command Centre. I orchestrate alumni discovery, career skill-gap analysis, learning roadmaps, and mentor matching grounded in institutional data.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const samplePrompts = [
    'Analyze my skill gap for AI Engineer',
    'Recommend mentors for AI in Japan',
    'Generate learning roadmap for missing skills',
    'Apply to AI Research Intern at Rakuten Symphony',
  ];

  // Check for any outstanding pending approvals on mount
  useEffect(() => {
    loadPendingApprovals();
  }, []);

  const loadPendingApprovals = async () => {
    try {
      const res = await api.getPendingApprovals();
      if (res && res.length > 0) {
        setPendingApproval(res[0]);
      }
    } catch {
      // Non-blocking in offline / unauthenticated preview
    }
  };

  const handleSend = async (textToSend?: string) => {
    const promptText = (textToSend || query).trim();
    if (!promptText || loading) return;

    const userMsgId = `user-${Date.now()}`;
    const userMsg: Message = {
      id: userMsgId,
      role: 'user',
      text: promptText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const res = await api.chatWithAI(promptText);
      const aiMsgId = `ai-${Date.now()}`;
      const aiMsg: Message = {
        id: aiMsgId,
        role: 'ai',
        text: res.final_summary || 'Analysis complete.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        aiData: res,
      };

      setMessages((prev) => [...prev, aiMsg]);

      if (res.status === 'interrupted' && res.pending_approval) {
        setPendingApproval(res.pending_approval);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `ai-err-${Date.now()}`,
          role: 'ai',
          text: `Service Notice: ${err.message || 'Unable to connect to MSGI AI Command Centre.'}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleApprovalDecision = async (decision: 'approved' | 'rejected') => {
    if (!pendingApproval) return;
    setApprovalSubmitting(true);
    try {
      const res = await api.decideApproval(pendingApproval.id, decision);
      Alert.alert(
        decision === 'approved' ? 'Action Approved' : 'Action Cancelled',
        decision === 'approved'
          ? `Successfully executed ${pendingApproval.action_type} for ${pendingApproval.target_entity_name}.`
          : 'The action has been rejected and will not be executed.'
      );
      setPendingApproval(null);

      // Append result message to chat
      setMessages((prev) => [
        ...prev,
        {
          id: `approval-res-${Date.now()}`,
          role: 'ai',
          text: decision === 'approved'
            ? `Confirmation: Action '${pendingApproval.action_type}' for ${pendingApproval.target_entity_name} has been verified and executed.`
            : `Notice: Action '${pendingApproval.action_type}' was declined by user.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } catch (err: any) {
      Alert.alert('Approval Error', err.message || 'Failed to process decision.');
    } finally {
      setApprovalSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Top AI Command Bar */}
      <View style={styles.headerBar}>
        <View style={styles.headerStatusRow}>
          <View style={styles.statusDot} />
          <Text style={styles.headerTitle}>MSGI AI COMMAND CENTRE</Text>
        </View>
        <Text style={styles.headerSubtitle}>
          LangGraph Master Orchestrator • 10 Domain Tools Active • Rule 15 Safety Enabled
        </Text>
      </View>

      {/* Chat Messages and Structured Artifacts */}
      <ScrollView contentContainerStyle={styles.chatScroll}>
        {messages.map((msg) => (
          <View key={msg.id} style={styles.messageContainer}>
            <View
              style={[
                styles.messageBubble,
                msg.role === 'user' ? styles.userBubble : styles.aiBubble,
              ]}
            >
              <View style={styles.bubbleHeader}>
                <Text style={styles.bubbleSender}>
                  {msg.role === 'user' ? 'You' : 'MSGI AI Orchestrator'}
                </Text>
                <Text style={styles.bubbleTime}>{msg.timestamp}</Text>
              </View>
              <Text
                style={[
                  styles.bubbleText,
                  msg.role === 'user' ? styles.userBubbleText : styles.aiBubbleText,
                ]}
              >
                {msg.text}
              </Text>
            </View>

            {/* Render Structured Artifacts if attached to AI response */}
            {msg.aiData && (
              <View style={styles.artifactsContainer}>
                {/* 1. Skill Gap Analysis Artifact */}
                {msg.aiData.skill_gap && (
                  <View style={styles.artifactCard}>
                    <View style={styles.artifactHeader}>
                      <Text style={styles.artifactTitle}>
                        Competency Gap Analysis — {msg.aiData.skill_gap.target_role}
                      </Text>
                      <Text style={styles.matchScoreBadge}>
                        {msg.aiData.skill_gap.match_percentage}% MATCH
                      </Text>
                    </View>

                    {/* Progress Bar */}
                    <View style={styles.progressBarBackground}>
                      <View
                        style={[
                          styles.progressBarFill,
                          { width: `${msg.aiData.skill_gap.match_percentage}%` },
                        ]}
                      />
                    </View>

                    {/* Missing Skills */}
                    <Text style={styles.sectionHeading}>Target Competency Gaps:</Text>
                    <View style={styles.chipsRow}>
                      {msg.aiData.skill_gap.missing_skills?.map((s: any, idx: number) => (
                        <View key={idx} style={styles.missingSkillChip}>
                          <Text style={styles.missingSkillText}>
                            {s.skill_name} (Wt: {s.importance_weight})
                          </Text>
                        </View>
                      ))}
                    </View>

                    {/* Covered Skills */}
                    {msg.aiData.skill_gap.covered_skills?.length > 0 && (
                      <>
                        <Text style={[styles.sectionHeading, { marginTop: Spacing.sm }]}>
                          Acquired Baseline Skills:
                        </Text>
                        <View style={styles.chipsRow}>
                          {msg.aiData.skill_gap.covered_skills.map((s: any, idx: number) => (
                            <View key={idx} style={styles.coveredSkillChip}>
                              <Text style={styles.coveredSkillText}>✓ {s.skill_name}</Text>
                            </View>
                          ))}
                        </View>
                      </>
                    )}
                  </View>
                )}

                {/* 2. Sequenced Learning Roadmap Artifact */}
                {msg.aiData.learning_roadmap && msg.aiData.learning_roadmap.length > 0 && (
                  <View style={styles.artifactCard}>
                    <Text style={styles.artifactTitle}>
                      Sequenced Learning Roadmap ({msg.aiData.learning_roadmap.length} Milestones)
                    </Text>
                    {msg.aiData.learning_roadmap.map((step: any, idx: number) => (
                      <View key={idx} style={styles.roadmapStep}>
                        <View style={styles.stepNumberBadge}>
                          <Text style={styles.stepNumberText}>{step.step || idx + 1}</Text>
                        </View>
                        <View style={styles.stepContent}>
                          <Text style={styles.stepTitle}>{step.course_title}</Text>
                          <Text style={styles.stepMeta}>
                            {step.provider} • {step.duration_hours}h • {step.difficulty} • ★ {step.rating}
                          </Text>
                        </View>
                      </View>
                    ))}
                  </View>
                )}

                {/* 3. Recommended Mentors Artifact */}
                {msg.aiData.recommended_mentors && msg.aiData.recommended_mentors.length > 0 && (
                  <View style={styles.artifactCard}>
                    <Text style={styles.artifactTitle}>Verified Alumni Mentors</Text>
                    {msg.aiData.recommended_mentors.map((m: any, idx: number) => (
                      <View key={idx} style={styles.mentorItem}>
                        <View style={styles.mentorInfo}>
                          <Text style={styles.mentorName}>{m.full_name}</Text>
                          <Text style={styles.mentorRole}>
                            {m.current_title} at {m.current_company} ({m.country})
                          </Text>
                        </View>
                        <TouchableOpacity
                          style={styles.connectButton}
                          onPress={() => handleSend(`Send mentorship request to ${m.full_name}`)}
                        >
                          <Text style={styles.connectButtonText}>Connect</Text>
                        </TouchableOpacity>
                      </View>
                    ))}
                  </View>
                )}

                {/* 4. Evidence Grounding Audit */}
                {msg.aiData.evidence && msg.aiData.evidence.length > 0 && (
                  <View style={styles.evidenceAuditBar}>
                    <Text style={styles.evidenceTitle}>Ground-Truth Verification Sources:</Text>
                    {msg.aiData.evidence.map((ev: any, idx: number) => (
                      <Text key={idx} style={styles.evidenceItem}>
                        • {ev.source} ({ev.count !== undefined ? `${ev.count} records verified` : 'confirmed'})
                      </Text>
                    ))}
                  </View>
                )}
              </View>
            )}
          </View>
        ))}

        {loading && (
          <View style={styles.loadingBubble}>
            <ActivityIndicator size="small" color={Colors.primary} />
            <Text style={styles.loadingText}>Orchestrating agents and querying tools...</Text>
          </View>
        )}
      </ScrollView>

      {/* Suggested Goal Prompts */}
      <View style={styles.promptSuggestions}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {samplePrompts.map((prompt, idx) => (
            <TouchableOpacity
              key={idx}
              style={styles.suggestionPill}
              onPress={() => handleSend(prompt)}
            >
              <Text style={styles.suggestionText}>{prompt}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Chat Input Bar */}
      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          placeholder="State your career or alumni networking goal..."
          placeholderTextColor={Colors.textMuted}
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={() => handleSend()}
        />
        <TouchableOpacity
          style={[styles.sendButton, loading && styles.sendButtonDisabled]}
          onPress={() => handleSend()}
          disabled={loading}
        >
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>

      {/* Rule 15: Human-In-The-Loop Consequential Action Modal */}
      {pendingApproval && (
        <Modal
          visible={!!pendingApproval}
          transparent={true}
          animationType="fade"
          onRequestClose={() => setPendingApproval(null)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalCard}>
              <View style={styles.modalAlertHeader}>
                <Text style={styles.modalAlertBadge}>HUMAN-IN-THE-LOOP REQUIRED</Text>
                <Text style={styles.ruleNotice}>Safety Law 15: Consequential Action Gate</Text>
              </View>

              <Text style={styles.modalPrompt}>
                The AI Command Centre has prepared an institutional action that requires your explicit confirmation:
              </Text>

              <View style={styles.approvalDetailBox}>
                <Text style={styles.approvalDetailLabel}>Action Type:</Text>
                <Text style={styles.approvalDetailVal}>{pendingApproval.action_type}</Text>

                <Text style={styles.approvalDetailLabel}>Target Entity:</Text>
                <Text style={styles.approvalDetailVal}>{pendingApproval.target_entity_name}</Text>

                <Text style={styles.approvalDetailLabel}>Entity ID:</Text>
                <Text style={styles.approvalDetailVal}>{pendingApproval.target_entity_id}</Text>
              </View>

              {approvalSubmitting ? (
                <ActivityIndicator size="small" color={Colors.primary} style={{ marginVertical: Spacing.md }} />
              ) : (
                <View style={styles.modalActionButtons}>
                  <TouchableOpacity
                    style={[styles.modalButton, styles.rejectButton]}
                    onPress={() => handleApprovalDecision('rejected')}
                  >
                    <Text style={styles.rejectButtonText}>Reject / Cancel</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.modalButton, styles.approveButton]}
                    onPress={() => handleApprovalDecision('approved')}
                  >
                    <Text style={styles.approveButtonText}>Confirm & Execute</Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
          </View>
        </Modal>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  headerBar: {
    backgroundColor: '#0F172A',
    padding: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  headerStatusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#10B981',
  },
  headerTitle: {
    fontSize: Typography.fontSize.sm,
    fontWeight: 'bold',
    color: '#F8FAFC',
    letterSpacing: 0.5,
  },
  headerSubtitle: {
    fontSize: Typography.fontSize.xs,
    color: '#94A3B8',
  },
  chatScroll: {
    padding: Spacing.md,
    paddingBottom: Spacing.xl,
  },
  messageContainer: {
    marginBottom: Spacing.md,
  },
  messageBubble: {
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    maxWidth: '90%',
  },
  aiBubble: {
    backgroundColor: Colors.card,
    borderWidth: 1,
    borderColor: Colors.border,
    alignSelf: 'flex-start',
  },
  userBubble: {
    backgroundColor: Colors.primary,
    alignSelf: 'flex-end',
  },
  bubbleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  bubbleSender: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.textMuted,
    textTransform: 'uppercase',
  },
  bubbleTime: {
    fontSize: 10,
    color: Colors.textMuted,
    marginLeft: 8,
  },
  bubbleText: {
    fontSize: Typography.fontSize.sm,
    lineHeight: 20,
  },
  aiBubbleText: {
    color: Colors.text,
  },
  userBubbleText: {
    color: '#FFFFFF',
  },
  artifactsContainer: {
    marginTop: Spacing.sm,
    gap: Spacing.sm,
  },
  artifactCard: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
  },
  artifactHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  artifactTitle: {
    fontSize: Typography.fontSize.sm,
    fontWeight: 'bold',
    color: Colors.text,
    flex: 1,
  },
  matchScoreBadge: {
    backgroundColor: '#DEF7EC',
    color: '#03543F',
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  progressBarBackground: {
    height: 8,
    backgroundColor: '#E2E8F0',
    borderRadius: 4,
    marginVertical: Spacing.xs,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: Colors.primary,
    borderRadius: 4,
  },
  sectionHeading: {
    fontSize: Typography.fontSize.xs,
    fontWeight: '600',
    color: Colors.textMuted,
    marginTop: Spacing.xs,
    marginBottom: 4,
  },
  chipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  missingSkillChip: {
    backgroundColor: '#FEF3C7',
    borderWidth: 1,
    borderColor: '#FCD34D',
    borderRadius: BorderRadius.full,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  missingSkillText: {
    fontSize: Typography.fontSize.xs,
    color: '#92400E',
    fontWeight: '500',
  },
  coveredSkillChip: {
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
    borderRadius: BorderRadius.full,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  coveredSkillText: {
    fontSize: Typography.fontSize.xs,
    color: '#065F46',
    fontWeight: '500',
  },
  roadmapStep: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Spacing.sm,
    marginTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    paddingTop: Spacing.xs,
  },
  stepNumberBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepNumberText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: 'bold',
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: Typography.fontSize.xs,
    fontWeight: '600',
    color: Colors.text,
  },
  stepMeta: {
    fontSize: 11,
    color: Colors.textMuted,
    marginTop: 2,
  },
  mentorItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    paddingTop: Spacing.xs,
  },
  mentorInfo: {
    flex: 1,
  },
  mentorName: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: Colors.text,
  },
  mentorRole: {
    fontSize: 11,
    color: Colors.textMuted,
  },
  connectButton: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: BorderRadius.sm,
  },
  connectButtonText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: 'bold',
  },
  evidenceAuditBar: {
    backgroundColor: '#F1F5F9',
    padding: Spacing.sm,
    borderRadius: BorderRadius.sm,
    borderLeftWidth: 3,
    borderLeftColor: Colors.primary,
  },
  evidenceTitle: {
    fontSize: 11,
    fontWeight: 'bold',
    color: Colors.textMuted,
    marginBottom: 2,
  },
  evidenceItem: {
    fontSize: 10,
    color: '#64748B',
  },
  loadingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    padding: Spacing.md,
    alignSelf: 'flex-start',
  },
  loadingText: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textMuted,
    fontStyle: 'italic',
  },
  promptSuggestions: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    backgroundColor: Colors.card,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
  },
  suggestionPill: {
    backgroundColor: '#F1F5F9',
    borderRadius: BorderRadius.full,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
    marginRight: Spacing.xs,
  },
  suggestionText: {
    fontSize: Typography.fontSize.xs,
    color: Colors.primary,
    fontWeight: '500',
  },
  inputBar: {
    flexDirection: 'row',
    padding: Spacing.md,
    backgroundColor: Colors.card,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    alignItems: 'center',
    gap: Spacing.sm,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: BorderRadius.md,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    fontSize: Typography.fontSize.sm,
    color: Colors.text,
  },
  sendButton: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.md,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: Typography.fontSize.sm,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.lg,
  },
  modalCard: {
    width: '100%',
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  modalAlertHeader: {
    marginBottom: Spacing.md,
  },
  modalAlertBadge: {
    color: '#DC2626',
    fontWeight: 'bold',
    fontSize: Typography.fontSize.xs,
    letterSpacing: 0.5,
  },
  ruleNotice: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textMuted,
    marginTop: 2,
  },
  modalPrompt: {
    fontSize: Typography.fontSize.sm,
    color: Colors.text,
    lineHeight: 20,
    marginBottom: Spacing.md,
  },
  approvalDetailBox: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.lg,
  },
  approvalDetailLabel: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.textMuted,
    textTransform: 'uppercase',
  },
  approvalDetailVal: {
    fontSize: Typography.fontSize.xs,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 6,
  },
  modalActionButtons: {
    flexDirection: 'row',
    gap: Spacing.md,
  },
  modalButton: {
    flex: 1,
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
  },
  rejectButton: {
    backgroundColor: '#F1F5F9',
  },
  rejectButtonText: {
    color: '#475569',
    fontWeight: '600',
    fontSize: Typography.fontSize.sm,
  },
  approveButton: {
    backgroundColor: '#10B981',
  },
  approveButtonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: Typography.fontSize.sm,
  },
});
