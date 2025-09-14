from collections.abc import Mapping, Sequence

def format_tree(obj, **ctx):
    """
    A YAML-ben lévő {partner} (és társai) placeholdereket futás előtt automatikusan kicseréljük konkrét értékekre,
    még mielőtt a riport-struktúrát renderelnénk.
    """
    if isinstance(obj, str):
        try:
            return obj.format(**ctx)
        except Exception:
            return obj
    if isinstance(obj, Mapping):
        return {k: format_tree(v, **ctx) for k, v in obj.items()}
    if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
        return [format_tree(x, **ctx) for x in obj]
    return obj

