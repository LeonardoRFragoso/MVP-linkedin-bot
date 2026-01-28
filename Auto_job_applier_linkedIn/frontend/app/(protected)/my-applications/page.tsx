'use client';

import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';

export default function MyApplicationsPage() {
  const { user } = useAuth();

  const { data: applicationsData, isLoading } = useQuery({
    queryKey: ['myApplications', user?.id],
    queryFn: () => user ? api.getUserApplications(user.id, { limit: 50 }) : [],
    enabled: !!user,
  });
  
  // Ensure applications is always an array
  const applications = Array.isArray(applicationsData) ? applicationsData : [];

  if (isLoading) {
    return <div className="p-8">Carregando...</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-2">Minhas Candidaturas</h1>
      <p className="text-muted-foreground mb-8">
        Histórico de todas as candidaturas realizadas pelo bot
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Total</div>
          <div className="text-2xl font-bold">{user?.total_applications || 0}</div>
        </div>
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Esta Semana</div>
          <div className="text-2xl font-bold text-primary">
            {applications.filter((a: any) => {
              const date = new Date(a.applied_at);
              const weekAgo = new Date();
              weekAgo.setDate(weekAgo.getDate() - 7);
              return date > weekAgo;
            }).length}
          </div>
        </div>
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Hoje</div>
          <div className="text-2xl font-bold text-green-600">
            {applications.filter((a: any) => {
              const date = new Date(a.applied_at);
              const today = new Date();
              return date.toDateString() === today.toDateString();
            }).length}
          </div>
        </div>
      </div>

      <div className="bg-card rounded-lg border">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="text-left p-4">Vaga</th>
              <th className="text-left p-4">Empresa</th>
              <th className="text-left p-4">Local</th>
              <th className="text-left p-4">Data</th>
              <th className="text-left p-4">Status</th>
            </tr>
          </thead>
          <tbody>
            {applications.map((app: any) => (
              <tr key={app.id} className="border-b hover:bg-muted/50">
                <td className="p-4">
                  <a
                    href={app.job_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    {app.job_title}
                  </a>
                </td>
                <td className="p-4">{app.company_name}</td>
                <td className="p-4 text-muted-foreground">{app.location}</td>
                <td className="p-4 text-muted-foreground">
                  {new Date(app.applied_at).toLocaleDateString('pt-BR')}
                </td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded text-xs ${
                    app.status === 'applied' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                      : 'bg-gray-100 dark:bg-gray-800'
                  }`}>
                    {app.status === 'applied' ? 'Enviada' : app.status}
                  </span>
                </td>
              </tr>
            ))}
            {applications.length === 0 && (
              <tr>
                <td colSpan={5} className="p-8 text-center text-muted-foreground">
                  Nenhuma candidatura ainda. Inicie o bot para começar!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
