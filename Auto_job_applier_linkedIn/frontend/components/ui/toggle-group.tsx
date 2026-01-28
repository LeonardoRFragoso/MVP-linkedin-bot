'use client';

import { useTheme, useTranslation } from '@/lib/app-context';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors hover:bg-accent w-full"
      title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {theme === 'dark' ? (
        <>
          <span>☀️</span>
          <span className="text-muted-foreground">Light</span>
        </>
      ) : (
        <>
          <span>🌙</span>
          <span className="text-muted-foreground">Dark</span>
        </>
      )}
    </button>
  );
}

export function LanguageToggle() {
  const { locale, setLocale } = useTranslation();

  const toggleLocale = () => {
    setLocale(locale === 'en' ? 'pt-BR' : 'en');
  };

  return (
    <button
      onClick={toggleLocale}
      className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors hover:bg-accent w-full"
      title={locale === 'en' ? 'Mudar para Português' : 'Switch to English'}
    >
      <span>🌐</span>
      <span className="text-muted-foreground">{locale === 'en' ? 'EN' : 'PT-BR'}</span>
    </button>
  );
}

export function SettingsToggles() {
  return (
    <div className="flex items-center gap-1 border-t pt-4 mt-4">
      <ThemeToggle />
      <LanguageToggle />
    </div>
  );
}
