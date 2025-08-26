import re
import pandas as pd

from config import DESC_COL, TYPE_COL, SPACE_COL

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
    if "retail" in type_of_space:
        cat = "Retail"
    elif "public art" in type_of_space:
        cat = "Public Art"
    elif "cultural" in type_of_space:
        cat = "Cultural"
    elif "bathhouse" in type_of_space:
        cat = "BathHouse"
    elif "cruising spot" in type_of_space:
        cat = "Open Space"
    elif "open space" in type_of_space:
        cat = "Open Space"
    elif any(k in type_of_space.lower() for k in ["bar", "restaurant", "club"]):
        # Restaurant / Bar / Club into separate categories
        if re.search(r"\b(restaurant|eatery|bistro|diner|trattoria|osteria|taqueria)\b", text, re.I):
            cat = "Restaurant"
        elif re.search(r"\b(bar|pub|tavern)\b", text, re.I):
            cat = "Bar"
        elif re.search(r"\b(club|lounge|night\s*club|nightclub|discotheque|disco)\b", text, re.I):
            cat = "Club"
        else:
            cat = "Bar"
    else:
        cat = "Other"

    # Only apply these when labels is too generic
    if cat in ("Other", "Open Space"):
        # Church (only if in the NAME, not general text; avoid Church Street/Wellesley)
        if (re.search(r"\b(church|cathedral|chapel|parish)\b", name, re.I)
                and not re.search(r"church\s*(street|st\.?)|\bchurch-wellesley\b", name, re.I)):
            cat = "Church"
        # Shelter
        elif re.search(r"\b(shelter|drop[-\s]*in|refuge|homeless|safe\s*house)\b", text, re.I):
            cat = "Shelter"

        # Memorial (only if in the NAME, not general text)
        elif re.search(r"\b(memorial)\b", name, re.I):
            cat = "Memorial"

        # Apartment / Residential
        elif re.search(r"\b(apartment|residential|condo|residence|housing|tenement|tower)\b", text, re.I):
            cat = "Residential"

        # Community Centre
        elif re.search(
                r"\b(the 519|community\s+centre|community\s+center|resource\s+centre|resource\s+center"
                r"|youth\s+service|youth\s+centre|youth\s+center|safe[-\s]*space)\b",
                text, re.I):
            cat = "Community Centre"

        # Health
        elif re.search(r"\b(clinic|hospital|aids|hiv|health|sexual\s*health|casey house|wellness|testing)\b",
                       text, re.I):
            cat = "Health"



        # Gym / Sports
        elif re.search(
                r"\b(gym|fitness|workout|yoga|dojo|martial\s*arts|boxing|crossfit|athletic|sports\s*centre|arena|stadium|court|rink|fieldhouse)\b",
                text, re.I):
            cat = "Gym/Sports"


    # beaches/parks/squares
    if any(k in text for k in ["beach", "park", "trail", "square", "plaza", "field"]):
        if cat in ["Other", "Cultural", "Retail"]:
            cat = "Open Space"

    return cat