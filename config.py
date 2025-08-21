import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Root of project

# Paths relative to the project root
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILEPATH = os.path.join(DATA_DIR, "queer_toronto_spaces.csv")

DESC_COL   = "Short Description / History"
TYPE_COL   = "Type of Space"
STATUS_COL = "Active, closed or moved?"
SPACE_COL  = "Space"
COORDS_COL = "Coordinates"

# Font Awesome 4.7 icon names + folium colors
ICON_MAP_ACTIVE = {
    "Bar/Club/Restaurant": ("cutlery", "pink"),
    "Bathhouse": ("tint", "blue"),
    "Open Space": ("tree", "green"),
    "Public Art": ("paint-brush", "purple"),
    "Community Centre": ("home", "orange"),
    "Church": ("plus", "cadetblue"),          # FA4 has no 'cross'; 'plus' reads like a cross
    "Retail": ("shopping-cart", "lightred"),
    "Health": ("medkit", "red"),
    "Cultural": ("university", "darkpurple"),
    "Other": ("info", "gray"),
}
ICON_CLOSED = ("times", "black")              # black X for closed/historical

LEGEND_HTML = """
{% macro html(this, kwargs) %}
<div id='map-legend' style='position: fixed; bottom: 18px; right: 18px; z-index: 9999;
     background: rgba(255,255,255,0.97); padding: 10px 12px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
     font-family: Arial, sans-serif; font-size: 12px; color: #111; min-width: 180px;'>
  <div style='font-weight: 700; margin-bottom: 6px;'>Legend</div>
  {% for label, icon, color in this.items %}
    <div style='display:flex; align-items:center; gap:8px; margin: 6px 0;'>
      <span class="fa fa-{{ icon }}" style="width: 16px; text-align:center; color: {{ color }};"></span>
      <span>{{ label }}</span>
    </div>
  {% endfor %}
</div>
<style>
#map-legend { pointer-events: none; }
#map-legend * { pointer-events: auto; }
</style>
{% endmacro %}
"""