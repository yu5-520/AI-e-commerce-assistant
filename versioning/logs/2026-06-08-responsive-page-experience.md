# 2026-06-08 Responsive Page Experience

## Change Type
frontend-responsive-layout / user-experience / device-adaptation

## Goal
Optimize the user page experience across desktop, tablet, and mobile without changing backend APIs or product result schema.

## Files Changed
- `frontend/styles.css`
- `frontend/README.md`
- `versioning/VERSION.md`
- `versioning/CHANGELOG.md`
- `runtime/version_manifest.json`

## Desktop Experience
- Left sidebar remains sticky for dashboard navigation.
- Input panel remains sticky so users can regenerate while reviewing long results.
- Main content width increased through `--content-max`.
- Output panel receives more space for product result cards.

## Tablet Experience
- Sidebar width is compressed.
- Input and output remain in two columns to preserve working efficiency.
- Decorative hero card is hidden to preserve working space.
- Tracking cards collapse to two columns.

## Mobile Experience
- Page becomes a single-column flow.
- Sidebar navigation becomes a horizontal scroll bar.
- Mode cards become horizontal swipe cards.
- Generate button becomes bottom-sticky for thumb operation.
- Inputs/selects use 16px text to avoid mobile browser zoom-in.
- Spacing and card radius are reduced to lower visual pressure.

## Preserved
- Productized rendering from v0.8.1.
- Generation configuration from v0.8.2.
- Backend API paths and local backflow folders.
- GitHub Issue -> Actions -> DeepSeek -> Issue comment workflow.

## Current Boundary
Responsive layout is CSS-level optimization only. It still needs real-device screenshot validation on iPhone, iPad, Android phone, Android tablet, and desktop browsers.
