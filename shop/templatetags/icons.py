"""
Small line-icon set for the category tiles, drawn as inline SVG (stroke = currentColor,
so they pick up CSS color). Generic pictograms, not traced from any reference image.
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_PATHS = {
    "painting": '<rect x="5" y="5" width="30" height="24" rx="1.5"/><path d="M5 22l7-7 6 5 6-8 11 10" fill="none"/><circle cx="14" cy="13" r="2.5" fill="currentColor" stroke="none"/><path d="M12 29v6M28 29v6" stroke-linecap="round"/>',
    "lotus": '<path d="M20 34c-8-3-9-12-9-18 4 2 7 6 9 11 2-5 5-9 9-11 0 6-1 15-9 18z"/><path d="M20 34c-5-6-5-14-2-22 3 3 4 8 4 13 2-6 6-10 10-11-1 6-4 14-12 20z"/><path d="M20 34c5-6 5-14 2-22-3 3-4 8-4 13-2-6-6-10-10-11 1 6 4 14 12 20z"/>',
    "home": '<path d="M6 18L20 6l14 12" fill="none"/><path d="M10 16v16h20V16" fill="none"/><rect x="16" y="24" width="8" height="8" fill="none"/>',
    "lamp": '<path d="M13 12l7-7 7 7-4 8H17z" fill="none"/><path d="M20 20v6" /><rect x="12" y="26" width="16" height="8" rx="1" fill="none"/>',
    "pot": '<path d="M14 8h12M16 8c-3 6-3 10 0 14M24 8c3 6 3 10 0 14" fill="none"/><path d="M12 22c0 7 3 12 8 12s8-5 8-12" fill="none"/>',
    "scarf": '<path d="M6 12c6-4 12-4 14 0s8 4 14 0" fill="none"/><path d="M6 22c6-4 12-4 14 0s8 4 14 0" fill="none"/><path d="M6 12v10M34 12v10" fill="none"/>',
    "gift": '<rect x="7" y="16" width="26" height="18" fill="none"/><path d="M7 22h26" /><path d="M20 16v18" /><path d="M20 16c-2-6-10-6-9-1 1 3 5 1 9 1zM20 16c2-6 10-6 9-1-1 3-5 1-9 1z" fill="none"/>',
    "brush": '<path d="M27 6l7 7-14 14-8 2 2-8z" fill="none"/><path d="M12 28c-1 4-3 5-6 5 2-1 2-3 1-5" fill="none"/>',
    "leaf": '<path d="M10 30C8 16 18 7 32 8c1 14-8 24-22 22z" fill="none"/><path d="M10 30c6-8 12-13 20-18" fill="none"/>',
}


@register.simple_tag
def category_icon(key, size=32):
    body = _PATHS.get(key, _PATHS["leaf"])
    return mark_safe(
        f'<svg viewBox="0 0 40 40" width="{size}" height="{size}" fill="none" '
        f'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{body}</svg>'
    )


# Generic UI glyphs (cart, heart, search, ...): plain geometric strokes, the same
# family of shape any icon set uses for these universal concepts.
_UI = {
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 20c1.5-4.5 5-6 8-6s6.5 1.5 8 6"/>',
    "heart": '<path d="M12 21S4 14.6 4 9.3C4 6.4 6.3 4 9.2 4c1.7 0 3.2.9 2.8.8C12.8 4 14.3 4 16 4c2.9 0 5.2 2.4 5.2 5.3C21.2 14.6 12 21 12 21z"/>',
    "heart-filled": '<path d="M12 21S4 14.6 4 9.3C4 6.4 6.3 4 9.2 4c1.7 0 3.2.9 2.8.8C12.8 4 14.3 4 16 4c2.9 0 5.2 2.4 5.2 5.3C21.2 14.6 12 21 12 21z" fill="currentColor"/>',
    "cart": '<circle cx="9" cy="21" r="1.4" fill="currentColor" stroke="none"/><circle cx="18" cy="21" r="1.4" fill="currentColor" stroke="none"/><path d="M2.5 3h2.7l2 12.2A2 2 0 0 0 9.2 17h9.1a2 2 0 0 0 2-1.6L22 7H6"/>',
    "chevron-down": '<path d="M6 9l6 6 6-6"/>',
    "chevron-left": '<path d="M15 18l-6-6 6-6"/>',
    "chevron-right": '<path d="M9 18l6-6-6-6"/>',
    "star": '<path d="M12 3.5l2.6 5.3 5.9.8-4.2 4.1 1 5.8L12 16.7l-5.3 2.8 1-5.8L3.5 9.6l5.9-.8z" fill="currentColor" stroke="none"/>',
    "star-outline": '<path d="M12 3.5l2.6 5.3 5.9.8-4.2 4.1 1 5.8L12 16.7l-5.3 2.8 1-5.8L3.5 9.6l5.9-.8z"/>',
    "truck": '<rect x="1.5" y="7" width="13" height="9"/><path d="M14.5 10h3.5l3 3v3h-6.5z"/><circle cx="6" cy="18.5" r="1.6" fill="currentColor" stroke="none"/><circle cx="17" cy="18.5" r="1.6" fill="currentColor" stroke="none"/>',
    "shield": '<path d="M12 3l7 3v5c0 5-3.2 8.4-7 10-3.8-1.6-7-5-7-10V6z"/><path d="M9 12l2 2 4-4"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.7 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.7-3.8-9S9.5 5.6 12 3z"/>',
    "gift": '<rect x="3" y="9" width="18" height="12"/><path d="M3 13h18"/><path d="M12 9v12"/><path d="M12 9C10 3 4 4 5.5 7.5S12 9 12 9zM12 9c2-6 8-5 6.5-1.5S12 9 12 9z"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7"/>',
    "check-circle": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.6 2.6L16 9.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    "package": '<path d="M21 8l-9-5-9 5 9 5 9-5z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/>',
    "map-pin": '<path d="M12 21s7-6.3 7-12a7 7 0 10-14 0c0 5.7 7 12 7 12z"/><circle cx="12" cy="9" r="2.5"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="1"/><path d="M3 6l9 7 9-7"/>',
    "phone": '<path d="M6.6 10.8c1.4 2.7 3.8 5.1 6.6 6.6l2.1-2.1c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.5.6.6 0 1 .5 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.3c.6 0 1 .4 1 1 0 1.2.2 2.4.6 3.5.1.4 0 .8-.3 1.1z"/>',
    "trash": '<path d="M4 7h16M9 7V5a1 1 0 011-1h4a1 1 0 011 1v2m-8 0l1 12a1 1 0 001 1h6a1 1 0 001-1l1-12"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "camera": '<rect x="3" y="7" width="18" height="13" rx="2"/><circle cx="12" cy="13.5" r="3.5"/><path d="M8 7l1.5-2.5h5L16 7"/>',
    "leaf-small": _PATHS["leaf"],
}


@register.simple_tag
def ui_icon(key, size=20, weight=1.8):
    body = _UI.get(key, "")
    return mark_safe(
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
        f'stroke="currentColor" stroke-width="{weight}" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{body}</svg>'
    )
