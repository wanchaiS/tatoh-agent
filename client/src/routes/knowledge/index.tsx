import { createFileRoute, useNavigate } from '@tanstack/react-router'
import React from 'react'

export const Route = createFileRoute('/knowledge/')({
  component: () => {
    const navigate = useNavigate()
    React.useEffect(() => {
      navigate({ to: '/knowledge/rooms' })
    }, [navigate])
    return null
  },
})
