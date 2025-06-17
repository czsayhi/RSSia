"use client"

import { useState } from "react"
import YoutubeHeader from "@/components/youtube-header"
import VideoGrid from "@/components/video-grid"
import LoginDialog from "@/components/login-dialog"
import { useAuth } from "@/contexts/auth-context"

function LoggedOutView() {
  return (
    <div className="flex-grow flex items-center justify-center text-center p-4">
      <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tighter text-foreground/80">
        Hey，我是RSSia
      </h1>
    </div>
  )
}

export default function HomePage() {
  const { isAuthenticated, logout } = useAuth()
  const [loginDialogOpen, setLoginDialogOpen] = useState(false)
  const [contentRefreshTrigger, setContentRefreshTrigger] = useState(0)

  const handleLogin = () => {
    setLoginDialogOpen(true)
  }

  const handleContentRefresh = () => {
    console.log('HomePage: 触发内容刷新')
    setContentRefreshTrigger(prev => prev + 1)
  }

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <YoutubeHeader 
        isLoggedIn={isAuthenticated} 
        onLogin={handleLogin} 
        onLogout={logout} 
        onContentRefresh={handleContentRefresh}
      />
      {isAuthenticated ? (
        <main className="flex-grow p-4 md:px-6 lg:px-8 pt-6">
          <VideoGrid refreshTrigger={contentRefreshTrigger} />
        </main>
      ) : (
        <LoggedOutView />
      )}
      
      <LoginDialog
        open={loginDialogOpen}
        onOpenChange={setLoginDialogOpen}
      />
    </div>
  )
}
