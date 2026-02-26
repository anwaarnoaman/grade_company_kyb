"use client"

import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react"
import { useRouter } from "next/navigation"

interface AuthContextType {
  token: string | null
  setToken: (token: string | null) => void
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const stored = sessionStorage.getItem("access_token")
    if (stored) {
      setTokenState(stored)
    }
    setMounted(true)
  }, [])

  const setToken = (newToken: string | null) => {
    setTokenState(newToken)
    if (newToken) {
      sessionStorage.setItem("access_token", newToken)
    } else {
      sessionStorage.removeItem("access_token")
    }
  }

  const logout = () => {
    setToken(null)
    router.push("/login")
  }

  if (!mounted) {
    return null
  }

  return (
    <AuthContext.Provider
      value={{ token, setToken, logout, isAuthenticated: !!token }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
