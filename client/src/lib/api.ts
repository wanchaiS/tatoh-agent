export class AuthError extends Error {
  constructor() {
    super('Unauthorized')
    this.name = 'AuthError'
  }
}

export async function apiFetch(url: string, options?: RequestInit): Promise<Response> {
  const res = await fetch(url, { credentials: 'include', ...options })

  if (res.status === 401) {
    const refresh = await fetch('/api/auth/refresh-token', {
      method: 'POST',
      credentials: 'include',
    })
    if (!refresh.ok) throw new AuthError()

    // retry after refreshed 
    const retryAfterRefresh = await fetch(url, { credentials: 'include', ...options })
    if (retryAfterRefresh.status === 401) throw new AuthError()
    if (!retryAfterRefresh.ok) throw new Error(await retryAfterRefresh.text().catch(() => retryAfterRefresh.statusText))
   
      return retryAfterRefresh
  }

  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText))
  return res
}
