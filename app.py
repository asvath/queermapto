import folium
import streamlit as st
from branca.element import Element
from streamlit_folium import st_folium

from config import (
    DATA_FILEPATH, COORDS_COL, STATUS_COL, DESC_COL, SPACE_COL,
    ICON_MAP_ACTIVE, ICON_CLOSED
)
from utils import read_csv, parse_latlon, normalize_type

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

st.caption(
    "Explore Toronto’s queer history and community with this interactive map of active and historical spaces.\n\n"
    "**Acknowledgment & Credits** — QueerMapTO builds on the "
    "[**Queer Spaces Database**](https://torontosocietyofarchitects.ca/toronto-queer-spaces/) "
    "created by volunteers of the Toronto Society of Architects (TSA). It also incorporates contributions "
    "from community members (including those who added memories to the 2024 Pride Street Fair map) and the "
    "University of Waterloo School of Architecture class. References and source materials are credited in "
    "TSA's Queer Spaces Database."
)

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
# Center on Nathan Phillips
NATHAN_PHILLIPS = (43.6526, -79.3832)
m = folium.Map(location=NATHAN_PHILLIPS, zoom_start=13, tiles=None, control_scale=True)

# CSS inside Folium iframe
m.get_root().html.add_child(Element("""
<style>
.leaflet-tile-pane    { z-index: 200 !important; }
.leaflet-overlay-pane { z-index: 400 !important; }
.leaflet-marker-pane  { z-index: 600 !important; }
.leaflet-tooltip-pane { z-index: 12000 !important; }
.leaflet-popup-pane   { z-index: 13000 !important; }
.leaflet-top, .leaflet-bottom, .leaflet-control-container, .leaflet-control, .leaflet-control-layers {
  z-index: 500 !important;
}
.leaflet-container { overflow: visible !important; }
</style>
"""))

# Basemap
folium.TileLayer("CartoDB positron", control=False).add_to(m)

# --- Layers: Closed FIRST so it stays at the TOP ---
group_closed = folium.FeatureGroup(name="Closed (Historical)", show=show_closed)
group_closed.add_to(m)

# --- Active groups: pre-create in alphabetical order ---
groups_active = {}
for t in sorted(dfa["Category"].dropna().unique().tolist()):
    fg = folium.FeatureGroup(name=f"{t} (Active)", show=True)
    fg.add_to(m)
    groups_active[t] = fg

# Ensure an 'Other' group exists if needed later
if "Other" not in groups_active:
    fg_other = folium.FeatureGroup(name="Other (Active)", show=True)
    fg_other.add_to(m)
    groups_active["Other"] = fg_other

# --- Active markers ---
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
        <i class="fa fa-compass"></i> Directions
      </a>
    </div>
    """

    grp = groups_active.get(typ, groups_active["Other"])
    folium.Marker(
        location=(lat, lon),
        tooltip=f"{name} ({typ})",
        popup=folium.Popup(popup_html, max_width=320),
        icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
        z_index_offset=650,
    ).add_to(grp)

# --- Closed markers (black = Closed) ---
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
        z_index_offset=650,
    ).add_to(group_closed)

# --- Controls + legend (Closed first, then alphabetical) ---
folium.LayerControl(collapsed=False, position="bottomleft").add_to(m)

# --- Render ---
st_folium(m, height=720, width=None)