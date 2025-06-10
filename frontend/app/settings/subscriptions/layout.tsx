"use client"

import type React from "react"
import { useEffect } from "react"
import { useRouter } from "next/navigation"
import YoutubeHeader from "@/components/youtube-header"
import { useAuth } from "@/hooks/use-auth"

export default function SettingsSubscriptionsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isLoggedIn, login, logout } = useAuth()
  const router = useRouter()

  const handleLogout = () => {
    console.log("Settings page logout triggered")
    logout()
    router.push("/")
  }

  useEffect(() => {
    if (!isLoggedIn) {
      router.push("/")
    }
  }, [isLoggedIn, router])

  if (!isLoggedIn) {
    return null
  }

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <YoutubeHeader isLoggedIn={isLoggedIn} onLogin={login} onLogout={handleLogout} showFilterTags={false} />
      <main className="flex-grow container mx-auto px-4 py-8">{children}</main>
    </div>
  )
}
