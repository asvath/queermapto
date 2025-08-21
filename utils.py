import re
import pandas as pd
import folium
from branca.element import MacroElement
from jinja2 import Template

from config import DESC_COL, TYPE_COL, SPACE_COL,LEGEND_HTML

class IconLegend(MacroElement):
    """Custom Folium MacroElement to render a legend of icons/colors."""
    def __init__(self, items, legend_html: str = LEGEND_HTML):
        super().__init__()
        self._name = 'IconLegend'
        self.template = Template(legend_html)
        self.items = items

    def render(self, **kwargs):
        figure = self.get_root()
        macro = self.template.module.html
        figure.header.add_child(folium.Element(macro(self, {})), name='icon-legend')


def read_csv(filepath: str) -> pd.DataFrame:
    """
     Reads csv as pandas DataFrame.
    :param filepath: Path to csv
    :return: pd.DataFrame
    """

    return pd.read_csv(filepath)

def parse_latlon(coord) -> tuple[None, None] | tuple[float, float]:
    """Parse latitude/longitude from a string into floats, or (None, None) if invalid.
    :param coord: coord from pd.DataFrame
    """
    if coord is None:
        return None, None

    coord = str(coord).strip()
    # replace commas with spaces to support "43.65,-79.38"
    coord= coord.replace(",", " ")
    coord = coord.split()
    if len(coord) >= 2:
        try:
            return float(coord[0]), float(coord[1])
        except ValueError:
            return None, None
    return None, None

def normalize_type(row:pd.Series) -> str:
    """Normalize raw type/name/description into a canonical category by:
    - Mapping cruising spot to open spaces
    - Creating Health, Community Center, and Church (place of worship not church st.) categories
    - Ambigious outdoor locations mapped to open space
    :param: row of pd.DataFrame
    :return One canonical category. Possible outputs:
            ["Bar/Club/Restaurant", "Bathhouse", "Retail", "Public Art",
             "Cultural", "Open Space", "Other",
             "Health", "Community Centre", "Church"]

    """
    type_of_space = str(row.get(TYPE_COL, "")).lower()
    name = str(row.get(SPACE_COL, "")).lower()
    desc = str(row.get(DESC_COL, "")).lower()
    text = f"{name} {desc}"

    # start from type_of_space label
    if any(s in type_of_space for s in ["bar", "club", "restaurant"]):
        cat = "Bar/Club/Restaurant"
    elif any(k in type_of_space for k in ["bath","bathhouse"]):
        cat = "Bathhouse"
    elif "retail" in type_of_space:
        cat = "Retail"
    elif "public art" in type_of_space:
        cat = "Public Art"
    elif "cultural" in type_of_space:
        cat = "Cultural"
    elif "cruising spot" in type_of_space:
        cat = "Open Space"
    elif "open space" in type_of_space:
        cat = "Open Space"
    else:
        cat = "Other"

    # overrides via name/description
    if re.search(r"\b(clinic|hospital|aids|hiv|sexual\s*health|casey house|wellness|testing)\b", text, re.I):
        cat = "Health"

    if re.search(r"\b(the 519|community\s+centre|community\s+center|resource\s+centre|resource\s+center)\b", text, re.I):
        cat = "Community Centre"

    # avoid Church Street false positives
    if (re.search(r"\b(church|cathedral|chapel|parish)\b", text, re.I)
            and not re.search(r"church\s*(street|st\.?)|\bchurch-wellesley\b", text, re.I)):
        cat = "Church"

    # beaches/parks/squares
    if any(k in text for k in ["beach", "park", "trail", "square", "plaza", "field"]):
        if cat in ["Other", "Cultural", "Retail"]:
            cat = "Open Space"

    return cat