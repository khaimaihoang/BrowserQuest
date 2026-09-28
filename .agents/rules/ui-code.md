---
paths:
  - "client/ts/ui/**"
  - "client/css/**"
  - "client/index.html"
  - "client/img/**"
  - "client/ui-lab.html"
  - "tools/ui/**"
  - "tools/ui-pack.py"
---

# UI Code Rules

- UI assets (sprites/slices) go through the Minifantasy slice pipeline — see
  `docs/ui-slice-pipeline.md` and `tools/ui/slices.json`. Do NOT hand-crop or
  hand-write 9-slice assets; add a manifest entry and run `npm run ui:pack`.
- UI must NEVER own or directly modify game state — display only, use commands/events to request changes
- All UI text must go through the localization system — no hardcoded user-facing strings
- Support both keyboard/mouse AND gamepad input for all interactive elements
- All animations must be skippable and respect user motion/accessibility preferences
- UI sounds trigger through the audio event system, not directly
- UI must never block the game thread
- Scalable text and colorblind modes are mandatory, not optional
- Test all screens at minimum and maximum supported resolutions
