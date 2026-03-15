interface RatingBadgeProps {
  value: number
  max?: number
}

export function RatingBadge({ value, max = 10 }: RatingBadgeProps) {
  const isHigh = value >= 6
  return (
    <span
      className="px-3 py-1 rounded-full text-xs font-semibold"
      style={{
        backgroundColor: isHigh ? 'var(--tropical-coral)' : 'var(--tropical-sand)',
        color: isHigh ? 'white' : 'oklch(0.2 0 0)',
      }}
    >
      {value}/{max}
    </span>
  )
}
