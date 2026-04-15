import { apiFetch } from '@/lib/api'
import { useQuery } from '@tanstack/react-query'

export interface Conversations {
  thread_id: string
  title: string | null
  created_at: string
}

interface ConversationsResponse {
  threads: Conversations[]
  total: number
  page: number
  limit: number
}

async function fetchConversations(page: number, limit: number): Promise<ConversationsResponse> {
  const res = await apiFetch(`/api/conversations?page=${page}&limit=${limit}`)
  return res.json()
}

export function useConversations(page = 1, limit = 50) {
  return useQuery({
    queryKey: ['converstions', page, limit],
    queryFn: () => fetchConversations(page, limit),
  })
}
