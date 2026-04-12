import * as React from 'react'

interface SpecTagProps {
  children: React.ReactNode
  className?: string
}

export function SpecTag({ children, className = '' }: SpecTagProps) {
  return (
    <span
      className={`px-3 py-1.5 rounded-full text-xs font-medium ${className}`}
      style={{ backgroundColor: 'var(--tropical-sand)', color: 'oklch(0.2 0 0)' }}
    >
      {children}
    </span>
  )
}
