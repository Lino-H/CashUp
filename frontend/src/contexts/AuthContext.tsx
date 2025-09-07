import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

interface User {
  id: number
  username: string
  email: string
  full_name?: string
  bio?: string
  avatar_url?: string
  timezone: string
  language: string
  is_email_verified: boolean
  roles: string[]
  created_at: string
}

interface AuthContextType {
  isAuthenticated: boolean
  user: User | null
  loading: boolean
  login: (userData: User, sessionId: string) => void
  logout: () => void
  refreshAuth: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  // 初始化认证状态
  useEffect(() => {
    refreshAuth()
  }, [])

  const refreshAuth = () => {
    const token = localStorage.getItem('access_token')
    const userInfoStr = localStorage.getItem('user_info')
    
    if (token && userInfoStr) {
      try {
        const parsedUserInfo = JSON.parse(userInfoStr)
        setUser(parsedUserInfo)
        setIsAuthenticated(true)
      } catch (error) {
        console.error('解析用户信息失败:', error)
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_info')
        setUser(null)
        setIsAuthenticated(false)
      }
    } else {
      setUser(null)
      setIsAuthenticated(false)
    }
    setLoading(false)
  }

  const login = (userData: User, sessionId: string) => {
    setIsAuthenticated(true)
    setUser(userData)
    localStorage.setItem('access_token', sessionId)
    localStorage.setItem('user_info', JSON.stringify(userData))
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
    setIsAuthenticated(false)
    setUser(null)
    navigate('/login')
  }

  const value: AuthContextType = {
    isAuthenticated,
    user,
    loading,
    login,
    logout,
    refreshAuth
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}