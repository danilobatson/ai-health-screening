import { ColorSchemeScript } from '@mantine/core';
import Providers from '@/components/Providers';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';

export const metadata = {
  title: 'AI Health Assessment System',
  description: 'Professional healthcare dashboard with AI-powered risk assessment',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <ColorSchemeScript />
      </head>
      <body suppressHydrationWarning>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
