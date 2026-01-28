'use client';

import { useTranslation, useTheme } from '@/lib/app-context';

export default function SettingsPage() {
  const { t, locale, setLocale } = useTranslation();
  const { theme, setTheme } = useTheme();
  
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">{t.settings.title}</h1>
      
      <div className="space-y-6">
        <div className="bg-card rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-2">{t.settings.appearance}</h2>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-muted-foreground block mb-2">{t.settings.theme}</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setTheme('light')}
                  className={`px-4 py-2 rounded-lg border transition-colors ${theme === 'light' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'}`}
                >
                  ☀️ {t.settings.lightMode}
                </button>
                <button
                  onClick={() => setTheme('dark')}
                  className={`px-4 py-2 rounded-lg border transition-colors ${theme === 'dark' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'}`}
                >
                  🌙 {t.settings.darkMode}
                </button>
              </div>
            </div>
            <div>
              <label className="text-sm text-muted-foreground block mb-2">{t.settings.language}</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setLocale('en')}
                  className={`px-4 py-2 rounded-lg border transition-colors ${locale === 'en' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'}`}
                >
                  🇺🇸 {t.settings.english}
                </button>
                <button
                  onClick={() => setLocale('pt-BR')}
                  className={`px-4 py-2 rounded-lg border transition-colors ${locale === 'pt-BR' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'}`}
                >
                  🇧🇷 {t.settings.portuguese}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-2">{t.settings.apiConfig}</h2>
          <p className="text-sm text-muted-foreground mb-4">{t.settings.apiConfigDesc}</p>
          <div className="flex items-center gap-2">
            <span className="text-sm">{t.settings.apiUrl}:</span>
            <code className="bg-muted px-2 py-1 rounded text-sm">http://localhost:8002</code>
          </div>
        </div>

        <div className="bg-card rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-2">{t.settings.botSettings}</h2>
          <p className="text-sm text-muted-foreground">{t.settings.botSettingsDesc}</p>
        </div>
      </div>
    </div>
  );
}
