from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    try:
        return value - arg
    except (TypeError, ValueError):
        return value

@register.filter
def multiply(value, arg):
    try:
        return value * arg
    except (TypeError, ValueError):
        return 0

@register.filter
def key_color(key):
    """Dynamically assign a color class based on the key string."""
    if not key:
        return "bg-label-secondary"
    
    # Predefined premium color palette
    colors = ['primary', 'success', 'info', 'warning', 'danger', 'dark']
    
    # Use a simple hash to consistently map a key to a color
    import hashlib
    # We use MD5 for a good distribution of colors
    hash_val = int(hashlib.md5(key.encode()).hexdigest(), 16)
    idx = hash_val % len(colors)
    
    return f"bg-label-{colors[idx]}"

@register.filter
def format_number(value):
    """Format a number with thousands separators."""
    if value is None or str(value).strip() == '':
        return "0"
    try:
        return "{:,.0f}".format(float(value))
    except (ValueError, TypeError):
        return str(value)
