import { apiFetch } from './api'

export const authQueryKey = ['auth', 'me'] as const

export interface UserInfo {
  username: string
}

export async function fetchMe(): Promise<UserInfo> {
  const res = await apiFetch('/api/auth/me')
  return res.json()
}

export async function login(username: string, password: string): Promise<UserInfo> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText))
  return res.json()
}

export async function logout(): Promise<void> {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
}
