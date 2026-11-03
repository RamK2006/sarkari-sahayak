import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { I18nProvider } from '@/lib/i18n';
import { SessionProvider } from '@/lib/session';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter', display: 'swap' });

export const metadata: Metadata = {
  title: 'Government Scheme Assistant',
  description: 'Find government schemes you may be eligible for, in your language.',
};

export const viewport: Viewport = { width: 'device-width', initialScale: 1, themeColor: '#1b4b8f' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        <I18nProvider>
          <SessionProvider>
            <div className="shell flex min-h-[100dvh] flex-col">
              <Header />
              <div className="flex min-h-0 flex-1 flex-col">{children}</div>
              <Footer />
            </div>
          </SessionProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
