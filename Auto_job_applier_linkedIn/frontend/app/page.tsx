import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <nav className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🤖</span>
            <span className="text-xl font-bold text-primary">LinkedIn Bot</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm hover:text-primary transition-colors">
              Entrar
            </Link>
            <Link
              href="/register"
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              Começar Grátis
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <h1 className="text-4xl md:text-6xl font-bold mb-6">
          Automatize suas candidaturas no
          <span className="text-primary"> LinkedIn</span>
        </h1>
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
          Encontre vagas, preencha formulários e envie candidaturas automaticamente.
          Economize horas do seu tempo e aumente suas chances de conseguir o emprego dos sonhos.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/register"
            className="px-8 py-4 bg-primary text-primary-foreground rounded-lg text-lg font-medium hover:bg-primary/90 transition-colors"
          >
            Começar Agora - É Grátis
          </Link>
          <Link
            href="#features"
            className="px-8 py-4 border rounded-lg text-lg font-medium hover:bg-accent transition-colors"
          >
            Saiba Mais
          </Link>
        </div>
      </section>

      {/* Stats */}
      <section className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
          <div className="p-6">
            <div className="text-4xl font-bold text-primary mb-2">500+</div>
            <div className="text-muted-foreground">Candidaturas por dia</div>
          </div>
          <div className="p-6">
            <div className="text-4xl font-bold text-primary mb-2">10x</div>
            <div className="text-muted-foreground">Mais rápido que manual</div>
          </div>
          <div className="p-6">
            <div className="text-4xl font-bold text-primary mb-2">24/7</div>
            <div className="text-muted-foreground">Automação contínua</div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="container mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center mb-12">Como Funciona</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-card rounded-xl border p-8 text-center">
            <div className="text-4xl mb-4">📝</div>
            <h3 className="text-xl font-semibold mb-3">1. Configure seu Perfil</h3>
            <p className="text-muted-foreground">
              Preencha suas informações, faça upload do currículo e responda perguntas frequentes uma única vez.
            </p>
          </div>
          <div className="bg-card rounded-xl border p-8 text-center">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold mb-3">2. Defina sua Busca</h3>
            <p className="text-muted-foreground">
              Escolha cargos, localização, tipo de trabalho (remoto, híbrido) e outras preferências.
            </p>
          </div>
          <div className="bg-card rounded-xl border p-8 text-center">
            <div className="text-4xl mb-4">🚀</div>
            <h3 className="text-xl font-semibold mb-3">3. Deixe o Bot Trabalhar</h3>
            <p className="text-muted-foreground">
              O bot busca vagas, preenche formulários e envia candidaturas automaticamente enquanto você descansa.
            </p>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="bg-muted/50 py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Por que usar o LinkedIn Bot?</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="flex gap-4">
              <span className="text-2xl">⏰</span>
              <div>
                <h3 className="font-semibold mb-2">Economize Tempo</h3>
                <p className="text-muted-foreground text-sm">
                  Não perca mais horas preenchendo os mesmos formulários. O bot faz isso em segundos.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <span className="text-2xl">🎯</span>
              <div>
                <h3 className="font-semibold mb-2">Candidaturas Direcionadas</h3>
                <p className="text-muted-foreground text-sm">
                  Filtros inteligentes garantem que você se candidate apenas a vagas relevantes.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <span className="text-2xl">📊</span>
              <div>
                <h3 className="font-semibold mb-2">Acompanhe em Tempo Real</h3>
                <p className="text-muted-foreground text-sm">
                  Dashboard completo com status das candidaturas, logs e estatísticas.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <span className="text-2xl">🔒</span>
              <div>
                <h3 className="font-semibold mb-2">Seguro e Privado</h3>
                <p className="text-muted-foreground text-sm">
                  Suas credenciais são criptografadas e seus dados nunca são compartilhados.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="container mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center mb-4">Planos</h2>
        <p className="text-muted-foreground text-center mb-12">Comece grátis, faça upgrade quando precisar</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="bg-card rounded-xl border p-8">
            <h3 className="text-xl font-semibold mb-2">Grátis</h3>
            <div className="text-3xl font-bold mb-4">R$ 0<span className="text-sm font-normal text-muted-foreground">/mês</span></div>
            <ul className="space-y-3 text-sm mb-8">
              <li className="flex items-center gap-2">✅ 10 candidaturas/dia</li>
              <li className="flex items-center gap-2">✅ Dashboard básico</li>
              <li className="flex items-center gap-2">✅ 1 perfil de busca</li>
              <li className="flex items-center gap-2 text-muted-foreground">❌ Suporte prioritário</li>
            </ul>
            <Link href="/register" className="block text-center py-3 border rounded-lg hover:bg-accent transition-colors">
              Começar Grátis
            </Link>
          </div>
          <div className="bg-card rounded-xl border-2 border-primary p-8 relative">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground px-3 py-1 rounded-full text-xs font-medium">
              Popular
            </div>
            <h3 className="text-xl font-semibold mb-2">Pro</h3>
            <div className="text-3xl font-bold mb-4">R$ 49<span className="text-sm font-normal text-muted-foreground">/mês</span></div>
            <ul className="space-y-3 text-sm mb-8">
              <li className="flex items-center gap-2">✅ 100 candidaturas/dia</li>
              <li className="flex items-center gap-2">✅ Dashboard completo</li>
              <li className="flex items-center gap-2">✅ 5 perfis de busca</li>
              <li className="flex items-center gap-2">✅ Suporte por email</li>
            </ul>
            <Link href="/register" className="block text-center py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
              Assinar Pro
            </Link>
          </div>
          <div className="bg-card rounded-xl border p-8">
            <h3 className="text-xl font-semibold mb-2">Enterprise</h3>
            <div className="text-3xl font-bold mb-4">R$ 199<span className="text-sm font-normal text-muted-foreground">/mês</span></div>
            <ul className="space-y-3 text-sm mb-8">
              <li className="flex items-center gap-2">✅ Candidaturas ilimitadas</li>
              <li className="flex items-center gap-2">✅ API dedicada</li>
              <li className="flex items-center gap-2">✅ Perfis ilimitados</li>
              <li className="flex items-center gap-2">✅ Suporte 24/7</li>
            </ul>
            <Link href="/register" className="block text-center py-3 border rounded-lg hover:bg-accent transition-colors">
              Falar com Vendas
            </Link>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-primary text-primary-foreground py-20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Pronto para automatizar sua busca por emprego?</h2>
          <p className="text-lg opacity-90 mb-8">Junte-se a milhares de profissionais que já economizam tempo com o LinkedIn Bot</p>
          <Link
            href="/register"
            className="inline-block px-8 py-4 bg-white text-primary rounded-lg text-lg font-medium hover:bg-gray-100 transition-colors"
          >
            Criar Conta Grátis
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xl">🤖</span>
              <span className="font-semibold">LinkedIn Bot</span>
            </div>
            <div className="flex gap-6 text-sm text-muted-foreground">
              <Link href="#" className="hover:text-foreground">Termos de Uso</Link>
              <Link href="#" className="hover:text-foreground">Privacidade</Link>
              <Link href="#" className="hover:text-foreground">Contato</Link>
            </div>
            <div className="text-sm text-muted-foreground">
              © 2026 LinkedIn Bot. Todos os direitos reservados.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
