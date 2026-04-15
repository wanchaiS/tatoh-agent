import { useQuery } from '@tanstack/react-query'
import type { BaseMessage } from '@langchain/core/messages'
import type { GenUIMessage } from '@/components/GenUIRenderer'
import { apiFetch } from '@/lib/api'

interface ThreadState {
  values: {
    messages?: BaseMessage[]
    ui?: (GenUIMessage & { message?: { id?: string } })[]
    [key: string]: unknown
  }
  next: string[]
  checkpoint: Record<string, unknown>
  created_at: string | null
}

async function fetchThreadState(threadId: string): Promise<ThreadState> {
  const res = await apiFetch(`/api/threads/${threadId}/state`)
  return res.json()
}

export function useThreadState(threadId: string | null) {
  return useQuery({
    queryKey: ['thread-state', threadId],
    queryFn: () => fetchThreadState(threadId!),
    enabled: !!threadId,
  })
}
