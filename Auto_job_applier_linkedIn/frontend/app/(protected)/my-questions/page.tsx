'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';

const QUESTION_CATEGORIES = {
  basic: {
    label: 'Informações Básicas',
    questions: [
      { id: 'years_experience', label: 'Anos de experiência' },
      { id: 'salary_expectation', label: 'Pretensão salarial' },
      { id: 'available_start', label: 'Disponibilidade para início' },
      { id: 'work_model', label: 'Modelo de trabalho preferido' },
    ]
  },
  skills: {
    label: 'Habilidades',
    questions: [
      { id: 'main_skills', label: 'Principais habilidades técnicas' },
      { id: 'english_level', label: 'Nível de inglês' },
      { id: 'other_languages', label: 'Outros idiomas' },
    ]
  },
  personal: {
    label: 'Preferências Pessoais',
    questions: [
      { id: 'willing_relocate', label: 'Disponibilidade para mudança' },
      { id: 'why_interested', label: 'Motivação para novas oportunidades' },
      { id: 'notice_period', label: 'Período de aviso prévio' },
    ]
  }
};

export default function MyQuestionsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [newQuestion, setNewQuestion] = useState({ id: '', answer: '' });

  const { data: answers = {}, isLoading } = useQuery({
    queryKey: ['myAnswers'],
    queryFn: () => api.getMe().then(u => u.question_answers || {}),
  });

  const saveMutation = useMutation({
    mutationFn: (newAnswers: Record<string, string>) => api.saveUserAnswers(newAnswers),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myAnswers'] });
      setEditingId(null);
    },
  });

  const handleSave = (questionId: string) => {
    saveMutation.mutate({ ...answers, [questionId]: editValue });
  };

  const handleAddCustom = () => {
    if (newQuestion.id && newQuestion.answer) {
      saveMutation.mutate({ 
        ...answers, 
        [newQuestion.id.toLowerCase().replace(/\s+/g, '_')]: newQuestion.answer 
      });
      setNewQuestion({ id: '', answer: '' });
    }
  };

  const startEdit = (questionId: string, currentValue: string) => {
    setEditingId(questionId);
    setEditValue(currentValue || '');
  };

  if (isLoading) {
    return <div className="p-8">Carregando...</div>;
  }

  const answeredCount = Object.keys(answers).filter(k => k !== 'updated_at' && answers[k] && typeof answers[k] !== 'object').length;

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-2">Minhas Respostas</h1>
      <p className="text-muted-foreground mb-8">
        Respostas automáticas usadas pelo bot nas candidaturas
      </p>

      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-8">
        <p className="text-sm">
          💡 <strong>Dica:</strong> Quanto mais respostas você preencher, mais candidaturas o bot conseguirá completar automaticamente!
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Respostas Preenchidas</div>
          <div className="text-2xl font-bold text-primary">{answeredCount}</div>
        </div>
        <div className="bg-card rounded-lg border p-4">
          <div className="text-sm text-muted-foreground">Última Atualização</div>
          <div className="text-lg font-medium">
            {answers.updated_at 
              ? new Date(answers.updated_at).toLocaleDateString('pt-BR')
              : '-'
            }
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {Object.entries(QUESTION_CATEGORIES).map(([categoryId, category]) => (
          <div key={categoryId} className="bg-card rounded-lg border p-6">
            <h2 className="text-lg font-semibold mb-4">{category.label}</h2>
            <div className="space-y-4">
              {category.questions.map((q) => (
                <div key={q.id} className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <label className="block text-sm font-medium mb-1">{q.label}</label>
                    {editingId === q.id ? (
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          className="flex-1 px-3 py-2 border rounded-lg bg-background"
                          autoFocus
                        />
                        <button
                          onClick={() => handleSave(q.id)}
                          disabled={saveMutation.isPending}
                          className="px-3 py-2 bg-primary text-primary-foreground rounded-lg"
                        >
                          Salvar
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          className="px-3 py-2 border rounded-lg"
                        >
                          Cancelar
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <span className={answers[q.id] ? '' : 'text-muted-foreground italic'}>
                          {typeof answers[q.id] === 'object' 
                            ? JSON.stringify(answers[q.id]) 
                            : (answers[q.id] || 'Não preenchido')}
                        </span>
                        <button
                          onClick={() => startEdit(q.id, answers[q.id])}
                          className="text-primary hover:underline text-sm"
                        >
                          {answers[q.id] ? 'Editar' : 'Preencher'}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* Custom Answers */}
        <div className="bg-card rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-4">Respostas Personalizadas</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Adicione respostas para perguntas específicas que você encontra frequentemente.
          </p>
          
          {/* Show existing custom answers */}
          <div className="space-y-3 mb-4">
            {Object.entries(answers)
              .filter(([key, value]) => {
                const predefinedIds = Object.values(QUESTION_CATEGORIES)
                  .flatMap(c => c.questions.map(q => q.id));
                return !predefinedIds.includes(key) && key !== 'updated_at' && typeof value !== 'object';
              })
              .map(([key, value]) => (
                <div key={key} className="flex items-center justify-between bg-muted/30 p-3 rounded-lg">
                  {editingId === key ? (
                    <div className="flex-1 flex gap-2">
                      <span className="font-medium py-2">{key.replace(/_/g, ' ')} →</span>
                      <input
                        type="text"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="flex-1 px-3 py-2 border rounded-lg bg-background"
                        autoFocus
                      />
                      <button
                        onClick={() => handleSave(key)}
                        disabled={saveMutation.isPending}
                        className="px-3 py-2 bg-primary text-primary-foreground rounded-lg text-sm"
                      >
                        Salvar
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        className="px-3 py-2 border rounded-lg text-sm"
                      >
                        Cancelar
                      </button>
                    </div>
                  ) : (
                    <>
                      <div>
                        <span className="font-medium">{key.replace(/_/g, ' ')}</span>
                        <span className="text-muted-foreground mx-2">→</span>
                        <span>{String(value)}</span>
                      </div>
                      <button
                        onClick={() => startEdit(key, String(value))}
                        className="text-primary hover:underline text-sm"
                      >
                        Editar
                      </button>
                    </>
                  )}
                </div>
              ))}
          </div>

          {/* Add new custom answer */}
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Nome da pergunta"
              value={newQuestion.id}
              onChange={(e) => setNewQuestion({ ...newQuestion, id: e.target.value })}
              className="flex-1 px-3 py-2 border rounded-lg bg-background"
            />
            <input
              type="text"
              placeholder="Sua resposta"
              value={newQuestion.answer}
              onChange={(e) => setNewQuestion({ ...newQuestion, answer: e.target.value })}
              className="flex-1 px-3 py-2 border rounded-lg bg-background"
            />
            <button
              onClick={handleAddCustom}
              disabled={!newQuestion.id || !newQuestion.answer}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50"
            >
              Adicionar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
