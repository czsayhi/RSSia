"use client"

import { useState, useEffect } from "react"
import { authStore } from "@/lib/auth-store"

export function useAuth() {
  const [isLoggedIn, setIsLoggedIn] = useState(authStore.getIsLoggedIn())

  useEffect(() => {
    const unsubscribe = authStore.subscribe(setIsLoggedIn)
    return unsubscribe
  }, [])

  const login = () => {
    authStore.login()
  }

  const logout = () => {
    authStore.logout()
  }

  return { isLoggedIn, login, logout }
}
