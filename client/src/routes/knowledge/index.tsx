import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useEffect } from 'react'

function KnowledgeIndex() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate({ to: '/knowledge/rooms' })
  }, [navigate])
  return null
}

export const Route = createFileRoute('/knowledge/')({
  component: KnowledgeIndex,
})
