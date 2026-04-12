import { createFileRoute, redirect } from '@tanstack/react-router'
import { useAuthStore } from '../../stores/authStore'
import { KnowledgeLayout } from '../../pages/knowledge/KnowledgeLayout'

export const Route = createFileRoute('/knowledge')({
  beforeLoad: () => {
    if (!useAuthStore.getState().user) throw redirect({ to: '/login' })
  },
  component: KnowledgeLayout,
})
