'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useTranslation } from '@/lib/app-context';

export default function DashboardPage() {
  const { t } = useTranslation();
  
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
  });

  const { data: tenants, isLoading: tenantsLoading } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => api.getTenants(),
  });

  const { data: questionStats, isLoading: statsLoading } = useQuery({
    queryKey: ['questionStats'],
    queryFn: () => api.getQuestionStats(),
  });

  const isLoading = healthLoading || tenantsLoading || statsLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">{t.common.loading}</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">{t.dashboard.title}</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title={t.dashboard.apiStatus}
          value={health?.status === 'healthy' ? t.dashboard.online : t.dashboard.offline}
          color={health?.status === 'healthy' ? 'text-green-600' : 'text-red-600'}
        />
        <StatCard
          title={t.dashboard.totalTenants}
          value={tenants?.length || 0}
        />
        <StatCard
          title={t.dashboard.totalQuestions}
          value={questionStats?.total_questions || 0}
        />
        <StatCard
          title={t.dashboard.verifiedQuestions}
          value={questionStats?.verified_questions || 0}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card rounded-lg border p-6">
          <h2 className="text-xl font-semibold mb-4">{t.dashboard.systemInfo}</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t.dashboard.database}</span>
              <span>{health?.database?.is_sqlite ? 'SQLite' : 'PostgreSQL'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t.dashboard.version}</span>
              <span>{health?.version}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t.dashboard.connection}</span>
              <span className={health?.database?.connected ? 'text-green-600' : 'text-red-600'}>
                {health?.database?.connected ? t.dashboard.connected : t.dashboard.disconnected}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-lg border p-6">
          <h2 className="text-xl font-semibold mb-4">{t.dashboard.questionsByType}</h2>
          <div className="space-y-2 text-sm">
            {questionStats?.by_type && Object.entries(questionStats.by_type).map(([type, count]) => (
              <div key={type} className="flex justify-between">
                <span className="text-muted-foreground capitalize">{type}</span>
                <span>{count as number}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, color }: { title: string; value: string | number; color?: string }) {
  return (
    <div className="bg-card rounded-lg border p-6">
      <div className="text-sm font-medium text-muted-foreground">{title}</div>
      <div className={`text-2xl font-bold mt-2 ${color || ''}`}>{value}</div>
    </div>
  );
}
