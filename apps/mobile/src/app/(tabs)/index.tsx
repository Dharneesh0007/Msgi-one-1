/**
 * MSGI One — Role-Aware Home Dashboard Orchestrator (Phase 4 Refactored)
 * Decomposed into StudentDashboard, AlumniDashboard, and AdminDashboard portals.
 */

import React from 'react';
import { ScrollView, RefreshControl, StyleSheet } from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { useDashboardData } from '../../hooks/useDashboardData';
import { StudentDashboard } from '../../components/dashboard/StudentDashboard';
import { AlumniDashboard } from '../../components/dashboard/AlumniDashboard';
import { AdminDashboard } from '../../components/dashboard/AdminDashboard';
import { Colors, Spacing } from '../../constants/theme';

export default function DashboardScreen() {
  const { user, primaryRole, refreshProfile } = useAuth();
  const dashboard = useDashboardData(user, primaryRole, refreshProfile);

  const renderPortal = () => {
    if (primaryRole === 'admin' || user?.roles?.includes('admin')) {
      return <AdminDashboard user={user} dashboard={dashboard} />;
    }
    if (primaryRole === 'alumni' || user?.roles?.includes('alumni')) {
      return <AlumniDashboard user={user} dashboard={dashboard} />;
    }
    return <StudentDashboard user={user} dashboard={dashboard} />;
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl
          refreshing={dashboard.refreshing}
          onRefresh={dashboard.onRefresh}
          colors={[Colors.primary]}
        />
      }
    >
      {renderPortal()}
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
});
