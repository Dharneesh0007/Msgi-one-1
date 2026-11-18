/**
 * MSGI One — MSGI AI Command Centre Screen (Phase 4 Preview)
 * Interface for LangGraph agentic workflow execution.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
} from 'react-native';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';

export default function AiScreen() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'ai' | 'user'; text: string }>>([
    {
      role: 'ai',
      text: 'Hello! I am the MSGI One Autonomous Alumni Agent. How can I assist your career and networking goals today?',
    },
  ]);

  const samplePrompts = [
    'Find alumni in Tokyo working on AI/ML',
    'Recommend mentors for Software Engineering',
    'Review my profile for alumni referral readiness',
  ];

  const handleSend = () => {
    if (!query.trim()) return;

    const userText = query.trim();
    setMessages((prev) => [
      ...prev,
      { role: 'user', text: userText },
      {
        role: 'ai',
        text: `[Phase 4 Agentic Hook] In Phase 4, your request "${userText}" will invoke the LangGraph Supervisor Agent with semantic retrieval over pgvector and tool-calling execution.`,
      },
    ]);
    setQuery('');
  };

  return (
    <View style={styles.container}>
      {/* Notice Banner */}
      <View style={styles.phaseNotice}>
        <Text style={styles.phaseBadge}>LANGGRAPH AGENT ARCHITECTURE</Text>
        <Text style={styles.phaseText}>
          The AI Command Centre multi-agent graph (Supervisor + Matching Agent + Content Agent)
          is documented in docs/SYSTEM_ARCHITECTURE.md and will be fully wired in Phase 4.
        </Text>
      </View>

      {/* Chat Messages */}
      <ScrollView contentContainerStyle={styles.chatScroll}>
        {messages.map((msg, idx) => (
          <View
            key={idx}
            style={[
              styles.messageBubble,
              msg.role === 'user' ? styles.userBubble : styles.aiBubble,
            ]}
          >
            <Text style={styles.bubbleSender}>
              {msg.role === 'user' ? 'You' : 'MSGI AI Agent'}
            </Text>
            <Text
              style={[
                styles.bubbleText,
                msg.role === 'user' ? styles.userBubbleText : styles.aiBubbleText,
              ]}
            >
              {msg.text}
            </Text>
          </View>
        ))}
      </ScrollView>

      {/* Suggested Prompts */}
      <View style={styles.promptSuggestions}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {samplePrompts.map((prompt, idx) => (
            <TouchableOpacity
              key={idx}
              style={styles.suggestionPill}
              onPress={() => setQuery(prompt)}
            >
              <Text style={styles.suggestionText}>{prompt}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Input Box */}
      <View style={styles.inputBar}>
        <TextInput
          style={styles.input}
          placeholder="Ask MSGI AI Command Centre..."
          placeholderTextColor={Colors.textMuted}
          value={query}
          onChangeText={setQuery}
        />
        <TouchableOpacity style={styles.sendButton} onPress={handleSend}>
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  phaseNotice: {
    backgroundColor: '#0F172A',
    padding: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  phaseBadge: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: Colors.accent,
    marginBottom: 2,
  },
  phaseText: {
    fontSize: Typography.fontSize.xs,
    color: '#94A3B8',
    lineHeight: 16,
  },
  chatScroll: {
    padding: Spacing.md,
    paddingBottom: Spacing.md,
  },
  messageBubble: {
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    maxWidth: '85%',
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
  bubbleSender: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.textMuted,
    textTransform: 'uppercase',
    marginBottom: 4,
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
  sendButtonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: Typography.fontSize.sm,
  },
});
