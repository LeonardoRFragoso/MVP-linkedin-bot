'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslation } from '@/lib/app-context';
import { useAuth } from '@/lib/auth-context';
import { ThemeToggle, LanguageToggle } from '@/components/ui/toggle-group';

export function Sidebar() {
  const pathname = usePathname();
  const { t } = useTranslation();
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <aside className="w-64 border-r bg-card p-4 flex flex-col">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-primary">{t.header.title}</h1>
        <p className="text-sm text-muted-foreground">{t.header.subtitle}</p>
      </div>
      <nav className="space-y-2 flex-1">
        <NavLink href="/dashboard" icon="📊" active={pathname === '/dashboard'}>
          {t.nav.dashboard}
        </NavLink>
        <NavLink href="/bot" icon="🤖" active={pathname === '/bot'}>
          Bot
        </NavLink>
        <NavLink href="/my-applications" icon="📝" active={pathname === '/my-applications'}>
          Minhas Candidaturas
        </NavLink>
        <NavLink href="/my-questions" icon="❓" active={pathname === '/my-questions'}>
          Minhas Respostas
        </NavLink>
        <NavLink href="/settings" icon="⚙️" active={pathname === '/settings'}>
          {t.nav.settings}
        </NavLink>
      </nav>
      
      {/* User info and logout */}
      <div className="border-t pt-4 mt-4">
        {isAuthenticated && user ? (
          <>
            <Link
              href="/profile"
              className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-accent transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-medium">
                {(user.first_name?.[0] || user.email?.[0] || 'U').toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">
                  {user.full_name || user.email?.split('@')[0] || 'Usuário'}
                </div>
                <div className="text-xs text-muted-foreground truncate">{user.email}</div>
              </div>
            </Link>
            <button
              onClick={logout}
              className="w-full mt-2 flex items-center gap-3 px-3 py-2 rounded-lg text-destructive hover:bg-destructive/10 transition-colors text-sm"
            >
              <span>🚪</span>
              <span>Sair</span>
            </button>
          </>
        ) : (
          <Link
            href="/login"
            className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-accent transition-colors text-sm"
          >
            <span>🔑</span>
            <span>Entrar</span>
          </Link>
        )}
      </div>
      
      <div className="border-t pt-4 mt-4 flex gap-2">
        <ThemeToggle />
        <LanguageToggle />
      </div>
    </aside>
  );
}

function NavLink({
  href,
  icon,
  active,
  children,
}: {
  href: string;
  icon: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all hover:bg-accent hover:text-accent-foreground ${
        active ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
      }`}
    >
      <span>{icon}</span>
      <span>{children}</span>
    </Link>
  );
}
