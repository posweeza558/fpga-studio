# -*- coding: utf-8 -*-
"""
Lime Night IDE Theme Palette & Typography Configuration
"""

# ==============================================================================
# "LIME NIGHT" PALETTE  (graphite IDE surfaces + single lime accent)
# Names are kept from the previous theme so every module keeps importing them.
# ==============================================================================
BG_BLACK      = "#0E0E10"   # Outer window shell & gaps between cards
BG_DARK       = "#161618"   # Generic dark surface alias
BG_TITLEBAR   = "#0E0E10"   # Menu / title bar
BG_ACTIVITY   = "#161618"   # Left icon rail card
BG_SIDEBAR    = "#161618"   # Explorer / Search card
BG_EDITOR     = "#121214"   # Code editor & machine-code card (darkest work surface)
BG_TAB_BAR    = "#161618"   # Card header / tab strip
BG_ELEVATED   = "#202024"   # Search pill, inputs, elevated rows
BG_CARD       = "#202024"   # Alias for elevated card container
BG_PILL_INACT = "#1E1E22"   # Inactive pill / secondary button
BG_PILL_ACT   = "#2C2C33"   # Active tab pill (graphite, white text)
BG_PANEL      = "#161618"   # Bottom board panel / right overview card
BG_HOVER      = "#2A2A30"   # Hover state surface
BG_SELECTION  = "#2E3A12"   # Lime-tinted text selection
BG_POPUP      = "#1E1E22"   # Popup menu surface

BORDER_COLOR  = "#26262C"   # Subtle inner divider
BORDER_HOVER  = "#44444C"   # Hover outline
ACCENT_GREEN  = "#C8F031"   # Primary accent (lime) -- kept name for compatibility
ACCENT_HOVER  = "#D8FF52"   # Hover fill for lime buttons
ACCENT_YELLOW = "#FFD43B"   # Warning / missing extension dot
ACCENT_WARN   = "#FFD43B"   # Alias for warning yellow
ACCENT_AMBER  = "#F59E0B"   # Pause / running amber
ACCENT_RED    = "#FF5A5F"   # Error indicator red
ACCENT_CYAN   = "#5FB4FF"   # Open-source toolchain blue
ACCENT_PURPLE = "#B392FF"   # Cloud synthesis purple

TXT_BRIGHT    = "#F4F4F5"   # Primary white
TXT_PRIMARY   = "#E4E4E7"   # Body text
TXT_MUTED     = "#9A9AA3"   # Secondary gray (menus, labels)
TXT_DIM       = "#5C5C66"   # Line numbers / hints
TXT_ON_WHITE  = "#0E0E10"   # Dark text on the lime accent
TXT_ON_PILL   = "#F4F4F5"   # Text on the active (graphite) tab pill

# ==============================================================================
# SYNTAX HIGHLIGHTING PALETTE (blue keywords, lime identifiers, as in the concept)
# ==============================================================================
SYN_KEYWORD   = "#6CB6FF"   # Keywords (int, while, return) -- blue
SYN_TYPE      = "#E3F26B"   # Types -- pale lime
SYN_MACRO     = "#C39BFF"   # #define / preprocessor -- violet
SYN_FUNC      = "#D4F04A"   # Function names -- lime
SYN_MMIO      = "#FFB86B"   # MMIO registers -- orange
SYN_STRING    = "#F2E28C"   # Strings -- soft yellow
SYN_NUMBER    = "#9ADFFF"   # Numbers -- light cyan
SYN_COMMENT   = "#6E6E78"   # Comments -- quiet gray

# ==============================================================================
# TYPOGRAPHY (MICROSOFT CLEARTYPE HINTED THAI + ENGLISH FONTS)
# ==============================================================================
FONT_UI       = "Leelawadee UI"
FONT_CODE     = "Cascadia Code SemiBold"
FONT_ICON     = "Segoe Fluent Icons"
