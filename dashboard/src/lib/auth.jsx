import { createContext, useContext, useState, useCallback } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('xpose_token'))
  const [user, setUser] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const login = useCallback((accessToken, refreshToken) => {
    localStorage.setItem('xpose_token', accessToken)
    localStorage.setItem('xpose_refresh', refreshToken)
    setToken(accessToken)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('xpose_token')
    localStorage.removeItem('xpose_refresh')
    setToken(null)
    setUser(null)
  }, [])

  const triggerRefresh = useCallback(() => {
    setRefreshKey(k => k + 1)
  }, [])

  return (
    <AuthContext.Provider value={{ token, user, setUser, login, logout, refreshKey, triggerRefresh }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
