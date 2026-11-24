/**
 * MSGI One — Admin AI Provider Control Centre Screen (Phase 9)
 * Security Guarantee: Configures encrypted AES-256-GCM provider keys (Gemini, OpenAI,
 * Anthropic, DeepSeek), fallback priority, budgets, health checks, and usage telemetry.
 * Never receives or renders plaintext API keys back from the backend vault.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { api } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { Colors, Typography, Spacing, BorderRadius } from '../constants/theme';

type ProviderKind = 'gemini' | 'openai' | 'anthropic' | 'deepseek';

const DEFAULT_MODELS: Record<ProviderKind, string> = {
  gemini: 'gemini-2.5-flash',
  openai: 'gpt-4o-mini',
  anthropic: 'claude-3-5-sonnet-latest',
  deepseek: 'deepseek-chat',
};

export default function AdminAIScreen() {
  const router = useRouter();
  const { primaryRole } = useAuth();
  const [providers, setProviders] = useState<any[]>([]);
  const [usage, setUsage] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [selectedProvider, setSelectedProvider] = useState<ProviderKind>('gemini');
  const [displayName, setDisplayName] = useState('MSGI Primary Gemini');
  const [modelId, setModelId] = useState(DEFAULT_MODELS.gemini);
  const [apiKey, setApiKey] = useState('');
  const [dailyBudget, setDailyBudget] = useState('25');
  const [isPrimary, setIsPrimary] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [pRes, uRes] = await Promise.all([api.listAdminAIProviders(), api.getAdminAIUsage()]);
      setProviders(pRes || []);
      setUsage(uRes || null);
    } catch (err: any) {
      Alert.alert('Access Notice', err.message || 'Unable to load AI control centre.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (primaryRole !== 'admin') {
    return (
      <View style={styles.deniedBox}>
        <Text style={styles.deniedTitle}>Administrator Access Required</Text>
        <Text style={styles.deniedSub}>Only verified MSGI administrators may configure AI providers or view usage ledgers.</Text>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Text style={styles.backBtnText}>Return</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const handleSaveProvider = async () => {
    if (apiKey.trim().length < 6) {
      Alert.alert('Validation Error', 'Enter a valid API key (minimum 6 characters).');
      return;
    }
    setSubmitting(true);
    try {
      await api.upsertAdminAIProvider({
        provider: selectedProvider,
        display_name: displayName.trim() || `${selectedProvider.toUpperCase()} Provider`,
        model_id: modelId.trim() || DEFAULT_MODELS[selectedProvider],
        api_key: apiKey.trim(),
        is_primary: isPrimary,
        daily_budget_usd: Number(dailyBudget) || 25,
      });
      setApiKey(''); // Immediately clear sensitive input after encrypted vault submission
      await loadData();
      Alert.alert('Vault Updated', 'API key encrypted via AES-256-GCM and registered cleanly.');
    } catch (err: any) {
      Alert.alert('Save Error', err.message || 'Failed to save provider config.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerify = async (configId: string) => {
    try {
      const res = await api.verifyAdminAIProvider(configId);
      Alert.alert(res.healthy ? 'Provider Verified' : 'Verification Failed', res.message || res.status);
      await loadData();
    } catch (err: any) {
      Alert.alert('Verification Error', err.message || 'Check failed.');
    }
  };

  const handleDelete = async (configId: string) => {
    try {
      await api.deleteAdminAIProvider(configId);
      await loadData();
    } catch (err: any) {
      Alert.alert('Delete Error', err.message || 'Failed to remove provider.');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={styles.backLink}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Admin AI Control Centre</Text>
      </View>

      <Text style={styles.subNotice}>
        Encrypted Key Vault (AES-256-GCM) • Keys are write-only and masked immediately.
      </Text>

      {/* Usage & Budget Telemetry */}
      {usage && (
        <View style={styles.kpiRow}>
          <View style={styles.kpiCard}>
            <Text style={styles.kpiValue}>{usage.total_requests ?? 0}</Text>
            <Text style={styles.kpiLabel}>Total Calls</Text>
          </View>
          <View style={styles.kpiCard}>
            <Text style={styles.kpiValue}>{usage.total_tokens ?? 0}</Text>
            <Text style={styles.kpiLabel}>Tokens</Text>
          </View>
          <View style={styles.kpiCard}>
            <Text style={styles.kpiValue}>${Number(usage.total_cost_usd ?? 0).toFixed(4)}</Text>
            <Text style={styles.kpiLabel}>Est. Cost</Text>
          </View>
        </View>
      )}

      {/* Provider Config Form */}
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Configure AI Provider Key</Text>
        <View style={styles.providerPills}>
          {(['gemini', 'openai', 'anthropic', 'deepseek'] as ProviderKind[]).map((p) => (
            <TouchableOpacity
              key={p}
              style={[styles.pill, selectedProvider === p && styles.pillActive]}
              onPress={() => {
                setSelectedProvider(p);
                setModelId(DEFAULT_MODELS[p]);
                setDisplayName(`MSGI ${p.toUpperCase()}`);
              }}
            >
              <Text style={[styles.pillText, selectedProvider === p && styles.pillTextActive]}>
                {p.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <TextInput
          style={styles.input}
          placeholder="Display Name"
          placeholderTextColor={Colors.textMuted}
          value={displayName}
          onChangeText={setDisplayName}
        />
        <TextInput
          style={styles.input}
          placeholder="Model ID (e.g. gemini-2.5-flash)"
          placeholderTextColor={Colors.textMuted}
          value={modelId}
          onChangeText={setModelId}
        />
        <TextInput
          style={styles.input}
          placeholder="Secret API Key (write-only)"
          placeholderTextColor={Colors.textMuted}
          secureTextEntry
          value={apiKey}
          onChangeText={setApiKey}
          autoCapitalize="none"
        />
        <View style={styles.rowBetween}>
          <TextInput
            style={[styles.input, { flex: 1, marginRight: Spacing.sm }]}
            placeholder="Daily Budget USD"
            placeholderTextColor={Colors.textMuted}
            keyboardType="numeric"
            value={dailyBudget}
            onChangeText={setDailyBudget}
          />
          <TouchableOpacity
            style={[styles.pill, isPrimary && styles.pillActive]}
            onPress={() => setIsPrimary(!isPrimary)}
          >
            <Text style={[styles.pillText, isPrimary && styles.pillTextActive]}>
              {isPrimary ? 'Primary: ON' : 'Primary: OFF'}
            </Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={styles.primaryBtn} onPress={handleSaveProvider} disabled={submitting}>
          <Text style={styles.primaryBtnText}>{submitting ? 'Encrypting...' : 'Encrypt & Save Provider'}</Text>
        </TouchableOpacity>
      </View>

      {/* Configured Vault Entries */}
      <Text style={styles.sectionTitle}>Vault Registry ({providers.length})</Text>
      {loading ? (
        <ActivityIndicator color={Colors.primary} style={{ marginTop: 20 }} />
      ) : providers.length === 0 ? (
        <View style={styles.card}>
          <Text style={styles.meta}>No external keys configured. System runs in deterministic offline mode.</Text>
        </View>
      ) : (
        providers.map((cfg) => (
          <View key={cfg.id} style={styles.card}>
            <View style={styles.rowBetween}>
              <Text style={styles.cfgTitle}>{cfg.display_name}</Text>
              <Text style={styles.statusTag}>
                {cfg.is_primary ? 'PRIMARY' : `FALLBACK #${cfg.fallback_priority}`}
              </Text>
            </View>
            <Text style={styles.meta}>
              {cfg.provider.toUpperCase()} • {cfg.model_id} • Hint: {cfg.key_hint} (v{cfg.key_version})
            </Text>
            <Text style={styles.meta}>
              Health: {cfg.verification_status?.toUpperCase()} • Daily Budget: ${cfg.daily_budget_usd ?? 0}
            </Text>
            <View style={styles.actionRow}>
              <TouchableOpacity style={styles.verifyBtn} onPress={() => handleVerify(cfg.id)}>
                <Text style={styles.verifyBtnText}>Verify Health</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.revokeBtn} onPress={() => handleDelete(cfg.id)}>
                <Text style={styles.revokeBtnText}>Revoke Key</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: Spacing.md, paddingTop: 48, paddingBottom: 40 },
  headerRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
  backLink: { fontSize: 15, fontWeight: '700', color: Colors.primary, marginRight: Spacing.md },
  headerTitle: { fontSize: 20, fontWeight: '700', color: Colors.text },
  subNotice: { fontSize: 12, color: Colors.textMuted, marginBottom: Spacing.md },
  kpiRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.md },
  kpiCard: { flex: 1, backgroundColor: Colors.card, borderRadius: BorderRadius.md, padding: Spacing.sm, borderWidth: 1, borderColor: Colors.border, alignItems: 'center' },
  kpiValue: { fontSize: 16, fontWeight: '800', color: Colors.primary },
  kpiLabel: { fontSize: 11, color: Colors.textMuted },
  card: { backgroundColor: Colors.card, borderRadius: BorderRadius.lg, padding: Spacing.md, marginBottom: Spacing.md, borderWidth: 1, borderColor: Colors.border },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: Colors.text, marginBottom: Spacing.sm },
  providerPills: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: Spacing.sm },
  pill: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: BorderRadius.full, backgroundColor: Colors.background, borderWidth: 1, borderColor: Colors.border },
  pillActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  pillText: { fontSize: 11, fontWeight: '700', color: Colors.textSecondary },
  pillTextActive: { color: '#FFFFFF' },
  input: { backgroundColor: Colors.background, borderWidth: 1, borderColor: Colors.border, borderRadius: BorderRadius.md, paddingHorizontal: 12, paddingVertical: 9, marginBottom: Spacing.sm, color: Colors.text },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  primaryBtn: { backgroundColor: Colors.primary, paddingVertical: 12, borderRadius: BorderRadius.md, alignItems: 'center', marginTop: 4 },
  primaryBtnText: { color: '#FFFFFF', fontWeight: '700', fontSize: 14 },
  cfgTitle: { fontSize: 15, fontWeight: '700', color: Colors.text },
  statusTag: { fontSize: 10, fontWeight: '800', color: Colors.primary, backgroundColor: Colors.background, paddingHorizontal: 8, paddingVertical: 3, borderRadius: BorderRadius.sm },
  meta: { fontSize: 12, color: Colors.textSecondary, marginTop: 4 },
  actionRow: { flexDirection: 'row', gap: Spacing.sm, marginTop: Spacing.sm },
  verifyBtn: { flex: 1, backgroundColor: Colors.info, paddingVertical: 8, borderRadius: BorderRadius.sm, alignItems: 'center' },
  verifyBtnText: { color: '#FFFFFF', fontWeight: '700', fontSize: 12 },
  revokeBtn: { flex: 1, backgroundColor: Colors.error, paddingVertical: 8, borderRadius: BorderRadius.sm, alignItems: 'center' },
  revokeBtnText: { color: '#FFFFFF', fontWeight: '700', fontSize: 12 },
  deniedBox: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: Spacing.lg, backgroundColor: Colors.background },
  deniedTitle: { fontSize: 20, fontWeight: '700', color: Colors.error, marginBottom: 8 },
  deniedSub: { textAlign: 'center', color: Colors.textSecondary, marginBottom: Spacing.md },
  backBtn: { backgroundColor: Colors.primary, paddingHorizontal: 20, paddingVertical: 10, borderRadius: BorderRadius.md },
  backBtnText: { color: '#FFFFFF', fontWeight: '700' },
});
