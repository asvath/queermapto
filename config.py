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
    "Residential": ("building", "darkgreen"),
    "Bar": ("beer", "lightred"),
    "BathHouse": ("tint", "blue"),
    "Church": ("plus", "cadetblue"),
    "Club": ("music", "darkred"),
    "Community Centre": ("home", "orange"),
    "Cultural": ("university", "darkpurple"),
    "Gym/Sports": ("bolt", "lightgreen"),
    "Health": ("medkit", "red"),
    "Memorial": ("flag", "lightgray"),
    "Open Space": ("tree", "green"),
    "Other": ("info", "gray"),
    "Public Art": ("paint-brush", "purple"),
    "Restaurant": ("cutlery", "pink"),
    "Retail": ("shopping-cart", "darkblue"),
    "Shelter": ("bed", "beige"),
}
ICON_CLOSED = ("times", "black")              # black X for closed/historical