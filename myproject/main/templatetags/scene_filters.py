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
    
    # Replace character names with links
    for char_name in character_names:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(char_name) + r'\b'
        replacement = f'<a href="/personas/?character={char_name}" class="text-primary fw-bold">{char_name}</a>'
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Replace location names with links
    for loc_name in location_names:
        pattern = r'\b' + re.escape(loc_name) + r'\b'
        replacement = f'<a href="/locations/?location={loc_name}" class="text-success fw-bold">{loc_name}</a>'
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return mark_safe(text)