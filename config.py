# config.py — Configurações globais do Legis
APP_NAME = "Legis"
APP_SUBTITLE = "Sistema de Gestão Jurídica"
APP_VERSION = "Beta"
UPDATE_URL = "https://raw.githubusercontent.com/legis-app/releases/main/version.json"

# Paleta CLARA — verde/cinza jurídico (padrão)
THEME_LIGHT = {
    "bg_main":         "#F5F6F5",
    "bg_sidebar":      "#1C2B1E",
    "bg_sidebar_hover":"#2E4A32",
    "bg_active":       "#3A6B40",
    "accent":          "#3A6B40",
    "accent_hover":    "#2E5433",
    "accent_light":    "#EAF2EB",
    "white":           "#FFFFFF",
    "border":          "#D6DDD7",
    "text_primary":    "#1A2B1C",
    "text_secondary":  "#5A6B5C",
    "text_muted":      "#8A9B8C",
    "sidebar_text":    "#B8CCB9",
    "sidebar_active":  "#FFFFFF",
    "danger":          "#C0392B",
    "danger_light":    "#FDEDEC",
    "warning":         "#D4A017",
    "warning_light":   "#FEF9E7",
    "success":         "#27AE60",
    "success_light":   "#EAFAF1",
    "blue":            "#2563EB",
    "card_bg":         "#FFFFFF",
    "table_alt":       "#F8FAF8",
    "header_bg":       "#F0F5F0",
}

# Paleta ESCURA
THEME_DARK = {
    "bg_main":         "#0F1410",
    "bg_sidebar":      "#0A0F0B",
    "bg_sidebar_hover":"#1A2E1C",
    "bg_active":       "#2E5433",
    "accent":          "#4A8B52",
    "accent_hover":    "#3A6B40",
    "accent_light":    "#1A2E1C",
    "white":           "#1E2820",
    "border":          "#2A3D2C",
    "text_primary":    "#E8F0E9",
    "text_secondary":  "#8FAF91",
    "text_muted":      "#5A7A5C",
    "sidebar_text":    "#6A8A6C",
    "sidebar_active":  "#FFFFFF",
    "danger":          "#E05445",
    "danger_light":    "#2A1512",
    "warning":         "#E0B830",
    "warning_light":   "#2A2010",
    "success":         "#3ABF6A",
    "success_light":   "#0F2015",
    "blue":            "#4A8FE0",
    "card_bg":         "#1A2210",
    "table_alt":       "#162018",
    "header_bg":       "#1A2810",
}

# Cores de acento disponíveis para personalização
ACCENT_PRESETS = {
    "Verde Jurídico": {"accent": "#3A6B40", "accent_hover": "#2E5433", "accent_light": "#EAF2EB", "bg_active": "#3A6B40"},
    "Azul Corporativo": {"accent": "#1E4D8C", "accent_hover": "#163A6B", "accent_light": "#E8F0FB", "bg_active": "#1E4D8C"},
    "Dourado Premium": {"accent": "#8B6914", "accent_hover": "#6B5010", "accent_light": "#FBF5E6", "bg_active": "#8B6914"},
    "Vinho Clássico": {"accent": "#6B1A2A", "accent_hover": "#501320", "accent_light": "#F9EAEC", "bg_active": "#6B1A2A"},
    "Cinza Titanium": {"accent": "#3A4A5A", "accent_hover": "#2A3A4A", "accent_light": "#EAF0F5", "bg_active": "#3A4A5A"},
}

# Tema ativo (modificável em runtime)
COLORS = dict(THEME_LIGHT)
CURRENT_THEME = "light"
CURRENT_ACCENT = "Verde Jurídico"

AREAS_DIREITO = [
    "Direito Penal", "Direito Civil", "Direito Constitucional",
    "Direito Administrativo", "Direito Trabalhista", "Direito Tributário",
    "Direito do Consumidor", "Direito Previdenciário", "Direito Empresarial",
    "Direito de Família", "Direito Ambiental", "Direito Militar",
]

TRIBUNAIS = [
    ("TJSP — Tribunal de Justiça de São Paulo",     "api_publica_tjsp"),
    ("TJRJ — Tribunal de Justiça do Rio de Janeiro","api_publica_tjrj"),
    ("TJMG — Tribunal de Justiça de Minas Gerais",  "api_publica_tjmg"),
    ("TJPR — Tribunal de Justiça do Paraná",        "api_publica_tjpr"),
    ("TJRS — Tribunal de Justiça do Rio Grande do Sul","api_publica_tjrs"),
    ("TRF1 — Tribunal Regional Federal 1ª Região",  "api_publica_trf1"),
    ("TRF3 — Tribunal Regional Federal 3ª Região",  "api_publica_trf3"),
    ("TRT2 — Tribunal Regional do Trabalho SP",     "api_publica_trt2"),
    ("STJ — Superior Tribunal de Justiça",          "api_publica_stj"),
    ("STF — Supremo Tribunal Federal",              "api_publica_stf"),
]

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

MESES = [
    "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
    "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"
]
