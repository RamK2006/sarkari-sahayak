import type { Metadata, Viewport } from 'next';
import { Fraunces, Inter } from 'next/font/google';
import './globals.css';
import { I18nProvider } from '@/lib/i18n';
import { SessionProvider } from '@/lib/session';
import { VaultProvider } from '@/lib/vault';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter', display: 'swap' });
const fraunces = Fraunces({ subsets: ['latin'], variable: '--font-display', display: 'swap' });

export const metadata: Metadata = {
  title: 'Government Scheme Assistant',
  description: 'Find government schemes you may be eligible for, in your language.',
};

export const viewport: Viewport = { width: 'device-width', initialScale: 1 };

// Applies the saved (or system) theme before first paint to avoid a flash.
const themeScript = `try{var t=localStorage.getItem('sa.theme');if(!t){t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}document.documentElement.dataset.theme=t}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${fraunces.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <I18nProvider>
          <VaultProvider>
            <SessionProvider>
              <div className="shell flex min-h-[100dvh] flex-col">
                <Header />
                <div className="flex min-h-0 flex-1 flex-col">{children}</div>
                <Footer />
              </div>
            </SessionProvider>
          </VaultProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
