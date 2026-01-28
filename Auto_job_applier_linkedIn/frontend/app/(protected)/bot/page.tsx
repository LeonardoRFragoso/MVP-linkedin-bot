'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth-context';
import { useTranslation } from '@/lib/app-context';
import { api } from '@/lib/api';

interface BotLog {
  id: string;
  timestamp: string;
  level: 'info' | 'success' | 'warning' | 'error';
  message: string;
  details?: any;
}

interface BotStatus {
  is_running: boolean;
  current_action?: string;
  jobs_applied_today: number;
  jobs_applied_total: number;
  current_job?: {
    title: string;
    company: string;
    location: string;
  };
  started_at?: string;
  last_activity?: string;
}

export default function BotPage() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Fetch bot status every 3 seconds
  const { data: botStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['botStatus'],
    queryFn: () => api.getBotStatus(),
    refetchInterval: 3000,
  });

  // Fetch logs every 2 seconds
  const { data: logs = [] } = useQuery({
    queryKey: ['botLogs'],
    queryFn: () => api.getBotLogs({ limit: 100 }),
    refetchInterval: 2000,
  });

  // Start bot mutation
  const startMutation = useMutation({
    mutationFn: () => api.startBot(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['botStatus'] });
    },
  });

  // Stop bot mutation
  const stopMutation = useMutation({
    mutationFn: () => api.stopBot(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['botStatus'] });
    },
  });

  // Auto-scroll to bottom of logs
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const getLogColor = (level: string) => {
    switch (level) {
      case 'success': return 'text-green-600 dark:text-green-400';
      case 'warning': return 'text-yellow-600 dark:text-yellow-400';
      case 'error': return 'text-red-600 dark:text-red-400';
      default: return 'text-muted-foreground';
    }
  };

  const getLogIcon = (level: string) => {
    switch (level) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return '📋';
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('pt-BR');
  };

  return (
    <div className="p-8">
      {/* Important Notices */}
      <div className="space-y-3 mb-6">
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-xl">💼</span>
            <div>
              <p className="font-medium text-blue-800 dark:text-blue-200">Plataforma exclusiva LinkedIn</p>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Este bot trabalha exclusivamente com vagas do LinkedIn Easy Apply. Certifique-se de que suas credenciais do LinkedIn estão configuradas.
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-xl">🌐</span>
            <div>
              <p className="font-medium text-amber-800 dark:text-amber-200">Navegador será aberto automaticamente</p>
              <p className="text-sm text-amber-700 dark:text-amber-300">
                Ao iniciar o bot, uma janela do Chrome será aberta automaticamente para realizar as candidaturas. 
                <strong> Não feche esta janela</strong> enquanto o bot estiver em execução.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Painel do Bot</h1>
          <p className="text-muted-foreground">
            Acompanhe a execução das candidaturas em tempo real
          </p>
        </div>
        <div className="flex gap-2">
          {botStatus?.is_running ? (
            <button
              onClick={() => stopMutation.mutate()}
              disabled={stopMutation.isPending}
              className="px-6 py-2 bg-destructive text-destructive-foreground rounded-lg font-medium flex items-center gap-2"
            >
              <span className="animate-pulse">🔴</span>
              {stopMutation.isPending ? 'Parando...' : 'Parar Bot'}
            </button>
          ) : (
            <button
              onClick={() => startMutation.mutate()}
              disabled={startMutation.isPending}
              className="px-6 py-2 bg-green-600 text-white rounded-lg font-medium flex items-center gap-2"
            >
              <span>▶️</span>
              {startMutation.isPending ? 'Iniciando...' : 'Iniciar Bot'}
            </button>
          )}
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Status</div>
          <div className="flex items-center gap-2 mt-1">
            <span className={`w-3 h-3 rounded-full ${botStatus?.is_running ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
            <span className="text-xl font-bold">
              {botStatus?.is_running ? 'Executando' : 'Parado'}
            </span>
          </div>
        </div>
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Candidaturas Hoje</div>
          <div className="text-2xl font-bold text-primary">
            {botStatus?.jobs_applied_today || 0}
          </div>
        </div>
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Total de Candidaturas</div>
          <div className="text-2xl font-bold">
            {botStatus?.jobs_applied_total || user?.total_applications || 0}
          </div>
        </div>
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Última Atividade</div>
          <div className="text-lg font-medium">
            {botStatus?.last_activity ? formatTime(botStatus.last_activity) : '-'}
          </div>
        </div>
      </div>

      {/* Current Action */}
      {botStatus?.is_running && botStatus.current_job && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-8">
          <div className="flex items-center gap-3">
            <div className="animate-spin text-2xl">⚙️</div>
            <div>
              <div className="font-medium">{botStatus.current_action || 'Processando candidatura...'}</div>
              <div className="text-sm text-muted-foreground">
                {botStatus.current_job.title} • {botStatus.current_job.company} • {botStatus.current_job.location}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Logs */}
      <div className="bg-card rounded-lg border">
        <div className="flex justify-between items-center p-4 border-b">
          <h2 className="text-lg font-semibold">Logs de Execução</h2>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="rounded"
            />
            Auto-scroll
          </label>
        </div>
        <div className="h-96 overflow-y-auto p-4 font-mono text-sm bg-muted/30">
          {logs.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              Nenhum log disponível. Inicie o bot para ver a execução.
            </div>
          ) : (
            logs.map((log: BotLog, index: number) => (
              <div key={log.id || index} className={`flex gap-2 py-1 ${getLogColor(log.level)}`}>
                <span className="text-muted-foreground w-20 shrink-0">
                  {formatTime(log.timestamp)}
                </span>
                <span>{getLogIcon(log.level)}</span>
                <span>{log.message}</span>
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <div className="bg-card rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-4">Candidaturas Recentes</h2>
          <div className="space-y-3">
            {logs
              .filter((log: BotLog) => log.level === 'success' && log.message.includes('candidatura'))
              .slice(-5)
              .map((log: BotLog, index: number) => (
                <div key={index} className="flex items-center gap-3 text-sm">
                  <span className="text-green-500">✅</span>
                  <span>{log.message}</span>
                </div>
              ))}
            {logs.filter((log: BotLog) => log.level === 'success').length === 0 && (
              <p className="text-muted-foreground text-sm">
                Nenhuma candidatura realizada ainda.
              </p>
            )}
          </div>
        </div>

        <div className="bg-card rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-4">Configurações do Bot</h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Limite diário de candidaturas</span>
              <span>50</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Intervalo entre candidaturas</span>
              <span>30-60 segundos</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Modo de execução</span>
              <span>Automático</span>
            </div>
            <a href="/settings" className="text-primary hover:underline block mt-4">
              Alterar configurações →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
