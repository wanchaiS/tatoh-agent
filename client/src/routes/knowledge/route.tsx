import { createFileRoute } from '@tanstack/react-router'
import { KnowledgeLayout } from '../../pages/knowledge/KnowledgeLayout'

export const Route = createFileRoute('/knowledge')({
  component: KnowledgeLayout,
})
