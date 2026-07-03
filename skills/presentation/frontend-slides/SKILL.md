---
schema_version: 1
tags:
  - "presentation"
  - "slides"
  - "html"
topics:
  - "HTML slide decks"
  - "web presentations"
  - "template selection"
  - "offline templates"
status: seed
created: 2026-06-05
updated: 2026-06-05
sources:
  - "https://github.com/zarazhangrui/frontend-slides"
  - "https://github.com/zarazhangrui/beautiful-html-templates"
  - "user requirement 2026-06-05: vendor all templates for offline enterprise Codex and Claude"
source_count: 3
aliases:
  - "frontend-slides"
  - "html slides"
  - "web deck"
  - "presentation"
  - "slide deck"
  - "agentic ai intro"
skill_id: presentation/frontend-slides
summary: "Create polished offline-capable HTML slide decks from a brief, existing content, or PowerPoint source using vendored frontend slide templates."
model_role: thinking
depends_on:
  - meta/contributing
related:
  - writing/humanizer
  - meta/deployment
---

# Frontend Slides

<!-- learned: 2026-06 | project: cortex-frontend-slides | model: thinking-model -->

Use this skill when creating, converting, or improving an HTML
presentation, especially for first-run onboarding decks, agentic AI
introductions, roadmap stretch decks, or any request for a polished web
slide deck.

## Core Rule

Build a self-contained HTML deck that works offline. Use the vendored
Frontend Slides workflow and vendored Beautiful HTML Templates payload in
`skills/presentation/frontend-slides/vendor/`; do not depend on GitHub,
CDNs, remote template galleries, or network fetches at runtime unless
the user explicitly asks for live assets.

## Workflow

1. Detect the mode: new presentation, PowerPoint conversion, or
   improvement to an existing HTML deck.
2. Ask whether the deck is speaker-led or reading-first. Use lower
   density for talks and higher but still readable density for async
   reports.
3. Read the upstream operating skill at
   `skills/presentation/frontend-slides/vendor/frontend-slides/SKILL.md`
   before building the first deck in a session.
4. Start from the selected template's contract before inventing new
   structure. For Frontend Slides bold templates, use
   `skills/presentation/frontend-slides/vendor/frontend-slides/html-template.md`
   and the shared runtime at
   `skills/presentation/frontend-slides/vendor/frontend-slides/bold-template-pack/deck-stage.js`
   where possible. Author slides as direct children of `<deck-stage>`
   at 1920x1080, and let the runtime own scaling, navigation, tap zones,
   slide labels, and print behavior.
5. If the user has not chosen a style, generate three compact visual
   previews and let the user pick one before building the full deck.
6. For template-backed styles, read
   `skills/presentation/frontend-slides/vendor/beautiful-html-templates/index.json`
   first, then inspect only shortlisted template folders under
   `skills/presentation/frontend-slides/vendor/beautiful-html-templates/templates/`.
7. Build the final HTML deck as a local artifact with inline or local
   CSS/JS and local assets. Prefer vendored fonts from
   `skills/presentation/frontend-slides/assets/fonts/google-fonts.css`
   before remote font links. Prefer local references to vendored runtime
   assets; inline them only when the deck must be a single portable file.
   Preserve license notices when copying upstream template material.
8. Verify by opening or screenshotting the deck at a desktop 16:9
   viewport and at least one narrower viewport. Fix overflow, overlap,
   clipped text, hidden slides, broken assets, and unreadable type.

## Offline Payload

The vendored payload is intentionally large because some target
enterprise Codex and Claude environments have no internet access:

- `vendor/frontend-slides/`: upstream skill, fixed viewport CSS, style
  presets, HTML template, animation patterns, scripts, and bold template
  pack.
- `vendor/beautiful-html-templates/`: upstream template index,
  operating manual, runtime helpers, scripts, screenshots, and all
  template folders.
- `assets/fonts/`: template-referenced Google Fonts WOFF2 files, local
  `@font-face` CSS, and documented exceptions for referenced fonts that
  are not available through the Google Fonts CSS API.

Treat these files as source assets. If a template pack update is needed,
refresh the vendored files in Cortex, preserve `LICENSE` files, validate,
commit, and redeploy native packages.

Refresh the font payload with:

```bash
python skills/presentation/frontend-slides/scripts/vendor_google_fonts.py
```

Check that the font manifest still covers the vendored templates with:

```bash
python skills/presentation/frontend-slides/scripts/vendor_google_fonts.py --check-template-fonts
```

## PowerPoint Conversion

For `.pptx` conversion, use the vendored extraction helper only when the
environment has the required Python dependency:

```bash
python skills/presentation/frontend-slides/vendor/frontend-slides/scripts/extract-pptx.py input.pptx output-dir
```

If `python-pptx` is missing and dependencies cannot be installed, tell
the user and offer to build from exported text/images instead.

## Caveats

Do not paste the full template library into context. Start from the
compact indexes and load only the template candidates needed for the
current deck.

Avoid generic AI slide aesthetics: overused system fonts, purple
gradients on white backgrounds, predictable SaaS card grids, and
decorative visuals unrelated to the topic. Pick a style with a point of
view that matches the audience and content.

Generated native packages for `SKILL.md` runtimes need to carry this
skill's `vendor/` directory. If a deployed package only contains
`SKILL.md`, it is incomplete for offline use.

## Completion Criteria

The skill has been applied when the deck is a local offline-capable HTML
artifact, uses a chosen or justified visual system, fits within the fixed
stage without scroll or overlap, preserves local assets and licenses,
and has been visually checked before delivery.
