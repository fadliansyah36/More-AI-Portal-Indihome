import type { Metadata, Viewport } from 'next';
import { Providers } from '@/components/providers';
import './globals.css';

export const viewport: Viewport = {
  themeColor: '#e11d48',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export const metadata: Metadata = {
  title: 'MoreAI - Global Partner ISP/Network Platform',
  description: 'Satu Aplikasi untuk Semua Kebutuhan AI Anda. Akses cepat, produktif, dan terintegrasi dalam satu platform dengan ekosistem Global Partner ISP & Network.',
  manifest: '/manifest.webmanifest',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'MoreAI',
  },
  icons: {
    icon: '/icon.svg',
    apple: '/apple-touch-icon.png',
  },
  openGraph: {
    title: 'MoreAI - Global Partner ISP & Network Workspace',
    description: 'Satu Aplikasi untuk Semua Kebutuhan AI Anda. Akses internet cepat dan teknologi AI untuk mendukung produktivitas, belajar, bekerja, dan berkreasi bersama Global Partner ISP/Network.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'MoreAI - Global Partner ISP & Network Platform',
    description: 'Satu Aplikasi untuk Semua Kebutuhan AI Anda dengan ekosistem Global Partner ISP & Network.',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <head>
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
      </head>
      <body className="min-h-screen antialiased font-sans bg-slate-50 text-slate-900 selection:bg-rose-500 selection:text-white" suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
