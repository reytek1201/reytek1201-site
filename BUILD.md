# How reytek1201.com is built

**Edit the source in `src/`, then rebuild.** Everything at the repo root (`index.html`, `assets/`, `origin/`, `music/`, `projects/`, `gaming/`, `art/`) is generated output. Each build overwrites it, so changes made there are lost.

```
python3 src/build.py            # rebuild the site at the repo root
python3 src/build.py --preview  # also write single-file previews to src/_preview/
```

Python 3 is all it needs, with no packages to install. Commit the source and the rebuilt output together.

## Where things live

| To change | Edit |
|---|---|
| Homepage: hero, year counter, key moments, turntable, hub doors, signup | `src/site.src.html` (markup, then the CSS in its `<style>` block, then the scripts) |
| Shared styles for every page | the `<style>` block in `src/site.src.html` (built into `assets/site.css`) |
| Homepage engine: vortex, deck, cursor, scroll story | the large `<script>` in `src/site.src.html` (built into `assets/main.js`) |
| Origin page text | `src/pages/origin.html` |
| The four-lane timeline (cards, years, photos) | `src/pages/origin-timeline.html` |
| Music, Projects, Gaming and Art pages | `src/pages/music.html`, `projects.html`, `gaming.html`, `art.html` |
| Track list (title, file, cover, BPM, NEW badge) | the `const TRACKS = [...]` line in `src/site.src.html` (the Music page and Art gallery are generated from it) |
| Inner-page frame (cursor, social rail, buttons) | `src/js/shell.js` |
| Music page player and the Gaming countdown | `src/js/pages.js` |
| Homepage title, description, social cards and Google Analytics tag | `src/seo.py` |
| Inner-page titles and descriptions | the `PAGES` table near the end of `src/build.py` |

Images live in `img/`, audio in `audio/` and cover art in `covers/` at the repo root, and pages reference them as `img/...`. The build rewrites those paths for pages in subfolders, and scripts resolve them from the site root with `rtUrl()`.

`src/portrait.b64` and `src/anybody.b64` are the hero portrait and the wordmark font, base64-encoded. The build inlines them. Don't edit them by hand.

## Rules of the road

- Writing is in first person, Reytek's own voice.
- Don't mention his dad anywhere except the 1984 arcades line.
- Keep these off the site: the lifestyle change (behind KeyMacro), and the film placements.
- The site is plain HTML, CSS and JS with no framework. three.js r128 comes from cdnjs.
- Check every change at phone width (about 390px) as well as desktop.
- To test locally, serve the repo root (`python3 -m http.server`) and open http://localhost:8000. Audio and the 3D deck won't load from `file://`.

## Roadmap

See `PLAN.md`. Phases 1 to 3 are done (shared assets, the Origin page, the door pages). Next is Phase 4: music that keeps playing between pages, using a router that swaps page content while the audio engine keeps running.
