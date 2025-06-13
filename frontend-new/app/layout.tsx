import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { AuthProvider } from "@/contexts/auth-context"
import { StagewiseToolbar } from "@stagewise/toolbar-next"
import { ReactPlugin } from "@stagewise-plugins/react"
import { Toaster } from "@/components/ui/toaster"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "RSSia - Your RSS Reader",
  description: "A modern RSS feed reader.",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem={false}
          disableTransitionOnChange={false}
          storageKey="rssreader-theme"
        >
          <AuthProvider>
            {children}
            <Toaster />
            <StagewiseToolbar 
              config={{
                plugins: [ReactPlugin]
              }}
            />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
