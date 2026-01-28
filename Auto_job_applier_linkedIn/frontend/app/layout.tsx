import './globals.css';
import { Providers } from './providers';

export const metadata = {
  title: 'LinkedIn Bot - Automatize suas candidaturas',
  description: 'Automatize suas candidaturas no LinkedIn e economize tempo na busca por emprego',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased" suppressHydrationWarning>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
