import { useAuthStore } from '../stores/authStore'

export class AuthError extends Error {
  constructor() {
    super('Unauthorized')
    this.name = 'AuthError'
  }
}

let refreshInFlight: Promise<Response> | null = null

function refreshOnce(): Promise<Response> {
  if (!refreshInFlight) {
    refreshInFlight = fetch('/api/auth/refresh-token', {
      method: 'POST',
      credentials: 'include',
    }).finally(() => { refreshInFlight = null })
  }
  return refreshInFlight
}

export async function apiFetch(url: string, options?: RequestInit): Promise<Response> {
  const res = await fetch(url, { credentials: 'include', ...options })

  if (res.status === 401) {
    const refresh = await refreshOnce()
    if (!refresh.ok) {
      useAuthStore.getState().clearUser()
      throw new AuthError()
    }

    const retryAfterRefresh = await fetch(url, { credentials: 'include', ...options })
    if (retryAfterRefresh.status === 401) {
      useAuthStore.getState().clearUser()
      throw new AuthError()
    }
    if (!retryAfterRefresh.ok) throw new Error(await retryAfterRefresh.text().catch(() => retryAfterRefresh.statusText))

    return retryAfterRefresh
  }

  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText))
  return res
}
