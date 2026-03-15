import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/playground')({
  component: PlaygroundPage,
})

const IMAGES = ['overview', 'test2'] as const

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-bold text-foreground">{title}</h2>
      {children}
    </section>
  )
}

function ImgWithInfo({ src, label }: { src: string; label: string }) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <img
        src={src}
        alt={label}
        className="rounded-lg border border-border"
        onLoad={(e) => {
          const img = e.currentTarget
          const info = img.nextElementSibling
          if (info) info.textContent = `${img.naturalWidth} x ${img.naturalHeight}`
        }}
      />
      <p className="text-xs text-muted-foreground/60"></p>
    </div>
  )
}

function PlaygroundPage() {
  const [cardWidth, setCardWidth] = useState(256)

  return (
    <div className="min-h-screen bg-background text-foreground p-6 max-w-5xl mx-auto space-y-10">
      <div>
        <h1 className="text-2xl font-bold">Thumbnail Cropping Playground</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Compare current <code className="bg-muted px-1 rounded">thumbnail(600,400)</code> vs proposed{' '}
          <code className="bg-muted px-1 rounded">ImageOps.fit(600,400, top-anchor)</code>
        </p>
      </div>

      {IMAGES.map((name) => (
        <div key={name} className="space-y-8 border-t border-border pt-8">
          <h2 className="text-xl font-bold capitalize">{name}.jpg</h2>

          {/* Row 1: Raw comparison */}
          <Section title="Raw Comparison">
            <div className="grid grid-cols-3 gap-4">
              <ImgWithInfo
                src={`/playground/${name}_original.jpg`}
                label="Original (scaled)"
              />
              <ImgWithInfo
                src={`/playground/${name}_thumb_current.jpg`}
                label="Current: thumbnail(600,400)"
              />
              <ImgWithInfo
                src={`/playground/${name}_thumb_proposed.jpg`}
                label="Proposed: fit(600,400, top)"
              />
            </div>
          </Section>

          {/* Row 2: Card Aspect Ratio Comparison */}
          <Section title="Proposed Landscape (600x400) at Different Card Ratios">
            <p className="text-xs text-muted-foreground -mt-2 mb-2">
              Same thumbnail, different card aspect ratios — see how much content survives
            </p>
            <div className="flex items-center gap-3 mb-2">
              <label className="text-xs font-medium text-muted-foreground whitespace-nowrap">Card width</label>
              <input
                type="range"
                min={128}
                max={400}
                value={cardWidth}
                onChange={(e) => setCardWidth(Number(e.target.value))}
                className="w-48"
              />
              <span className="text-xs tabular-nums text-muted-foreground">{cardWidth}px</span>
            </div>
            <div className="flex gap-4 overflow-x-auto pb-2">
              {([
                { ratio: 'aspect-[3/2]', label: '3:2 (matches thumb)' },
                { ratio: 'aspect-[4/3]', label: '4:3' },
                { ratio: 'aspect-square', label: '1:1' },
                { ratio: 'aspect-[4/5]', label: '4:5' },
                { ratio: 'aspect-[2/3]', label: '2:3 (current card)' },
              ] as const).map(({ ratio, label }) => (
                <div key={ratio} className="space-y-1 shrink-0">
                  <p className="text-xs font-medium text-muted-foreground">{label}</p>
                  <div style={{ width: cardWidth }} className="rounded-2xl overflow-hidden bg-card shadow-md">
                    <div className={`${ratio} overflow-hidden relative`}>
                      <img
                        src={`/playground/${name}_thumb_proposed.jpg`}
                        alt={`proposed at ${label}`}
                        className="h-full w-full object-cover object-top"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent pointer-events-none" />
                    </div>
                    <div className="p-3">
                      <div className="font-bold text-lg leading-tight text-foreground">
                        Sample Room
                      </div>
                      <div className="text-xs text-muted-foreground/70 mt-0.5">Bungalow</div>
                      <div className="text-xs text-muted-foreground mt-1">4 guests</div>
                      <div className="mt-2">
                        <span className="text-xs text-muted-foreground">Starting </span>
                        <span className="font-bold text-tropical-coral">&#3647;3,500</span>
                        <span className="text-xs font-normal text-muted-foreground ml-1">/ night</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Section>

          {/* Row 3: Portrait thumbnail vs Landscape at 2:3 card */}
          <Section title="Landscape vs Portrait Thumbnail in 2:3 Card">
            <p className="text-xs text-muted-foreground -mt-2 mb-2">
              Option A: change card ratio to match landscape thumb &mdash; Option B: generate portrait thumb to match current card
            </p>
            <div className="flex gap-6">
              {([
                { src: `proposed`, label: 'Landscape 600x400 (proposed)' },
                { src: `portrait`, label: 'Portrait 400x600 (new)' },
              ] as const).map(({ src, label }) => (
                <div key={src} className="space-y-1">
                  <p className="text-xs font-medium text-muted-foreground">{label}</p>
                  <div style={{ width: cardWidth }} className="rounded-2xl overflow-hidden bg-card shadow-md">
                    <div className="aspect-[2/3] overflow-hidden relative">
                      <img
                        src={`/playground/${name}_thumb_${src}.jpg`}
                        alt={`${label} in 2:3 card`}
                        className="h-full w-full object-cover object-top"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent pointer-events-none" />
                    </div>
                    <div className="p-3">
                      <div className="font-bold text-lg leading-tight text-foreground">
                        Sample Room
                      </div>
                      <div className="text-xs text-muted-foreground/70 mt-0.5">Bungalow</div>
                      <div className="text-xs text-muted-foreground mt-1">4 guests</div>
                      <div className="mt-2">
                        <span className="text-xs text-muted-foreground">Starting </span>
                        <span className="font-bold text-tropical-coral">&#3647;3,500</span>
                        <span className="text-xs font-normal text-muted-foreground ml-1">/ night</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Section>

          {/* Row 3: As RoomFocusView hero */}
          <Section title="As RoomFocusView Hero (h-44 sm:h-64, object-cover)">
            <div className="grid grid-cols-2 gap-4">
              {(['current', 'proposed'] as const).map((variant) => (
                <div key={variant} className="space-y-1">
                  <p className="text-xs font-medium text-muted-foreground capitalize">{variant}</p>
                  <div className="relative h-44 sm:h-64 w-full overflow-hidden rounded-xl">
                    <img
                      src={`/playground/${name}_thumb_${variant}.jpg`}
                      alt={`${variant} in hero`}
                      className="h-full w-full object-cover"
                    />
                  </div>
                </div>
              ))}
            </div>
          </Section>
        </div>
      ))}
    </div>
  )
}
