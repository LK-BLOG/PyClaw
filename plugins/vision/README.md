# vision

Bundled plugin: image attachments are sent to the model as pixels instead of only a path.

- `attachments: vision.py` — the core calls `transform(item, context)` for every attachment;
  returning content blocks makes them part of the model message.
- `settings` — declares `VISION_MAX_BYTES` and `VISION_DETAIL`, which the settings panel
  picks up automatically and hot-reloads.
- `webui` — injects CSS and JS into the page; this one adds a panel and a badge.

Turn it off by putting `"!vision"` in `PLUGINS_ENABLED`.
