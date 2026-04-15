import { createFileRoute } from '@tanstack/react-router'
import { ConversationsPage } from '../../../pages/knowledge/conversations/ConversationsPage'

export const Route = createFileRoute('/knowledge/conversations/')({
  component: ConversationsPage,
})
