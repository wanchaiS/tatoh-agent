import { useState } from "react"

interface SuggestedAnswersProps {
  options: string[]
  onSelect: (option: string) => void
  disabled?: boolean
}

export function SuggestedAnswers({
  options,
  onSelect,
  disabled = false,
}: SuggestedAnswersProps) {
  const [selected, setSelected] = useState<string | null>(null)

  const handleClick = (option: string) => {
    if (disabled || selected) return
    setSelected(option)
    onSelect(option)
  }

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => (
        <button
          key={option}
          onClick={() => handleClick(option)}
          disabled={disabled || selected !== null}
          className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
            selected === option
              ? "border-blue-500 bg-blue-500/20 text-blue-400"
              : selected !== null || disabled
                ? "cursor-not-allowed border-border bg-muted/50 text-muted-foreground opacity-50"
                : "cursor-pointer border-border bg-muted text-foreground hover:border-blue-500/50 hover:bg-blue-500/10"
          }`}
        >
          {option}
        </button>
      ))}
    </div>
  )
}
