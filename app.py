import streamlit as st
import folium
from branca.element import MacroElement, Template, Element
from streamlit_folium import st_folium

from utils import read_csv, parse_latlon, normalize_type, IconLegend
from config import (
    DATA_FILEPATH, COORDS_COL, STATUS_COL, DESC_COL, SPACE_COL,
    ICON_MAP_ACTIVE, ICON_CLOSED, LEGEND_HTML
)

st.set_page_config(page_title="Queer Toronto Map", layout="wide")
st.markdown(
    """
    <h1 style="display:flex; align-items:center; gap:12px;">
          <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Flag_of_Canada_%28Pantone%29.svg/320px-Flag_of_Canada_%28Pantone%29.svg.png" 
           alt="Canadian Flag" width="40">
      <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Gay_Pride_Flag.svg/240px-Gay_Pride_Flag.svg.png" 
           alt="Pride Flag" width="40">
      Map of Queer Spaces in Toronto
    </h1>
    """,
    unsafe_allow_html=True,
)

st.caption("Explore Toronto’s queer history and community with this interactive map of active and historical spaces.")
# ---------------------------
# Load & clean
# ---------------------------
df = read_csv(DATA_FILEPATH)

# coords
df["lat"], df["lon"] = zip(*df[COORDS_COL].map(parse_latlon))
df = df.dropna(subset=["lat", "lon"])

# normalize status & category
df[STATUS_COL] = df[STATUS_COL].fillna("").str.strip().str.lower()
df["Category"] = df.apply(normalize_type, axis=1)

show_active = True        # always show active
show_closed = False       # don't show closed by default
present_types = sorted(df["Category"].unique().tolist())
sel_types = present_types # include all categories
mask_types = df["Category"].isin(sel_types)

# filtered frames
dfa = df[mask_types & (df[STATUS_COL] == "active")].copy() if show_active else df.iloc[0:0].copy()
# closed always added so map toggle works
dfc = df[mask_types & (df[STATUS_COL] != "active")].copy()

# ---------------------------
# Build map
# ---------------------------
TORONTO = (43.6532, -79.3832)
m = folium.Map(location=TORONTO, zoom_start=12, tiles=None, control_scale=True)
leaflet_css = """
<style>
/* keep tiles low; popups highest (inside the map iframe) */
.leaflet-tile-pane   { z-index: 200 !important; }
.leaflet-overlay-pane{ z-index: 400 !important; }
.leaflet-marker-pane { z-index: 600 !important; }
.leaflet-tooltip-pane{ z-index: 12000 !important; }
.leaflet-popup-pane  { z-index: 13000 !important; }
/* prevent clipping inside the iframe */
.leaflet-container   { overflow: visible !important; }
</style>
"""
m.get_root().header.add_child(Element(leaflet_css))
folium.TileLayer("CartoDB positron", control=False).add_to(m)  # hidden from LayerControl

# Active groups by type
groups_active = {}
def get_group(label):
    if label not in groups_active:
        groups_active[label] = folium.FeatureGroup(name=f"{label} (Active)", show=True)
        groups_active[label].add_to(m)
    return groups_active[label]

# Closed layer (initial visibility = checkbox)
group_closed = folium.FeatureGroup(name="Closed (Historical)", show=show_closed)
group_closed.add_to(m)

# Active markers
for _, row in dfa.iterrows():
    name = str(row[SPACE_COL]).strip()
    desc = str(row.get(DESC_COL, "")).strip()
    typ  = str(row.get("Category", "Other")).strip()
    lat, lon = row["lat"], row["lon"]
    icon_name, color = ICON_MAP_ACTIVE.get(typ, ("info", "gray"))
    gmaps = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
    popup_html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 13px; line-height: 1.35; max-width: 280px;">
      <div style="font-weight: 700; margin-bottom: 4px;">{name}</div>
      <div style="opacity:0.8; margin-bottom: 6px;"><i>{typ}</i></div>
      <div style="margin-bottom: 8px;">{desc if desc else "No description available."}</div>
      <a href="{gmaps}" target="_blank" rel="noopener noreferrer">
      <i class="fa fa-compass"></i> Directions</a>
    </div>
    """
    grp = get_group(typ)
    folium.Marker(
        location=(lat, lon),
        tooltip=f"{name} ({typ})",
        popup=folium.Popup(popup_html, max_width=320),
        icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
    ).add_to(grp)

# Closed markers (black X)
for _, row in dfc.iterrows():
    name = str(row[SPACE_COL]).strip()
    desc = str(row.get(DESC_COL, "")).strip()
    lat, lon = row["lat"], row["lon"]
    popup_html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 13px; line-height: 1.35; max-width: 280px;">
      <div style="font-weight: 700; margin-bottom: 4px;">{name}</div>
      <div style="opacity:0.8; margin-bottom: 6px;"><i>Closed / Historical</i></div>
      <div>{desc if desc else "No description available."}</div>
    </div>
    """
    folium.Marker(
        location=(lat, lon),
        tooltip=f"{name} (Closed)",
        popup=folium.Popup(popup_html, max_width=320),
        icon=folium.Icon(color=ICON_CLOSED[1], icon=ICON_CLOSED[0], prefix="fa"),
    ).add_to(group_closed)

# controls + legend
folium.LayerControl(collapsed=False).add_to(m)

legend_rows = []
for t in sorted(dfa["Category"].dropna().unique().tolist()):
    icon, color = ICON_MAP_ACTIVE.get(t, ("info", "gray"))
    legend_rows.append((t, icon, color))
legend_rows.append(("Closed (Historical)", ICON_CLOSED[0], ICON_CLOSED[1]))
IconLegend(legend_rows, LEGEND_HTML).add_to(m)

# footer spacer + credits (collapsed by default)
m.get_root().html.add_child(Element('<div style="height:44px;"></div>'))
footer_tpl = Template("""
{% macro html(this, kwargs) %}
<div id="credits-box" style="
     position: fixed; bottom: 0; left: 0; width: 100%;
     background: rgba(255,255,255,0.94);
     font-size: 12px; font-family: Arial, sans-serif; line-height: 1.45;
     box-shadow: 0 -1px 6px rgba(0,0,0,0.18); z-index: 999999;">
  <div id="credits-header" style="padding:8px 16px; cursor:pointer; font-weight:700;"
       onclick="var c=document.getElementById('credits-content');
                var h=document.getElementById('credits-header');
                if(c.style.display==='none'){c.style.display='block'; h.innerHTML='Acknowledgment & Credits ▲';}
                else{c.style.display='none'; h.innerHTML='Acknowledgment & Credits ▼';}">
    Acknowledgment & Credits ▼
  </div>
  <div id="credits-content" style="display:none; padding:0 16px 12px 16px;">
    <div style="margin-bottom:10px;">
      QueerMapTO builds on the 
      <a href="https://torontosocietyofarchitects.ca/toronto-queer-spaces/" target="_blank" rel="noopener noreferrer">
        <b>Queer Spaces database</b>
      </a> created by the volunteers of the Toronto Society of Architects (TSA).
    </div>
    <div style="margin-bottom:10px;">
      The TSA database was made possible thanks to the efforts of countless individuals including
      Janice M., Kurtis C., Joël L., Amanda E., Cherisse T., Eric W., Kate R., Rebecca P., Ryan F.,
      Samantha B., Simon L., and Spencer L.
    </div>
    <div style="margin-bottom:10px;">
      It also incorporates contributions from members of the community, including the over one
      thousand individuals who added their memories to the 2024 Pride Street Fair map and the
      class at the University of Waterloo School of Architecture, who helped to digitize these
      memories.
    </div>
    <div style="margin-bottom:10px;">
      References and source materials are credited in the TSA database. 
      Please see the TSA site for the full bibliography.
    </div>
  </div>
</div>
{% endmacro %}
""")

class Footer(MacroElement):
    def __init__(self):
        super().__init__()
        self._template = footer_tpl

# optional tiny spacer inside the map iframe so controls don't sit under the footer
m.get_root().html.add_child(Element('<div style="height:44px;"></div>'))

# add the footer macro to the map root
m.get_root().add_child(Footer())

# render
st_folium(m, height=720, width=None)