import { createFileRoute, redirect } from '@tanstack/react-router'
import { KnowledgeLayout } from '../../pages/knowledge/KnowledgeLayout'
import { AuthError } from '../../lib/api'
import { authQueryKey, fetchMe } from '../../lib/auth'

export const Route = createFileRoute('/knowledge')({
  beforeLoad: async ({ context }) => {
    try {
      await context.queryClient.fetchQuery({
        queryKey: authQueryKey,
        queryFn: fetchMe,
        staleTime: 60_000,
      })
    } catch (e) {
      if (e instanceof AuthError) throw redirect({ to: '/login' })
      throw e
    }
  },
  component: KnowledgeLayout,
})
