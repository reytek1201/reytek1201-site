# REYTEK — Interactive Coming-Soon Hub · Phased Plan

> Home for Reytek's music, art, projects and gaming. Also a portfolio piece for rayburgos.com, so the bar is "people screenshot it."
> Built here first, then finished in Cursor. Every phase ends with a working, deployable state.

---

## 1. Creative direction: "The Vortex"

The whole site grows out of the portrait: a figure half in shadow, ringed by light-painted trails, with one lit blue eye. That ring of light trails is the **signature motif**. It's the hero, the loader, the cursor, the section transitions and the audio visualizer.

| Element | Source | Use |
|---|---|---|
| Light-trail vortex | Portrait (light painting) | WebGL hero, loader, audio-reactive core |
| Monochrome + one cold accent | The single blue eye | Base palette is near-black/bone-white; cyan only where something is *alive* |
| Neon circuitry + hex cells | Suno banner | Grid and hex structure for the hub/projects section; magenta as the second accent |
| Terminal prompt | Current page (`> initializing hub`) | Keep the voice: boot sequence, status lines, mono labels |
| 1990s rave → modern | Bio | Scroll narrative: strobe, warehouse grain, BPM, then clean cinematic precision |

**Mood words:** dark, cinematic, precise, warm underneath. Late-night, not neon-cheese.

### Palette (draft tokens)
```
--void:      #050608   (page)
--ink:       #0B0D12   (panels, carried over)
--bone:      #EDEBE6   (primary text, light trails)
--ash:       #8A8C94   (secondary text)
--signal:    #22D3EE   (cyan: the eye, live states, audio)
--pulse:     #E0388F   (magenta: hover heat, beat flashes, sparingly)
--violet:    #8B5CF6   (legacy accent; keep for continuity or retire)
```
### Type (draft)
- Display: a tall, condensed grotesk with character (e.g. *Monument Extended*, *Neue Machina* or *Druk*; pick in Phase 0)
- Mono: **IBM Plex Mono** (carried over for terminal and labels)
- Body: **Public Sans** or **Inter Tight**

---

## 2. Page architecture (one scrolling page plus later routes)

```
00  BOOT        Terminal boot lines → the vortex ignites from a single point of light
01  HERO        WebGL light-trail vortex · REYTEK wordmark · cursor bends the trails
                [ ENTER WITH SOUND ] / [ ENTER SILENT ]
02  ORIGIN      Pinned scroll story: 1991 → now. Strobe, grain, flyer typography, BPM counter
                scrubs from 128 to today's tempo; the dancefloor dissolves into the vortex
03  PORTRAIT    Iris-mask reveal: the vortex opens and the portrait comes through it;
                the eye picks up the cyan; parallax depth on the light trails
04  BIO         The reworked bio, line-by-line reveal tied to scroll
05  THE HUB     Four doors: MUSIC · ART · PROJECTS · GAMING. Hex/circuit grid that lights
                up toward the cursor; each door previews what's coming (status: soon)
06  SIGNAL      Music teaser: player plus live visualizer (the vortex again, small and reactive)
07  BUILDING    Project cards: KeyMacro.fit · SlidePress · rayburgos.com (+ more),
                magnetic 3D tilt, circuit traces drawing in between them
08  TRANSMIT    "Join the transmission": email signup with a satisfying confirm animation
09  FOOTER      Socials · "Designed & built by rayburgos.com" (the portfolio hook)
```
Global layer: Lenis smooth scroll · custom cursor (a small light-trail ring) · sound toggle · grain overlay · scroll-progress "tracklist" rail.

---

## 3. Tech stack (matches FunkHarp so the patterns carry over)

| Concern | Choice | Why |
|---|---|---|
| Framework | **Next.js 16 (App Router) + React 19 + TypeScript** | Same as FunkHarp; hub routes later (`/music`, `/art`, …) |
| Styling | **Tailwind CSS 4** + CSS variables | Same as FunkHarp |
| UI motion | **framer-motion** | Reuse FunkHarp's `Reveal`, `Magnetic`, `useMedia`, `useRamp` patterns |
| Scroll | **Lenis** + framer `useScroll` | Buttery scroll; pinned sections |
| Hero / 3D | **three.js via @react-three/fiber + drei**, custom GLSL | Light-trail vortex, iris reveal, post-processing bloom |
| Post FX | **@react-three/postprocessing** | Bloom, chromatic aberration, film grain |
| Audio | **Web Audio API** (`AnalyserNode`) | Beat and frequency data drive the vortex. *Needs self-hosted audio files: Suno embeds can't be analysed (cross-origin).* |
| Signup | **Supabase** (`subscribers` table, server action) | Same pattern as FunkHarp's `0004_subscribers.sql` |
| Hosting | **Vercel** | Same as FunkHarp; preview deploys per phase |
| Analytics | Vercel Analytics | Lightweight |

> Optional: GSAP + ScrollTrigger only if one pinned sequence becomes painful in framer-motion. Default is **one** animation system.

### Folder layout
```
app/
  layout.tsx            fonts, metadata, Lenis provider, cursor, grain
  page.tsx              composes the sections
  actions/subscribe.ts  server action → Supabase
components/
  scene/                Vortex.tsx, vortex.glsl, IrisReveal.tsx, Effects.tsx
  sections/             Boot, Hero, Origin, Portrait, Bio, Hub, Signal, Building, Transmit, Footer
  ui/                   Reveal, Magnetic, Cursor, SoundToggle, SplitText, ProgressRail
lib/
  site.ts               ALL copy, links, projects, socials (single source of truth)
  audio.ts              AudioContext + analyser store
  useMedia.ts, useReducedMotion, useGPUTier.ts
public/
  img/ audio/ og/
```

---

## 4. Phases

Each phase ends deployed to a Vercel preview, with a short checklist.

### Phase 0: Direction & Content (no code)
- [ ] Lock the name treatment: **REYTEK** (artist) vs **reytek1201** (handle). Recommend: REYTEK as the wordmark, @reytek1201 as the handle
- [ ] Rework the bio together (draft below)
- [ ] Choose display font and finalise palette tokens
- [ ] Gather assets: high-res portrait (ideally the subject cut out from the trails, for parallax depth), 1–3 track previews (MP3/OGG, 30–60 s), any rave-era photos/flyers, art pieces
- [ ] Decide hub doors: Music / Art / Projects / Gaming (confirm list and order)
- [x] Quick visual prototype of the hero vortex → `prototype/vortex-01.html` (awaiting approval)

### Phase 1: Foundation
- [ ] Scaffold Next 16 + TS + Tailwind 4 (mirror FunkHarp config, React Compiler on)
- [ ] Design tokens in `globals.css`, fonts in `layout.tsx`
- [ ] `lib/site.ts` with all copy and links (ported from current `index.html`)
- [ ] Port `Reveal`, `Magnetic`, `useMedia` from FunkHarp
- [ ] Lenis provider, grain overlay, base section shells (static content in place)
- [ ] `useReducedMotion` + GPU-tier detection wired from day one
- [ ] Repo → Vercel, preview deploys working
- ✅ *Done when:* the full page scrolls top to bottom with real copy, unstyled motion

### Phase 2: The Signature Moment (Boot + Hero)
- [ ] Boot sequence: terminal lines type out, then a point of light ignites
- [ ] **Vortex shader**: 2–5k particle trails on noisy orbital paths (GPU instancing, trail fade), bloom
- [ ] Cursor interaction: trails bend/attract toward the pointer; click sends a shockwave ring
- [ ] Wordmark: split-letter reveal, subtle RGB split on hover
- [ ] Enter with sound / Enter silent gate
- [ ] Fallbacks: low-tier GPU → fewer particles; no WebGL / reduced motion → pre-rendered video loop or a still
- ✅ *Done when:* first 5 seconds are portfolio-grade on desktop **and** mid-range phone at ~60fps

### Phase 3: Scroll Narrative (Origin + Portrait + Bio)
- [ ] Origin: pinned section, years scrub 1991 → now, strobe flashes on beat, flyer-style type collage, grain
- [ ] BPM counter tied to scroll progress
- [ ] Transition: the dancefloor/strobe dissolves into the vortex
- [ ] Portrait iris reveal (shader mask), layered parallax (trails / face / background), cyan eye glint
- [ ] Bio line-by-line reveal
- ✅ *Done when:* scrolling the story feels like one continuous camera move, no "slide" seams

### Phase 4: The Hub (Doors + Building + Signal)
- [ ] Hex/circuit grid background, cells light up near the cursor (canvas or shader)
- [ ] Four doors with hover previews, "status: soon" terminal labels, magnetic tilt
- [ ] Project cards (KeyMacro.fit, SlidePress, rayburgos.com, …): 3D tilt, circuit traces animate between them
- [ ] Music teaser player UI (play/pause, scrub, track title)
- ✅ *Done when:* every interactive element has hover, focus and touch states

### Phase 5: Sound Layer
- [ ] `lib/audio.ts`: shared AudioContext + analyser (bass/mid/high bands, beat detection)
- [ ] Vortex reacts: bass → ring expansion, highs → trail sparkle, beat → magenta pulse
- [ ] Subtle UI sounds on hover/click (optional, off when silent)
- [ ] Persistent sound toggle; never autoplay audio
- ✅ *Done when:* entering with sound transforms the page; silent mode still feels complete

### Phase 6: Conversion, SEO & Backend
- [ ] Supabase `subscribers` table + RLS + server action (FunkHarp pattern), honeypot/rate limit
- [ ] Signup success animation (the vortex collapses into a point, then "transmission received")
- [ ] Metadata, OG image (1200×630 vortex + wordmark), favicon/icon set, sitemap, robots, JSON-LD (`MusicGroup`/`Person`)
- [ ] Vercel Analytics; track enter-with-sound, signups, project clicks
- ✅ *Done when:* signups land in Supabase and link previews look premium

### Phase 7: Polish, Performance, Launch
- [ ] Lighthouse: Perf ≥ 85 mobile / ≥ 95 desktop, A11y ≥ 95
- [ ] Lazy-load three.js below the boot; dynamic import scenes; image optimisation
- [ ] Full keyboard path, visible focus, reduced-motion pass, screen-reader copy for visual sections
- [ ] Cross-device QA: iOS Safari, Android Chrome, Firefox, low-power mode
- [ ] Easter egg (e.g. typing `1991` plays a hidden rave loop; Konami code → strobe mode)
- [ ] Attach domain, production deploy, "Designed & built by rayburgos.com" credit + case-study notes
- ✅ *Done when:* shipped

### Later (post-launch hub routes)
`/music` releases + player · `/art` gallery · `/projects` case studies · `/gaming` · an admin like FunkHarp's for adding releases without code.

---

## 5. Cursor handoff checklist
- [ ] `CLAUDE.md` / `AGENTS.md` with stack, conventions, the Next 16 note FunkHarp uses, and "copy lives in `lib/site.ts`"
- [ ] `.cursor/rules/` → `motion.mdc` (always respect reduced motion; one animation system), `scene.mdc` (r3f conventions, dispose resources), `style.mdc` (tokens only, no raw hex)
- [ ] This `PLAN.md` kept current; checkboxes ticked as phases land
- [ ] Each section is a self-contained component, so Cursor can iterate on one without touching others

---

## 6. Bio: first rework draft (to refine in Phase 0)

> Reytek learned electronic music on the dancefloor. The early-'90s rave scene, with its warehouses, borrowed sound systems and rooms full of strangers moving as one, showed him what a kick drum can do to people, and that's still the standard he works to.
>
> His sound has grown darker and more deliberate since: cinematic in scale, exact in its synthesis, made with the patience of someone who has been listening for a long time. It's built for the big speaker stack and the drive home after.
>
> Under the same name he makes visuals, art and software too, all with one aim: make something that moves people.

*Shorter tagline options:* "Electronic music with a memory." · "Born on the dancefloor. Built for the dark." · "From the warehouse to the widescreen."

---

## 7. Open decisions
1. Wordmark: REYTEK or REYTEK1201?
2. Hub doors: Music / Art / Projects / Gaming. Final list?
3. Do you have (or can you export) track audio files for the audio-reactive layer?
4. Keep violet from the old page, or go to the monochrome + cyan + magenta palette?
5. Domain for the hub?
