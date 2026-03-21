import { createFileRoute } from '@tanstack/react-router'
import { MainConversationPage } from '../pages/MainConversationPage'

export const Route = createFileRoute('/')({
  component: MainConversationPage,
})
