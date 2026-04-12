import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  user: { username: string } | null
  setUser: (user: { username: string }) => void
  clearUser: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      setUser: (user) => set({ user }),
      clearUser: () => set({ user: null }),
    }),
    { name: 'tatoh' },
  ),
)
