'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { api } from '@/lib/api';

type Step = 'profile' | 'resume' | 'questions' | 'linkedin' | 'complete';

const COMMON_QUESTIONS = [
  { id: 'years_experience', question: 'Quantos anos de experiência você tem na sua área?', type: 'text' },
  { id: 'salary_expectation', question: 'Qual sua pretensão salarial?', type: 'text' },
  { id: 'available_start', question: 'Qual sua disponibilidade para início?', type: 'select', options: ['Imediato', '15 dias', '30 dias', 'A combinar'] },
  { id: 'work_model', question: 'Qual modelo de trabalho você prefere?', type: 'select', options: ['Remoto', 'Híbrido', 'Presencial', 'Qualquer'] },
  { id: 'willing_relocate', question: 'Você tem disponibilidade para mudança?', type: 'select', options: ['Sim', 'Não', 'Depende da oportunidade'] },
  { id: 'english_level', question: 'Qual seu nível de inglês?', type: 'select', options: ['Básico', 'Intermediário', 'Avançado', 'Fluente', 'Nativo'] },
  { id: 'why_interested', question: 'Por que você está interessado em novas oportunidades?', type: 'textarea' },
  { id: 'main_skills', question: 'Quais são suas principais habilidades técnicas?', type: 'textarea' },
];

export default function OnboardingPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<Step>('profile');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const [profileData, setProfileData] = useState({
    phone_number: '',
    current_city: '',
    job_title: '',
    linkedin_url: '',
  });

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  
  // Custom questions from LinkedIn
  const [customQuestions, setCustomQuestions] = useState<{ question: string; answer: string }[]>([]);
  const [newCustomQuestion, setNewCustomQuestion] = useState({ question: '', answer: '' });

  const addCustomQuestion = () => {
    if (newCustomQuestion.question && newCustomQuestion.answer) {
      setCustomQuestions([...customQuestions, newCustomQuestion]);
      // Also add to answers with a sanitized key
      const key = `custom_${newCustomQuestion.question.toLowerCase().replace(/[^a-z0-9]/g, '_').slice(0, 50)}`;
      setAnswers({ ...answers, [key]: newCustomQuestion.answer });
      setNewCustomQuestion({ question: '', answer: '' });
    }
  };

  const removeCustomQuestion = (index: number) => {
    const removed = customQuestions[index];
    const key = `custom_${removed.question.toLowerCase().replace(/[^a-z0-9]/g, '_').slice(0, 50)}`;
    const newAnswers = { ...answers };
    delete newAnswers[key];
    setAnswers(newAnswers);
    setCustomQuestions(customQuestions.filter((_, i) => i !== index));
  };

  const [linkedinCreds, setLinkedinCreds] = useState({
    email: '',
    password: '',
  });

  const steps: { key: Step; label: string; icon: string }[] = [
    { key: 'profile', label: 'Perfil', icon: '👤' },
    { key: 'resume', label: 'Currículo', icon: '📄' },
    { key: 'questions', label: 'Perguntas', icon: '❓' },
    { key: 'linkedin', label: 'LinkedIn', icon: '🔗' },
    { key: 'complete', label: 'Concluído', icon: '✅' },
  ];

  const handleProfileSubmit = async () => {
    setIsLoading(true);
    try {
      await api.updateProfile(profileData);
      setCurrentStep('resume');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao salvar perfil');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResumeUpload = async () => {
    if (!resumeFile) {
      setCurrentStep('questions');
      return;
    }
    
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', resumeFile);
      await api.uploadResume(formData);
      setCurrentStep('questions');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao enviar currículo');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuestionsSubmit = async () => {
    setIsLoading(true);
    try {
      await api.saveUserAnswers(answers);
      setCurrentStep('linkedin');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao salvar respostas');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLinkedinSubmit = async () => {
    setIsLoading(true);
    try {
      await api.saveLinkedinCredentials(linkedinCreds);
      setCurrentStep('complete');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao salvar credenciais');
    } finally {
      setIsLoading(false);
    }
  };

  const handleComplete = () => {
    router.push('/bot');
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Configuração Inicial</h1>
        <p className="text-muted-foreground mb-8">
          Complete seu perfil para começar a usar o bot de candidaturas
        </p>

        {/* Progress Steps */}
        <div className="flex items-center justify-between mb-8">
          {steps.map((step, index) => (
            <div key={step.key} className="flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${
                  steps.findIndex(s => s.key === currentStep) >= index
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                {step.icon}
              </div>
              {index < steps.length - 1 && (
                <div className={`w-12 h-1 mx-2 ${
                  steps.findIndex(s => s.key === currentStep) > index
                    ? 'bg-primary'
                    : 'bg-muted'
                }`} />
              )}
            </div>
          ))}
        </div>

        {error && (
          <div className="bg-destructive/10 text-destructive p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {/* Step Content */}
        <div className="bg-card rounded-lg border p-6">
          {currentStep === 'profile' && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Informações do Perfil</h2>
              <div>
                <label className="block text-sm font-medium mb-2">Cargo/Função Desejada *</label>
                <input
                  type="text"
                  value={profileData.job_title}
                  onChange={(e) => setProfileData({ ...profileData, job_title: e.target.value })}
                  placeholder="Ex: Desenvolvedor Full Stack, Analista de Dados..."
                  className="w-full px-3 py-2 border rounded-lg bg-background"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Telefone</label>
                <input
                  type="tel"
                  value={profileData.phone_number}
                  onChange={(e) => setProfileData({ ...profileData, phone_number: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg bg-background"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Cidade</label>
                <input
                  type="text"
                  value={profileData.current_city}
                  onChange={(e) => setProfileData({ ...profileData, current_city: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg bg-background"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">URL do LinkedIn</label>
                <input
                  type="url"
                  value={profileData.linkedin_url}
                  onChange={(e) => setProfileData({ ...profileData, linkedin_url: e.target.value })}
                  placeholder="https://linkedin.com/in/seu-perfil"
                  className="w-full px-3 py-2 border rounded-lg bg-background"
                />
              </div>
              <button
                onClick={handleProfileSubmit}
                disabled={isLoading || !profileData.job_title}
                className="w-full py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50"
              >
                {isLoading ? 'Salvando...' : 'Continuar'}
              </button>
            </div>
          )}

          {currentStep === 'resume' && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Upload do Currículo</h2>
              <p className="text-sm text-muted-foreground">
                Envie seu currículo em PDF para que o bot possa anexá-lo às candidaturas.
              </p>
              <div className="border-2 border-dashed rounded-lg p-8 text-center">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="resume-upload"
                />
                <label htmlFor="resume-upload" className="cursor-pointer">
                  <div className="text-4xl mb-2">📄</div>
                  {resumeFile ? (
                    <p className="text-primary font-medium">{resumeFile.name}</p>
                  ) : (
                    <p className="text-muted-foreground">
                      Clique para selecionar ou arraste o arquivo PDF
                    </p>
                  )}
                </label>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentStep('profile')}
                  className="px-4 py-2 border rounded-lg"
                >
                  Voltar
                </button>
                <button
                  onClick={handleResumeUpload}
                  disabled={isLoading}
                  className="flex-1 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50"
                >
                  {isLoading ? 'Enviando...' : resumeFile ? 'Enviar e Continuar' : 'Pular'}
                </button>
              </div>
            </div>
          )}

          {currentStep === 'questions' && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Banco de Respostas</h2>
              
              {/* Instrução Principal */}
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <p className="text-sm">
                  📝 <strong>Insira aqui as perguntas mais frequentes que os recrutadores fazem no LinkedIn para podermos reutilizar suas respostas.</strong>
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  Copie as perguntas diretamente dos formulários do LinkedIn e adicione sua resposta padrão. 
                  O bot usará essas respostas automaticamente durante as candidaturas. Você pode editar as respostas a qualquer momento.
                </p>
              </div>

              {/* Perguntas Comuns Pré-definidas */}
              <div className="border-b pb-4">
                <h3 className="text-sm font-medium text-muted-foreground mb-3">Perguntas mais comuns:</h3>
                <div className="space-y-4 max-h-64 overflow-y-auto">
                  {COMMON_QUESTIONS.map((q) => (
                    <div key={q.id}>
                      <label className="block text-sm font-medium mb-2">{q.question}</label>
                      {q.type === 'select' ? (
                        <select
                          value={answers[q.id] || ''}
                          onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                          className="w-full px-3 py-2 border rounded-lg bg-background"
                        >
                          <option value="">Selecione...</option>
                          {q.options?.map((opt) => (
                            <option key={opt} value={opt}>{opt}</option>
                          ))}
                        </select>
                      ) : q.type === 'textarea' ? (
                        <textarea
                          value={answers[q.id] || ''}
                          onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                          rows={2}
                          className="w-full px-3 py-2 border rounded-lg bg-background"
                          placeholder="Digite sua resposta padrão..."
                        />
                      ) : (
                        <input
                          type="text"
                          value={answers[q.id] || ''}
                          onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                          className="w-full px-3 py-2 border rounded-lg bg-background"
                          placeholder="Digite sua resposta padrão..."
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Adicionar Perguntas Personalizadas */}
              <div>
                <h3 className="text-sm font-medium mb-3">➕ Adicionar pergunta personalizada do LinkedIn:</h3>
                <div className="space-y-3">
                  {customQuestions.map((cq, index) => (
                    <div key={index} className="bg-muted/30 p-3 rounded-lg">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-sm font-medium">{cq.question}</span>
                        <button
                          onClick={() => removeCustomQuestion(index)}
                          className="text-destructive hover:underline text-xs"
                        >
                          Remover
                        </button>
                      </div>
                      <p className="text-sm text-muted-foreground">{cq.answer}</p>
                    </div>
                  ))}
                  
                  <div className="border-2 border-dashed rounded-lg p-4 space-y-3">
                    <input
                      type="text"
                      value={newCustomQuestion.question}
                      onChange={(e) => setNewCustomQuestion({ ...newCustomQuestion, question: e.target.value })}
                      placeholder="Cole aqui a pergunta do recrutador do LinkedIn..."
                      className="w-full px-3 py-2 border rounded-lg bg-background text-sm"
                    />
                    <textarea
                      value={newCustomQuestion.answer}
                      onChange={(e) => setNewCustomQuestion({ ...newCustomQuestion, answer: e.target.value })}
                      placeholder="Digite sua resposta padrão para esta pergunta..."
                      rows={2}
                      className="w-full px-3 py-2 border rounded-lg bg-background text-sm"
                    />
                    <button
                      onClick={addCustomQuestion}
                      disabled={!newCustomQuestion.question || !newCustomQuestion.answer}
                      className="w-full py-2 border border-primary text-primary rounded-lg text-sm hover:bg-primary/10 disabled:opacity-50"
                    >
                      + Adicionar Pergunta e Resposta
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 pt-4">
                <button
                  onClick={() => setCurrentStep('resume')}
                  className="px-4 py-2 border rounded-lg"
                >
                  Voltar
                </button>
                <button
                  onClick={handleQuestionsSubmit}
                  disabled={isLoading}
                  className="flex-1 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50"
                >
                  {isLoading ? 'Salvando...' : 'Continuar'}
                </button>
              </div>
            </div>
          )}

          {currentStep === 'linkedin' && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Credenciais do LinkedIn</h2>
              <p className="text-sm text-muted-foreground">
                Suas credenciais são criptografadas e usadas apenas para automação das candidaturas.
              </p>
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  🔒 Suas credenciais são armazenadas de forma segura com criptografia AES-256.
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Email do LinkedIn</label>
                <input
                  type="email"
                  value={linkedinCreds.email}
                  onChange={(e) => setLinkedinCreds({ ...linkedinCreds, email: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg bg-background"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Senha do LinkedIn</label>
                <input
                  type="password"
                  value={linkedinCreds.password}
                  onChange={(e) => setLinkedinCreds({ ...linkedinCreds, password: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg bg-background"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentStep('questions')}
                  className="px-4 py-2 border rounded-lg"
                >
                  Voltar
                </button>
                <button
                  onClick={handleLinkedinSubmit}
                  disabled={isLoading || !linkedinCreds.email || !linkedinCreds.password}
                  className="flex-1 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50"
                >
                  {isLoading ? 'Salvando...' : 'Continuar'}
                </button>
              </div>
            </div>
          )}

          {currentStep === 'complete' && (
            <div className="text-center py-8">
              <div className="text-6xl mb-4">🎉</div>
              <h2 className="text-2xl font-bold mb-2">Configuração Concluída!</h2>
              <p className="text-muted-foreground mb-6">
                Seu perfil está pronto. Agora você pode iniciar o bot e acompanhar as candidaturas em tempo real.
              </p>
              <button
                onClick={handleComplete}
                className="px-8 py-3 bg-primary text-primary-foreground rounded-lg font-medium"
              >
                Ir para o Painel do Bot
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
