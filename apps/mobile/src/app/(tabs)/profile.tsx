/**
 * MSGI One — Mobile User Profile & Account Settings Screen
 * Features: View profile, role badge, privacy compliance indicators, editable fields, and Sign Out.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../lib/api';
import { VerificationStatusResponse } from '../../types/business';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';

export default function ProfileScreen() {
  const { user, primaryRole, signOut, refreshProfile } = useAuth();

  const [isEditing, setIsEditing] = useState(false);
  const [firstName, setFirstName] = useState(user?.first_name || '');
  const [lastName, setLastName] = useState(user?.last_name || '');
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const [verificationStatus, setVerificationStatus] = useState<VerificationStatusResponse | null>(null);
  const [gradYear, setGradYear] = useState('2022');
  const [degree, setDegree] = useState('B.Tech Computer Science');
  const [department, setDepartment] = useState('Computer Science');
  const [submittingVerify, setSubmittingVerify] = useState(false);

  useEffect(() => {
    api.getMyVerificationStatus().then(setVerificationStatus).catch(() => null);
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    setSaveMessage(null);
    try {
      await api.updateMyProfile({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      });
      await refreshProfile();
      setSaveMessage('Profile successfully updated.');
      setIsEditing(false);
    } catch (err: any) {
      setSaveMessage(err.message || 'Failed to update profile.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSubmitAlumniVerification = async () => {
    setSubmittingVerify(true);
    setSaveMessage(null);
    try {
      await api.submitVerificationRequest({
        requested_role: 'alumni',
        graduation_year: Number(gradYear),
        degree: degree.trim(),
        department: department.trim(),
      });
      const latest = await api.getMyVerificationStatus();
      setVerificationStatus(latest);
      setSaveMessage('Institutional alumni verification request submitted for admin review.');
    } catch (err: any) {
      setSaveMessage(err.message || 'Verification submission failed.');
    } finally {
      setSubmittingVerify(false);
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (err: any) {
      console.error('Sign out error:', err);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      {/* Profile Header Card */}
      <View style={styles.profileCard}>
        <View style={styles.avatarCrest}>
          <Text style={styles.avatarText}>
            {user?.first_name ? user.first_name[0].toUpperCase() : 'M'}
          </Text>
        </View>

        <Text style={styles.fullName}>
          {user?.first_name ? `${user.first_name} ${user.last_name || ''}` : 'Institutional Member'}
        </Text>
        <Text style={styles.emailText}>{user?.email}</Text>

        <View style={styles.badgeRow}>
          <View style={styles.roleBadge}>
            <Text style={styles.roleBadgeText}>{primaryRole.toUpperCase()}</Text>
          </View>
          {user?.is_verified ? (
            <View style={styles.verifiedBadge}>
              <Text style={styles.verifiedBadgeText}>✓ VERIFIED</Text>
            </View>
          ) : (
            <View style={styles.unverifiedBadge}>
              <Text style={styles.unverifiedBadgeText}>UNVERIFIED</Text>
            </View>
          )}
        </View>
      </View>

      {/* Edit Profile Section */}
      <View style={styles.sectionCard}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Profile Details</Text>
          <TouchableOpacity onPress={() => setIsEditing(!isEditing)}>
            <Text style={styles.editActionText}>{isEditing ? 'Cancel' : 'Edit'}</Text>
          </TouchableOpacity>
        </View>

        {saveMessage && (
          <View style={styles.messageBanner}>
            <Text style={styles.messageText}>{saveMessage}</Text>
          </View>
        )}

        <View style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>First Name</Text>
          {isEditing ? (
            <TextInput
              style={styles.input}
              value={firstName}
              onChangeText={setFirstName}
              autoCapitalize="words"
            />
          ) : (
            <Text style={styles.fieldValue}>{user?.first_name || 'Not set'}</Text>
          )}
        </View>

        <View style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>Last Name</Text>
          {isEditing ? (
            <TextInput
              style={styles.input}
              value={lastName}
              onChangeText={setLastName}
              autoCapitalize="words"
            />
          ) : (
            <Text style={styles.fieldValue}>{user?.last_name || 'Not set'}</Text>
          )}
        </View>

        <View style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>Registered Email</Text>
          <Text style={styles.fieldValueReadOnly}>{user?.email} (Institutional Read-Only)</Text>
        </View>

        <View style={styles.fieldGroup}>
          <Text style={styles.fieldLabel}>Assigned Roles</Text>
          <Text style={styles.fieldValueReadOnly}>
            {user?.roles?.join(', ') || 'student'} (Server-Enforced RBAC)
          </Text>
        </View>

        {isEditing && (
          <TouchableOpacity
            style={[styles.saveButton, isSaving && styles.buttonDisabled]}
            onPress={handleSave}
            disabled={isSaving}
          >
            {isSaving ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.saveButtonText}>Save Changes</Text>
            )}
          </TouchableOpacity>
        )}
      </View>

      {/* FERPA / GDPR Privacy Notice */}
      <View style={styles.privacyCard}>
        <Text style={styles.privacyTitle}>🔒 Privacy & Compliance Assurance</Text>
        <Text style={styles.privacyText}>
          Under FERPA and institutional data policy, your email address, phone number, and physical
          coordinates are never exposed to public directory searches without your explicit consent.
        </Text>
      </View>

      {/* Institutional Verification Section for Unverified / Alumni Candidates */}
      {!user?.is_verified && primaryRole !== 'admin' && (
        <View style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Institutional Alumni Verification</Text>
          <Text style={styles.fieldValueReadOnly}>
            Current Status: {(verificationStatus?.overall_status || 'unverified').toUpperCase()}
          </Text>
          {verificationStatus?.overall_status !== 'pending' && (
            <View style={{ marginTop: Spacing.sm }}>
              <TextInput
                style={[styles.input, { marginBottom: Spacing.xs }]}
                value={gradYear}
                onChangeText={setGradYear}
                keyboardType="number-pad"
                placeholder="Graduation Year (e.g. 2022)"
              />
              <TextInput
                style={[styles.input, { marginBottom: Spacing.xs }]}
                value={degree}
                onChangeText={setDegree}
                placeholder="Degree (e.g. B.Tech)"
              />
              <TextInput
                style={[styles.input, { marginBottom: Spacing.sm }]}
                value={department}
                onChangeText={setDepartment}
                placeholder="Department"
              />
              <TouchableOpacity
                style={[styles.saveButton, submittingVerify && styles.buttonDisabled]}
                onPress={handleSubmitAlumniVerification}
                disabled={submittingVerify}
              >
                <Text style={styles.saveButtonText}>
                  {submittingVerify ? 'Submitting...' : 'Request Alumni Verification'}
                </Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      )}

      {/* Account Actions */}
      <View style={styles.actionsContainer}>
        <TouchableOpacity style={styles.signOutButton} onPress={handleSignOut}>
          <Text style={styles.signOutButtonText}>Sign Out</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: Spacing.xxl,
  },
  profileCard: {
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    alignItems: 'center',
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  avatarCrest: {
    width: 72,
    height: 72,
    borderRadius: BorderRadius.full,
    backgroundColor: Colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  avatarText: {
    fontSize: Typography.fontSize.title,
    fontWeight: 'bold',
    color: Colors.accent,
  },
  fullName: {
    fontSize: Typography.fontSize.xl,
    fontWeight: 'bold',
    color: Colors.text,
  },
  emailText: {
    fontSize: Typography.fontSize.sm,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  badgeRow: {
    flexDirection: 'row',
    gap: Spacing.xs,
    marginTop: Spacing.sm,
  },
  roleBadge: {
    backgroundColor: '#EFF6FF',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    borderRadius: BorderRadius.sm,
  },
  roleBadgeText: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: Colors.primary,
  },
  verifiedBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    borderRadius: BorderRadius.sm,
  },
  verifiedBadgeText: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: '#15803D',
  },
  unverifiedBadge: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    borderRadius: BorderRadius.sm,
  },
  unverifiedBadgeText: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: Colors.textMuted,
  },
  sectionCard: {
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  sectionTitle: {
    fontSize: Typography.fontSize.md,
    fontWeight: 'bold',
    color: Colors.text,
  },
  editActionText: {
    fontSize: Typography.fontSize.sm,
    fontWeight: 'bold',
    color: Colors.primary,
  },
  messageBanner: {
    backgroundColor: '#ECFDF5',
    padding: Spacing.sm,
    borderRadius: BorderRadius.sm,
    marginBottom: Spacing.md,
  },
  messageText: {
    color: '#065F46',
    fontSize: Typography.fontSize.xs,
  },
  fieldGroup: {
    marginBottom: Spacing.md,
  },
  fieldLabel: {
    fontSize: Typography.fontSize.xs,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  fieldValue: {
    fontSize: Typography.fontSize.md,
    color: Colors.text,
  },
  fieldValueReadOnly: {
    fontSize: Typography.fontSize.sm,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  input: {
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: BorderRadius.sm,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
    fontSize: Typography.fontSize.md,
    color: Colors.text,
  },
  saveButton: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.sm,
    paddingVertical: Spacing.sm,
    alignItems: 'center',
    marginTop: Spacing.xs,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: Typography.fontSize.sm,
  },
  privacyCard: {
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: '#BBF7D0',
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.lg,
  },
  privacyTitle: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: '#166534',
    marginBottom: 4,
  },
  privacyText: {
    fontSize: Typography.fontSize.xs,
    color: '#15803D',
    lineHeight: 16,
  },
  actionsContainer: {
    alignItems: 'center',
  },
  signOutButton: {
    width: '100%',
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FCA5A5',
    borderRadius: BorderRadius.md,
    paddingVertical: Spacing.md,
    alignItems: 'center',
  },
  signOutButtonText: {
    color: Colors.error,
    fontWeight: 'bold',
    fontSize: Typography.fontSize.md,
  },
});
