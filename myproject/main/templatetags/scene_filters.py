from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def linkify_characters_and_locations(text, story_data):
    if not text or not story_data:
        return text
    
    character_names = [persona['name'] for persona in story_data.get('persona_description', [])]
    location_names = [location['name'] for location in story_data.get('setting_description', [])]

    # Sort by length (longest first) to avoid partial matches
    character_names.sort(key=len, reverse=True)
    location_names.sort(key=len, reverse=True)

    placeholders = {}
    placeholder_counter = 0

    def replace_with_placeholder(match, url_template, css_class):
        nonlocal placeholder_counter
        placeholder = f"___PLACEHOLDER_{placeholder_counter}___"
        placeholders[placeholder] = f'<a href="{url_template}" class="{css_class}">{match.group(0)}</a>'
        placeholder_counter += 1
        return placeholder

    # Replace location names with placeholders
    for loc_name in location_names:
        pattern = r'\b' + re.escape(loc_name) + r'\b'
        text = re.sub(pattern, lambda m: replace_with_placeholder(m, f"/locations/?location={loc_name}", "text-success fw-bold"), text, flags=re.IGNORECASE)

    # Replace character names with placeholders
    for char_name in character_names:
        pattern = r'\b' + re.escape(char_name) + r'\b'
        text = re.sub(pattern, lambda m: replace_with_placeholder(m, f"/personas/?character={char_name}", "text-primary fw-bold"), text, flags=re.IGNORECASE)

    # Restore placeholders with actual HTML
    for placeholder, html in placeholders.items():
        text = text.replace(placeholder, html)

    return mark_safe(text)
