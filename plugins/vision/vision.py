"""Turn an image attachment into a vision content block.

The core hands every attachment to plugins first; whatever a plugin returns becomes
part of the model message. Returning None means "I do not handle this one".
"""

MAX_DEFAULT = 1500000


def transform(item, context):
    if (item or {}).get("kind") != "image":
        return None
    data = item.get("data") or ""
    if not data.startswith("data:"):
        return None  # no bytes reached us; the core falls back to a path note
    limit = int((context.get("config") or {}).get("VISION_MAX_BYTES", MAX_DEFAULT) or MAX_DEFAULT)
    if len(data) > limit:
        return None
    detail = str((context.get("config") or {}).get("VISION_DETAIL", "auto") or "auto")
    return [{"type": "image_url", "image_url": {"url": data, "detail": detail}}]
