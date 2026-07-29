import os
import re
import sqlite3
import hashlib
import hmac
import secrets as py_secrets
from datetime import date, datetime
from html import escape

import pandas as pd
import streamlit as st


DB_NAME = "tyre_business.db"
LOW_STOCK_LIMIT = 5
WALK_IN_CUSTOMER = "Walk-in Customer"
REGULAR_CUSTOMER = "Regular Customer"
PAYMENT_METHODS = ["Cash", "POS", "Bank Transfer", "Credit", "Other"]
COMMON_TYRE_SIZES = [
    "155 R12C", "165/80 R13", "185/70 R13", "185 R14C", "185/70 R14",
    "195 R14C", "195/70 R14", "185/65 R15", "195 R15C", "195/65 R15",
    "205/55 R16", "205/60 R16", "215/60 R16", "215/65 R16", "225/45 R17",
    "225/50 R17", "225/55 R17", "235/45 R18", "245/45 R18", "265/70 R16",
]
COMMON_TYRE_BRANDS = [
    "Austone", "Bridgestone", "Michelin", "Goodyear", "Dunlop", "Pirelli",
    "Continental", "Hankook", "Maxxis", "Firestone", "Yokohama", "Apollo",
    "MRF", "CEAT", "Linglong", "Triangle", "Double Coin", "Roadstone", "Westlake",
]
APP_NAME = "Tyre Stock Manager"
APP_SUBTITLE = "Stock, Sales, Payments & Outstanding Balance Tracker"
SUPPORT_EMAIL_SECRET = "SUPPORT_EMAIL"
SUPPORT_WHATSAPP_SECRET = "SUPPORT_WHATSAPP"
SUPPORT_CONTACT_NOT_CONFIGURED = "Support contact not configured yet."
DEFAULT_BUSINESS_SETTINGS = {
    "business_name": "Tyre Business",
    "business_phone": "",
    "business_address": "",
    "country": "",
    "low_stock_alert_level": LOW_STOCK_LIMIT,
    "receipt_footer": "Thank you for your business.",
}
COUNTRIES = [
    "Afghanistan",
    "Albania",
    "Algeria",
    "Andorra",
    "Angola",
    "Antigua and Barbuda",
    "Argentina",
    "Armenia",
    "Australia",
    "Austria",
    "Azerbaijan",
    "Bahamas",
    "Bahrain",
    "Bangladesh",
    "Barbados",
    "Belarus",
    "Belgium",
    "Belize",
    "Benin",
    "Bhutan",
    "Bolivia",
    "Bosnia and Herzegovina",
    "Botswana",
    "Brazil",
    "Brunei",
    "Bulgaria",
    "Burkina Faso",
    "Burundi",
    "Cabo Verde",
    "Cambodia",
    "Cameroon",
    "Canada",
    "Central African Republic",
    "Chad",
    "Chile",
    "China",
    "Colombia",
    "Comoros",
    "Congo",
    "Costa Rica",
    "Cote d'Ivoire",
    "Croatia",
    "Cuba",
    "Cyprus",
    "Czechia",
    "Democratic Republic of the Congo",
    "Denmark",
    "Djibouti",
    "Dominica",
    "Dominican Republic",
    "Ecuador",
    "Egypt",
    "El Salvador",
    "Equatorial Guinea",
    "Eritrea",
    "Estonia",
    "Eswatini",
    "Ethiopia",
    "Fiji",
    "Finland",
    "France",
    "Gabon",
    "Gambia",
    "Georgia",
    "Germany",
    "Ghana",
    "Greece",
    "Grenada",
    "Guatemala",
    "Guinea",
    "Guinea-Bissau",
    "Guyana",
    "Haiti",
    "Honduras",
    "Hungary",
    "Iceland",
    "India",
    "Indonesia",
    "Iran",
    "Iraq",
    "Ireland",
    "Israel",
    "Italy",
    "Jamaica",
    "Japan",
    "Jordan",
    "Kazakhstan",
    "Kenya",
    "Kiribati",
    "Kuwait",
    "Kyrgyzstan",
    "Laos",
    "Latvia",
    "Lebanon",
    "Lesotho",
    "Liberia",
    "Libya",
    "Liechtenstein",
    "Lithuania",
    "Luxembourg",
    "Madagascar",
    "Malawi",
    "Malaysia",
    "Maldives",
    "Mali",
    "Malta",
    "Marshall Islands",
    "Mauritania",
    "Mauritius",
    "Mexico",
    "Micronesia",
    "Moldova",
    "Monaco",
    "Mongolia",
    "Montenegro",
    "Morocco",
    "Mozambique",
    "Myanmar",
    "Namibia",
    "Nauru",
    "Nepal",
    "Netherlands",
    "New Zealand",
    "Nicaragua",
    "Niger",
    "Nigeria",
    "North Korea",
    "North Macedonia",
    "Norway",
    "Oman",
    "Pakistan",
    "Palau",
    "Palestine",
    "Panama",
    "Papua New Guinea",
    "Paraguay",
    "Peru",
    "Philippines",
    "Poland",
    "Portugal",
    "Qatar",
    "Romania",
    "Russia",
    "Rwanda",
    "Saint Kitts and Nevis",
    "Saint Lucia",
    "Saint Vincent and the Grenadines",
    "Samoa",
    "San Marino",
    "Sao Tome and Principe",
    "Saudi Arabia",
    "Senegal",
    "Serbia",
    "Seychelles",
    "Sierra Leone",
    "Singapore",
    "Slovakia",
    "Slovenia",
    "Solomon Islands",
    "Somalia",
    "South Africa",
    "South Korea",
    "South Sudan",
    "Spain",
    "Sri Lanka",
    "Sudan",
    "Suriname",
    "Sweden",
    "Switzerland",
    "Syria",
    "Taiwan",
    "Tajikistan",
    "Tanzania",
    "Thailand",
    "Timor-Leste",
    "Togo",
    "Tonga",
    "Trinidad and Tobago",
    "Tunisia",
    "Turkey",
    "Turkmenistan",
    "Tuvalu",
    "Uganda",
    "Ukraine",
    "United Arab Emirates",
    "United Kingdom",
    "United States",
    "Uruguay",
    "Uzbekistan",
    "Vanuatu",
    "Vatican City",
    "Venezuela",
    "Vietnam",
    "Yemen",
    "Zambia",
    "Zimbabwe",
]
PAGE_NAV_ITEMS = {
    "📊 Dashboard": "Dashboard",
    "➕ Add Stock": "Add Stock",
    "📦 View Stock": "View Stock",
    "⚠️ Low Stock Items": "Low Stock Items",
    "🔎 Search Tyres": "Search Tyres",
    "🧾 Record Sale": "Record Sale",
    "⚠️ Outstanding Balances": "Outstanding Balances",
    "📈 Sales Report": "Sales Report",
    "⚙️ Business Settings": "Business Settings",
}
PAGE_NAV_ITEMS.update(
    {
        "Help / How to Use": "Help / How to Use",
        "Terms of Use": "Terms of Use",
        "Privacy Policy": "Privacy Policy",
    }
)
OWNER_NAV_ITEMS = {
    "📊 Platform Dashboard": "Platform Dashboard",
    "🏢 Businesses": "Businesses",
}


def inject_app_styles():
    st.markdown(
        """
        <style>
        :root {
            --deep-green: #0f3d2e;
            --green: #176247;
            --green-bright: #238461;
            --charcoal: #17211d;
            --cream: #fbfaf4;
            --soft-grey: #edf1ee;
            --mid-grey: #66756f;
            --gold: #c69c3d;
            --gold-soft: #f5ead0;
            --danger: #b42318;
            --surface: #ffffff;
            --border: #dfe6e1;
        }

        .stApp {
            background:
                radial-gradient(circle at 92% 2%, rgba(198, 156, 61, 0.09), transparent 24rem),
                linear-gradient(180deg, #fbfaf4 0%, #f3f6f2 52%, #ffffff 100%);
            color: var(--charcoal);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f3d2e 0%, #13251f 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 14px 0 38px rgba(15, 61, 46, 0.11);
        }

        [data-testid="stSidebar"] > div:first-child {
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: rgba(255,255,255,.25) transparent;
        }

        [data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,.14);
            margin: 1.25rem 0;
        }

        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.09);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
        }

        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stSelectbox p,
        [data-testid="stSidebar"] .stCaptionContainer,
        [data-testid="stSidebar"] .stCaptionContainer p,
        [data-testid="stSidebar"] .sidebar-brand,
        [data-testid="stSidebar"] .sidebar-brand * {
            color: #f8fbf7 !important;
        }

        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(255, 255, 255, 0.08);
            color: #ffffff;
        }

        .block-container {
            padding-top: 2.15rem;
            padding-bottom: 3rem;
            max-width: 1320px;
        }

        h1, h2, h3 {
            letter-spacing: 0;
            color: var(--charcoal);
        }

        .stApp label,
        .stApp label p,
        .stApp label span,
        .stApp [data-testid="stWidgetLabel"],
        .stApp [data-testid="stWidgetLabel"] *,
        .stApp [data-testid="stRadio"] label,
        .stApp [data-testid="stRadio"] label *,
        .stApp [role="radiogroup"] label,
        .stApp [role="radiogroup"] label *,
        .stApp [data-baseweb="radio"] *,
        .stApp [data-testid="stTextInput"] label,
        .stApp [data-testid="stDateInput"] label,
        .stApp [data-testid="stSelectbox"] label,
        .stApp [data-testid="stNumberInput"] label,
        .stApp [data-testid="stTextArea"] label,
        .stApp [data-testid="stCheckbox"] label,
        .stApp [data-testid="stCaptionContainer"],
        .stApp [data-testid="stCaptionContainer"] *,
        .stApp [data-testid="stExpander"] label,
        .stApp [data-testid="stExpander"] p {
            color: #1f2933 !important;
        }

        .stApp input,
        .stApp textarea,
        .stApp div[data-baseweb="select"] span,
        .stApp [data-testid="stDataFrame"],
        .stApp [data-testid="stDataFrame"] * {
            color: #1f2933 !important;
        }

        .stApp input,
        .stApp textarea,
        .stApp [data-baseweb="input"],
        .stApp [data-baseweb="textarea"],
        .stApp [data-baseweb="select"] > div,
        .stApp [data-baseweb="select"] div,
        .stApp [data-testid="stTextInput"] div[data-baseweb="input"],
        .stApp [data-testid="stNumberInput"] div[data-baseweb="input"],
        .stApp [data-testid="stDateInput"] div[data-baseweb="input"],
        .stApp [data-testid="stTextArea"] textarea,
        .stApp [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: #1f2933 !important;
            border-color: #d1d5db !important;
        }

        .stApp input,
        .stApp textarea {
            caret-color: #0f3d2e !important;
        }

        .stApp [data-baseweb="input"],
        .stApp [data-baseweb="textarea"],
        .stApp [data-baseweb="select"] > div {
            border: 1px solid #d1d5db !important;
            border-radius: 12px !important;
            box-shadow: none !important;
        }

        .stApp [data-baseweb="input"]:focus-within,
        .stApp [data-baseweb="textarea"]:focus-within,
        .stApp [data-baseweb="select"]:focus-within > div {
            border-color: #0f3d2e !important;
            box-shadow: 0 0 0 2px rgba(15, 61, 46, 0.14) !important;
        }

        .stApp [data-baseweb="select"] svg,
        .stApp [data-baseweb="input"] svg {
            color: #1f2933 !important;
            fill: #1f2933 !important;
        }

        .stApp input::placeholder,
        .stApp textarea::placeholder,
        .stApp [data-baseweb="input"] input::placeholder {
            color: #6b7280 !important;
            opacity: 1;
        }

        .visible-widget-label {
            color: #1f2933 !important;
            font-weight: 700;
            font-size: 0.95rem;
            margin: 0.35rem 0 0.2rem 0;
        }

        .visible-helper-text {
            color: #52615b !important;
            font-size: 0.9rem;
        }

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] label p,
        [data-testid="stSidebar"] label span,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
        [data-testid="stSidebar"] div[data-baseweb="select"] span,
        [data-testid="stSidebar"] .stCaptionContainer,
        [data-testid="stSidebar"] .stCaptionContainer *,
        [data-testid="stSidebar"] .sidebar-brand,
        [data-testid="stSidebar"] .sidebar-brand * {
            color: #f8fbf7 !important;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-baseweb="select"] div {
            background-color: rgba(255, 255, 255, 0.09) !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] span,
        [data-testid="stSidebar"] [data-baseweb="select"] svg {
            color: #f8fbf7 !important;
            fill: #f8fbf7 !important;
        }

        div[data-testid="stForm"], div[data-testid="stExpander"] {
            border: 1px solid var(--border);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.94);
            box-shadow: 0 12px 32px rgba(15, 61, 46, 0.07);
            padding: .35rem .55rem;
        }

        .app-hero {
            position: relative;
            overflow: hidden;
            border-radius: 24px;
            padding: 2rem 2.15rem;
            margin-bottom: 1.65rem;
            background: linear-gradient(132deg, #0b3024 0%, #176247 68%, #88702e 155%);
            color: #ffffff;
            box-shadow: 0 22px 55px rgba(15, 61, 46, 0.21);
            border: 1px solid rgba(255,255,255,.12);
        }

        .app-hero::after {
            content: "";
            position: absolute;
            width: 280px;
            height: 280px;
            right: -75px;
            top: -145px;
            border-radius: 50%;
            border: 42px solid rgba(255,255,255,.07);
        }

        .app-hero h1 {
            color: #ffffff;
            font-size: clamp(1.8rem, 3vw, 2.45rem);
            margin: 0 0 0.45rem 0;
            line-height: 1.15;
            font-weight: 850;
        }

        .app-hero p {
            color: rgba(255, 255, 255, 0.86);
            margin: 0;
            font-size: 1rem;
        }

        .sidebar-brand {
            padding: 1rem 0.2rem 1.25rem 0.2rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.16);
            margin-bottom: 1.15rem;
        }

        .sidebar-brand .title {
            font-size: 1.14rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.3;
        }

        .sidebar-brand .subtitle {
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.68);
            margin-top: 0.2rem;
            line-height: 1.35;
        }

        .section-title {
            margin: 1.65rem 0 0.75rem 0;
            padding-left: .85rem;
            border-left: 4px solid var(--gold);
        }

        .section-title h2 {
            font-size: 1.15rem;
            margin: 0;
        }

        .section-title p {
            margin: 0.15rem 0 0 0;
            color: var(--mid-grey);
            font-size: 0.9rem;
        }

        .metric-card {
            position: relative;
            overflow: hidden;
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1.2rem 1.25rem;
            min-height: 142px;
            box-shadow: 0 13px 34px rgba(15, 61, 46, 0.075);
            border-top: 4px solid var(--green);
            transition: transform .16s ease, box-shadow .16s ease;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 17px 38px rgba(15, 61, 46, 0.11);
        }

        .metric-icon {
            width: 38px;
            height: 38px;
            display: grid;
            place-items: center;
            border-radius: 11px;
            margin-bottom: .75rem;
            background: #e8f3ee;
            color: var(--deep-green);
            font-size: 1.1rem;
            font-weight: 900;
        }

        .metric-card.gold {
            border-top-color: var(--gold);
        }

        .metric-card.warning {
            border-top-color: var(--danger);
        }

        .metric-label {
            color: var(--mid-grey);
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .metric-value {
            margin-top: 0.35rem;
            color: var(--charcoal);
            font-size: clamp(1.35rem, 2.3vw, 1.75rem);
            font-weight: 850;
            line-height: 1.15;
            overflow-wrap: anywhere;
        }

        .metric-detail {
            color: var(--mid-grey);
            font-size: 0.82rem;
            margin-top: 0.4rem;
        }

        .preview-strip {
            border-radius: 17px;
            border: 1px solid #dfe6e1;
            background: linear-gradient(135deg, #f8faf7, #fffdf7);
            padding: 1rem 1.15rem;
            color: var(--charcoal);
            margin: 0.55rem 0 1rem 0;
            box-shadow: 0 8px 22px rgba(15,61,46,.045);
        }

        .preview-strip strong {
            color: var(--deep-green);
        }

        .stButton > button, .stFormSubmitButton > button {
            min-height: 2.75rem;
            border-radius: 12px;
            border: 1px solid #0f3d2e;
            background: linear-gradient(180deg, #176247, #0f3d2e);
            color: #ffffff;
            font-weight: 750;
            padding: .55rem 1.15rem;
            box-shadow: 0 6px 14px rgba(15,61,46,.14);
        }

        .stButton > button:hover, .stFormSubmitButton > button:hover {
            background: linear-gradient(180deg, #238461, #176247);
            color: #ffffff;
            border-color: #176247;
            transform: translateY(-1px);
        }

        [data-testid="stDownloadButton"] button {
            background: #ffffff;
            color: var(--deep-green);
            border: 1px solid #b9ccc3;
            box-shadow: none;
        }

        button[data-testid="stBaseButton-primary"] {
            background: linear-gradient(180deg, #c43b30, #9f2219);
            border-color: #8f1f17;
            box-shadow: 0 6px 14px rgba(180,35,24,.18);
        }

        button[data-testid="stBaseButton-primary"]:hover {
            background: linear-gradient(180deg, #d3483c, #b42318);
            border-color: #9f2219;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 9px 25px rgba(15,61,46,.055);
        }

        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: .45rem;
            background: #e9efeb;
            padding: .35rem;
            border-radius: 14px;
        }

        [data-testid="stTabs"] button[role="tab"] {
            border-radius: 10px;
            padding: .65rem 1.2rem;
            color: #44534d;
            font-weight: 750;
        }

        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            background: #ffffff;
            color: var(--deep-green);
            box-shadow: 0 3px 12px rgba(15,61,46,.1);
        }

        [data-testid="stAlert"] {
            border-radius: 14px;
            border-width: 1px;
        }

        @media (max-width: 700px) {
            .block-container { padding: 1rem .8rem 2rem; }
            .app-hero { padding: 1.45rem; border-radius: 19px; }
            .metric-card { min-height: 126px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_database_url():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    try:
        database_url = st.secrets.get("DATABASE_URL")
        if database_url:
            return database_url

        database_secrets = st.secrets.get("database", {})
        if hasattr(database_secrets, "get"):
            return database_secrets.get("url")
    except Exception:
        return None

    return None


def get_config_value(name):
    value = os.getenv(name)
    if value and str(value).strip():
        return str(value).strip()

    try:
        value = st.secrets.get(name)
        if value and str(value).strip():
            return str(value).strip()
    except Exception:
        return ""

    return ""


def get_support_contacts():
    return (
        get_config_value(SUPPORT_EMAIL_SECRET),
        get_config_value(SUPPORT_WHATSAPP_SECRET),
    )


def render_support_sidebar():
    support_email, support_whatsapp = get_support_contacts()
    if support_email:
        st.sidebar.caption(f"Support: {support_email}")
    if support_whatsapp:
        st.sidebar.caption(f"WhatsApp: {support_whatsapp}")
    if not support_email and not support_whatsapp:
        st.sidebar.caption(SUPPORT_CONTACT_NOT_CONFIGURED)


def get_platform_owner_credentials():
    try:
        return st.secrets.get("PLATFORM_OWNER_EMAIL"), st.secrets.get("PLATFORM_OWNER_PASSWORD")
    except Exception:
        return None, None


def normalize_email(email):
    return email.strip().lower()


def get_country_options(saved_country=""):
    options = ["Select your country"] + COUNTRIES.copy()
    clean_country = (saved_country or "").strip()
    if clean_country and clean_country not in options:
        options.append(clean_country)
    return options


def country_selectbox(label, saved_country="", key=None):
    options = get_country_options(saved_country)
    selected_index = options.index(saved_country) if saved_country in options else 0
    selected_country = st.selectbox(label, options, index=selected_index, key=key)
    return "" if selected_country == "Select your country" else selected_country


def hash_password(password):
    salt = py_secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 150000)
    return f"pbkdf2_sha256$150000${salt}${password_hash.hex()}"


def verify_password(password, stored_password_hash):
    try:
        algorithm, iterations, salt, expected_hash = stored_password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(password_hash, expected_hash)
    except Exception:
        return False


def verify_platform_owner_password(password, owner_password_secret):
    owner_password_secret = str(owner_password_secret or "")
    if owner_password_secret.startswith("pbkdf2_sha256$"):
        return verify_password(password, owner_password_secret)
    return hmac.compare_digest(password, owner_password_secret)


def email_exists(email):
    rows = run_query("SELECT id FROM users WHERE email = ?", (normalize_email(email),))
    return not rows.empty


def register_business(business_name, owner_name, email, phone, country, password, confirm_password, accepted_terms):
    clean_email = normalize_email(email)
    if not all([business_name.strip(), owner_name.strip(), clean_email, phone.strip(), country.strip()]):
        return False, "Please complete all registration fields."
    if "@" not in clean_email or "." not in clean_email:
        return False, "Please enter a valid email address."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if password != confirm_password:
        return False, "Passwords do not match."
    if not accepted_terms:
        return False, "You must accept the Terms of Use and Privacy Policy before creating an account."
    if email_exists(clean_email):
        return False, "An account with this email already exists. Please log in instead."

    existing_users = run_query("SELECT COUNT(*) AS user_count FROM users")
    is_first_account = int(existing_users.iloc[0]["user_count"] or 0) == 0

    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    try:
        cursor.execute(
            """
            INSERT INTO businesses
            (business_name, owner_full_name, email, phone, country, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (business_name.strip(), owner_name.strip(), clean_email, phone.strip(), country.strip(), now),
        )
        business_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO users
            (business_id, full_name, email, phone, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (business_id, owner_name.strip(), clean_email, phone.strip(), hash_password(password), now),
        )
        user_id = cursor.lastrowid
        if is_first_account:
            cursor.execute("UPDATE stock SET business_id = ? WHERE business_id IS NULL", (business_id,))
            cursor.execute("UPDATE customers SET business_id = ? WHERE business_id IS NULL", (business_id,))
            cursor.execute("UPDATE sales SET business_id = ? WHERE business_id IS NULL", (business_id,))
            cursor.execute("UPDATE sale_items SET business_id = ? WHERE business_id IS NULL", (business_id,))
            cursor.execute("UPDATE payments SET business_id = ? WHERE business_id IS NULL", (business_id,))
            cursor.execute("DELETE FROM business_settings WHERE id = ? OR business_id IS NULL", (business_id,))
        cursor.execute(
            """
            INSERT INTO business_settings
            (id, business_id, business_name, business_phone, business_address, low_stock_alert_level, receipt_footer)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                business_id,
                business_id,
                business_name.strip(),
                phone.strip(),
                "",
                LOW_STOCK_LIMIT,
                DEFAULT_BUSINESS_SETTINGS["receipt_footer"],
            ),
        )
        conn.commit()
        st.session_state.logged_in = True
        st.session_state.authenticated = True
        st.session_state.login_role = "business"
        st.session_state.role = "business_user"
        st.session_state.user_id = user_id
        st.session_state.business_id = business_id
        st.session_state.business_name = business_name.strip()
        st.session_state.user_email = clean_email
        st.session_state.user_name = owner_name.strip()
        st.session_state.show_new_account_welcome = True
        return True, "Account created successfully. Welcome."
    except Exception as error:
        conn.rollback()
        return False, str(error)
    finally:
        conn.close()


def login_user(email, password):
    clean_email = normalize_email(email)
    owner_email, owner_password = get_platform_owner_credentials()
    if owner_email and owner_password and clean_email == normalize_email(owner_email):
        if verify_platform_owner_password(password, owner_password):
            st.session_state.logged_in = True
            st.session_state.authenticated = True
            st.session_state.login_role = "owner"
            st.session_state.role = "platform_owner"
            st.session_state.user_email = clean_email
            st.session_state.user_name = "Platform Owner"
            return True, "Welcome to the Platform Owner Dashboard."
        return False, "Invalid email or password."

    rows = run_query(
        """
        SELECT
            u.id,
            u.business_id,
            u.full_name,
            u.email,
            u.password_hash,
            b.business_name,
            COALESCE(b.status, 'active') AS status
        FROM users u
        JOIN businesses b ON b.id = u.business_id
        WHERE u.email = ?
        """,
        (clean_email,),
    )
    if rows.empty:
        return False, "Invalid email or password."

    row = rows.iloc[0]
    if row["status"] == "suspended":
        return False, "This business account is suspended. Please contact the platform owner."
    if not verify_password(password, row["password_hash"]):
        return False, "Invalid email or password."

    st.session_state.logged_in = True
    st.session_state.authenticated = True
    st.session_state.login_role = "business"
    st.session_state.role = "business_user"
    st.session_state.user_id = int(row["id"])
    st.session_state.business_id = int(row["business_id"])
    st.session_state.business_name = row["business_name"]
    st.session_state.user_email = row["email"]
    st.session_state.user_name = row["full_name"]
    return True, f"Welcome back to {row['business_name']}."


def current_business_id():
    return st.session_state.get("business_id")


def unique_suggestions(values, starter_values=()):
    """Return clean suggestions in first-seen order, without case-insensitive duplicates."""
    suggestions = []
    seen = set()
    for value in list(values) + list(starter_values):
        clean_value = str(value or "").strip()
        normalized = clean_value.casefold()
        if clean_value and normalized not in seen:
            seen.add(normalized)
            suggestions.append(clean_value)
    return suggestions


def get_business_stock_suggestions():
    """Only read suggestion values belonging to the signed-in business."""
    rows = run_query(
        """
        SELECT size, brand, COALESCE(pattern_model, '') AS pattern_model,
               COALESCE(supplier, '') AS supplier
        FROM stock
        WHERE business_id = ?
        ORDER BY id DESC
        """,
        (current_business_id(),),
    )
    if rows.empty:
        rows = pd.DataFrame(columns=["size", "brand", "pattern_model", "supplier"])
    return {
        "sizes": unique_suggestions(rows["size"].tolist(), COMMON_TYRE_SIZES),
        "brands": unique_suggestions(rows["brand"].tolist(), COMMON_TYRE_BRANDS),
        "patterns": unique_suggestions(rows["pattern_model"].tolist()),
        "suppliers": unique_suggestions(rows["supplier"].tolist()),
    }


def get_business_customer_suggestions():
    rows = run_query(
        """
        SELECT name, COALESCE(phone, '') AS phone
        FROM customers
        WHERE business_id = ?
        ORDER BY id DESC
        """,
        (current_business_id(),),
    )
    if rows.empty:
        return {"names": [], "phones": []}
    return {
        "names": unique_suggestions(rows["name"].tolist()),
        "phones": unique_suggestions(rows["phone"].tolist()),
    }


def suggestion_input(label, options, key, placeholder="Type or choose a suggestion", **kwargs):
    """A searchable Streamlit combobox that still accepts brand-new values."""
    return st.selectbox(
        label,
        options,
        index=None,
        placeholder=placeholder,
        accept_new_options=True,
        key=key,
        **kwargs,
    ) or ""


def require_login():
    if st.session_state.get("logged_in") and st.session_state.get("login_role") == "owner":
        return True
    if st.session_state.get("logged_in") and st.session_state.get("login_role") == "business" and current_business_id():
        return True

    render_page_header(APP_NAME, APP_SUBTITLE)
    login_tab, register_tab = st.tabs(["Login", "Create Account"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email address")
            password = st.text_input("Password", type="password")
            login_clicked = st.form_submit_button("Login")
        if login_clicked:
            success, message = login_user(email, password)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with register_tab:
        with st.form("register_business_form"):
            business_name = st.text_input("Business name")
            owner_name = st.text_input("Owner full name")
            email = st.text_input("Email address", key="register_email")
            phone = st.text_input("Phone / WhatsApp number")
            country = country_selectbox("Country", key="register_country")
            password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm password", type="password")
            accepted_terms = st.checkbox(
                "I accept the Terms of Use and Privacy Policy, and understand each business account has private data."
            )
            register_clicked = st.form_submit_button("Create Account")
        if register_clicked:
            success, message = register_business(
                business_name,
                owner_name,
                email,
                phone,
                country,
                password,
                confirm_password,
                accepted_terms,
            )
            if success:
                st.success(message)
                st.info("Welcome to Tyre Stock Manager. Start by adding your current tyre stock, then record your first sale.")
                st.rerun()
            else:
                st.error(message)

    return False


def using_postgres():
    return bool(get_database_url())


class PostgresCursor:
    def __init__(self, cursor):
        self.cursor = cursor
        self.lastrowid = None

    def execute(self, query, params=None):
        query = prepare_postgres_query(query)
        query = add_postgres_returning_id(query)
        params = tuple(params or ())
        self.cursor.execute(query, params)

        if query.rstrip().upper().endswith("RETURNING ID"):
            row = self.cursor.fetchone()
            self.lastrowid = row[0] if row else None
        else:
            self.lastrowid = None

        return self

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    @property
    def description(self):
        return self.cursor.description


class PostgresConnection:
    def __init__(self, connection):
        self.connection = connection

    def cursor(self):
        return PostgresCursor(self.connection.cursor())

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


def prepare_postgres_query(query):
    query = query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    query = query.replace("?", "%s")
    return query


def add_postgres_returning_id(query):
    clean_query = query.strip()
    if re.match(
        r"INSERT\s+INTO\s+(businesses|users|business_settings|stock|customers|sales|sale_items|payments)\b",
        clean_query,
        re.IGNORECASE,
    ):
        if "RETURNING" not in clean_query.upper():
            return f"{query.rstrip()} RETURNING id"
    return query


def get_connection():
    database_url = get_database_url()
    if database_url:
        import psycopg2

        return PostgresConnection(psycopg2.connect(database_url))

    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            owner_full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            country TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (business_id) REFERENCES businesses (id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER,
            size TEXT NOT NULL,
            brand TEXT NOT NULL,
            pattern_model TEXT,
            condition TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            buying_price REAL NOT NULL,
            selling_price REAL NOT NULL,
            supplier TEXT,
            date_added TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER,
            customer_type TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            vehicle_type TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER,
            invoice_number TEXT,
            customer_id INTEGER,
            customer_type TEXT,
            customer_name TEXT,
            phone TEXT,
            total_quantity INTEGER,
            total_amount REAL,
            total_cost REAL,
            total_profit REAL,
            payment_method TEXT,
            amount_paid REAL,
            balance REAL,
            payment_status TEXT,
            sale_date TEXT NOT NULL,
            created_at TEXT,
            stock_id INTEGER,
            size TEXT,
            brand TEXT,
            pattern_model TEXT,
            condition TEXT,
            quantity_sold INTEGER,
            selling_price REAL,
            buying_price REAL,
            profit REAL,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER,
            sale_id INTEGER NOT NULL,
            stock_id INTEGER NOT NULL,
            size TEXT NOT NULL,
            brand TEXT NOT NULL,
            pattern_model TEXT,
            condition TEXT NOT NULL,
            quantity_sold INTEGER NOT NULL,
            selling_price REAL NOT NULL,
            buying_price REAL NOT NULL,
            line_total REAL NOT NULL,
            line_cost REAL NOT NULL,
            line_profit REAL NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales (id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER,
            sale_id INTEGER NOT NULL,
            payment_date TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            amount_paid REAL NOT NULL,
            payment_note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales (id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS business_settings (
            id INTEGER PRIMARY KEY,
            business_id INTEGER,
            business_name TEXT,
            business_phone TEXT,
            business_address TEXT,
            low_stock_alert_level INTEGER,
            receipt_footer TEXT
        )
        """
    )

    migrate_database(cursor)

    conn.commit()
    conn.close()


def migrate_database(cursor):
    add_column_if_missing(cursor, "businesses", "status", "TEXT DEFAULT 'active'")
    add_column_if_missing(cursor, "stock", "pattern_model", "TEXT")
    add_column_if_missing(cursor, "stock", "business_id", "INTEGER")
    add_column_if_missing(cursor, "customers", "business_id", "INTEGER")

    sales_columns = {
        "business_id": "INTEGER",
        "invoice_number": "TEXT",
        "customer_id": "INTEGER",
        "customer_type": "TEXT",
        "customer_name": "TEXT",
        "phone": "TEXT",
        "address": "TEXT",
        "vehicle_type": "TEXT",
        "customer_notes": "TEXT",
        "total_quantity": "INTEGER",
        "total_amount": "REAL",
        "total_cost": "REAL",
        "total_profit": "REAL",
        "payment_method": "TEXT",
        "amount_paid": "REAL",
        "balance": "REAL",
        "payment_status": "TEXT",
        "promised_payment_date": "TEXT",
        "follow_up_note": "TEXT",
        "created_at": "TEXT",
        "stock_id": "INTEGER",
        "size": "TEXT",
        "brand": "TEXT",
        "pattern_model": "TEXT",
        "condition": "TEXT",
        "quantity_sold": "INTEGER",
        "selling_price": "REAL",
        "buying_price": "REAL",
        "profit": "REAL",
        "sale_status": "TEXT DEFAULT 'Active'",
        "cancellation_reason": "TEXT",
        "cancelled_at": "TEXT",
    }

    for column_name, column_type in sales_columns.items():
        add_column_if_missing(cursor, "sales", column_name, column_type)

    add_column_if_missing(cursor, "sale_items", "item_status", "TEXT DEFAULT 'Active'")
    add_column_if_missing(cursor, "sale_items", "business_id", "INTEGER")
    add_column_if_missing(cursor, "payments", "payment_status", "TEXT DEFAULT 'Active'")
    add_column_if_missing(cursor, "payments", "cancelled_at", "TEXT")
    add_column_if_missing(cursor, "payments", "business_id", "INTEGER")
    add_column_if_missing(cursor, "business_settings", "business_id", "INTEGER")
    add_column_if_missing(cursor, "business_settings", "business_name", "TEXT")
    add_column_if_missing(cursor, "business_settings", "business_phone", "TEXT")
    add_column_if_missing(cursor, "business_settings", "business_address", "TEXT")
    add_column_if_missing(cursor, "business_settings", "low_stock_alert_level", "INTEGER")
    add_column_if_missing(cursor, "business_settings", "receipt_footer", "TEXT")

    cursor.execute("UPDATE sales SET sale_status = 'Active' WHERE sale_status IS NULL OR sale_status = ''")
    cursor.execute("UPDATE sale_items SET item_status = 'Active' WHERE item_status IS NULL OR item_status = ''")
    cursor.execute("UPDATE payments SET payment_status = 'Active' WHERE payment_status IS NULL OR payment_status = ''")
    cursor.execute("UPDATE business_settings SET business_id = id WHERE business_id IS NULL")
    cursor.execute("UPDATE businesses SET status = 'active' WHERE status IS NULL OR status = ''")

    migrate_legacy_sales(cursor)
    migrate_legacy_payments(cursor)


def add_column_if_missing(cursor, table_name, column_name, column_type):
    if using_postgres():
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
                AND table_name = ?
            """,
            (table_name,),
        )
        existing_columns = [row[0] for row in cursor.fetchall()]
    else:
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = [row[1] for row in cursor.fetchall()]

    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def migrate_legacy_sales(cursor):
    cursor.execute(
        """
        SELECT
            s.id,
            s.stock_id,
            s.size,
            s.brand,
            COALESCE(s.pattern_model, ''),
            s.condition,
            s.quantity_sold,
            s.selling_price,
            s.buying_price,
            s.profit,
            s.sale_date
        FROM sales s
        LEFT JOIN sale_items si ON si.sale_id = s.id
        WHERE si.id IS NULL
            AND s.stock_id IS NOT NULL
            AND s.quantity_sold IS NOT NULL
        """
    )
    legacy_sales = cursor.fetchall()

    for sale in legacy_sales:
        (
            sale_id,
            stock_id,
            size,
            brand,
            pattern_model,
            condition,
            quantity_sold,
            selling_price,
            buying_price,
            profit,
            sale_date,
        ) = sale
        line_total = float(selling_price or 0) * int(quantity_sold or 0)
        line_cost = float(buying_price or 0) * int(quantity_sold or 0)
        line_profit = float(profit or (line_total - line_cost))

        cursor.execute(
            """
            INSERT INTO sale_items
            (
                sale_id,
                stock_id,
                size,
                brand,
                pattern_model,
                condition,
                quantity_sold,
                selling_price,
                buying_price,
                line_total,
                line_cost,
                line_profit
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sale_id,
                stock_id,
                size,
                brand,
                pattern_model,
                condition,
                int(quantity_sold or 0),
                float(selling_price or 0),
                float(buying_price or 0),
                line_total,
                line_cost,
                line_profit,
            ),
        )

        cursor.execute(
            """
            UPDATE sales
            SET
                invoice_number = COALESCE(invoice_number, ?),
                customer_type = COALESCE(customer_type, ?),
                customer_name = COALESCE(customer_name, ?),
                total_quantity = COALESCE(total_quantity, ?),
                total_amount = COALESCE(total_amount, ?),
                total_cost = COALESCE(total_cost, ?),
                total_profit = COALESCE(total_profit, ?),
                payment_method = COALESCE(payment_method, ?),
                amount_paid = COALESCE(amount_paid, ?),
                balance = COALESCE(balance, ?),
                payment_status = COALESCE(payment_status, ?),
                created_at = COALESCE(created_at, ?)
            WHERE id = ?
            """,
            (
                make_invoice_number(sale_id),
                WALK_IN_CUSTOMER,
                WALK_IN_CUSTOMER,
                int(quantity_sold or 0),
                line_total,
                line_cost,
                line_profit,
                "Cash",
                line_total,
                0.0,
                "Paid",
                str(sale_date or date.today()),
                sale_id,
            ),
        )


def migrate_legacy_payments(cursor):
    cursor.execute(
        """
        SELECT
            s.id,
            s.sale_date,
            COALESCE(s.payment_method, 'Cash'),
            COALESCE(s.amount_paid, s.total_amount, 0)
        FROM sales s
        LEFT JOIN payments p ON p.sale_id = s.id
        WHERE p.id IS NULL
            AND COALESCE(s.amount_paid, s.total_amount, 0) > 0
        """
    )
    sales_without_payments = cursor.fetchall()
    now = datetime.now().isoformat(timespec="seconds")

    for sale_id, sale_date, payment_method, amount_paid in sales_without_payments:
        cursor.execute(
            """
            INSERT INTO payments
            (sale_id, payment_date, payment_method, amount_paid, payment_note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                sale_id,
                str(sale_date or date.today()),
                payment_method or "Cash",
                float(amount_paid or 0),
                "Migrated from old sale payment",
                now,
            ),
        )


def make_invoice_number(sale_id):
    return f"INV-{sale_id:06d}"


def run_query(query, params=()):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=columns)
    finally:
        conn.close()


def get_business_settings():
    settings = DEFAULT_BUSINESS_SETTINGS.copy()
    business_id = current_business_id()
    if not business_id:
        return settings
    try:
        rows = run_query(
            """
            SELECT
                COALESCE(bs.business_name, '') AS business_name,
                COALESCE(bs.business_phone, '') AS business_phone,
                COALESCE(bs.business_address, '') AS business_address,
                COALESCE(bs.low_stock_alert_level, ?) AS low_stock_alert_level,
                COALESCE(bs.receipt_footer, '') AS receipt_footer,
                COALESCE(b.country, '') AS country
            FROM business_settings bs
            LEFT JOIN businesses b ON b.id = bs.business_id
            WHERE bs.business_id = ?
            """,
            (LOW_STOCK_LIMIT, business_id),
        )
    except Exception:
        return settings

    if rows.empty:
        return settings

    row = rows.iloc[0].to_dict()
    settings["business_name"] = row.get("business_name") or settings["business_name"]
    settings["business_phone"] = row.get("business_phone") or settings["business_phone"]
    settings["business_address"] = row.get("business_address") or settings["business_address"]
    settings["country"] = row.get("country") or settings["country"]
    settings["receipt_footer"] = row.get("receipt_footer") or settings["receipt_footer"]
    try:
        low_stock_level = int(row.get("low_stock_alert_level") or LOW_STOCK_LIMIT)
    except (TypeError, ValueError):
        low_stock_level = LOW_STOCK_LIMIT
    settings["low_stock_alert_level"] = max(low_stock_level, 1)
    return settings


def save_business_settings(business_name, business_phone, business_address, country, low_stock_alert_level, receipt_footer):
    business_id = current_business_id()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM business_settings WHERE business_id = ?", (business_id,))
    cursor.execute(
        """
        INSERT INTO business_settings
        (id, business_id, business_name, business_phone, business_address, low_stock_alert_level, receipt_footer)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            business_id,
            business_id,
            business_name.strip() or DEFAULT_BUSINESS_SETTINGS["business_name"],
            business_phone.strip(),
            business_address.strip(),
            int(low_stock_alert_level),
            receipt_footer.strip() or DEFAULT_BUSINESS_SETTINGS["receipt_footer"],
        ),
    )
    cursor.execute(
        """
        UPDATE businesses
        SET business_name = ?, phone = ?, country = ?
        WHERE id = ?
        """,
        (
            business_name.strip() or DEFAULT_BUSINESS_SETTINGS["business_name"],
            business_phone.strip(),
            country.strip(),
            business_id,
        ),
    )
    conn.commit()
    conn.close()


def get_low_stock_alert_level():
    return int(get_business_settings()["low_stock_alert_level"])


def add_csv_download(label, df, file_name, hidden_columns=None):
    if df.empty:
        return
    export_df = df.copy()
    if hidden_columns:
        export_df = export_df.drop(columns=[column for column in hidden_columns if column in export_df.columns])
    st.download_button(
        label,
        export_df.to_csv(index=False).encode("utf-8"),
        file_name=file_name,
        mime="text/csv",
    )


def add_stock(
    size,
    brand,
    pattern_model,
    condition,
    quantity,
    buying_price,
    selling_price,
    supplier,
    date_added,
):
    business_id = current_business_id()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO stock
        (
            business_id,
            size,
            brand,
            pattern_model,
            condition,
            quantity,
            buying_price,
            selling_price,
            supplier,
            date_added
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            business_id,
            size,
            brand,
            pattern_model,
            condition,
            quantity,
            buying_price,
            selling_price,
            supplier,
            str(date_added),
        ),
    )
    conn.commit()
    conn.close()


def delete_stock_item(stock_id):
    business_id = current_business_id()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stock WHERE id = ? AND business_id = ?", (stock_id, business_id))
    conn.commit()
    conn.close()


def clear_all_app_data():
    business_id = current_business_id()
    conn = get_connection()
    cursor = conn.cursor()
    if using_postgres():
        cursor.execute("DELETE FROM payments WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM sale_items WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM sales WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM customers WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM stock WHERE business_id = ?", (business_id,))
    else:
        cursor.execute("DELETE FROM payments WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM sale_items WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM sales WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM customers WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM stock WHERE business_id = ?", (business_id,))
    conn.commit()
    conn.close()


def get_or_create_customer(cursor, customer_type, name, phone, address, vehicle_type, notes):
    business_id = current_business_id()
    if customer_type == WALK_IN_CUSTOMER:
        return None, name.strip() or WALK_IN_CUSTOMER

    clean_name = name.strip()
    clean_phone = phone.strip()

    existing_customer_id = None
    if clean_phone:
        cursor.execute(
            """
            SELECT id FROM customers
            WHERE business_id = ? AND customer_type = ? AND phone = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (business_id, REGULAR_CUSTOMER, clean_phone),
        )
        row = cursor.fetchone()
        existing_customer_id = row[0] if row else None

    if existing_customer_id:
        cursor.execute(
            """
            UPDATE customers
            SET name = ?, address = ?, vehicle_type = ?, notes = ?
            WHERE id = ? AND business_id = ?
            """,
            (clean_name, address.strip(), vehicle_type.strip(), notes.strip(), existing_customer_id, business_id),
        )
        customer_id = existing_customer_id
    else:
        cursor.execute(
            """
            INSERT INTO customers
            (business_id, customer_type, name, phone, address, vehicle_type, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                business_id,
                REGULAR_CUSTOMER,
                clean_name,
                clean_phone,
                address.strip(),
                vehicle_type.strip(),
                notes.strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        customer_id = cursor.lastrowid

    return customer_id, clean_name


def calculate_payment_status(total_amount, amount_paid):
    balance = max(total_amount - amount_paid, 0.0)
    if amount_paid >= total_amount and total_amount > 0:
        status = "Paid"
    elif amount_paid > 0:
        status = "Part Payment"
    else:
        status = "Unpaid"
    return balance, status


def get_payment_methods_summary(payment_lines):
    totals = {}
    for payment in payment_lines:
        method = payment["payment_method"]
        totals[method] = totals.get(method, 0.0) + float(payment["amount_paid"])
    return "; ".join(f"{method} {format_currency(amount)}" for method, amount in totals.items())


def add_payment_to_current_sale(payment_date, payment_method, amount_paid, payment_note):
    payment = {
        "payment_date": str(payment_date),
        "payment_method": payment_method,
        "amount_paid": float(amount_paid),
        "payment_note": payment_note.strip(),
    }
    st.session_state.sale_payments.append(payment)


def get_payments_dataframe(payment_lines=None):
    payments = st.session_state.sale_payments if payment_lines is None else payment_lines
    if not payments:
        return pd.DataFrame()
    return pd.DataFrame(payments).rename(
        columns={
            "payment_date": "Payment Date",
            "payment_method": "Payment Method",
            "amount_paid": "Amount Paid",
            "payment_note": "Payment Note / Reference",
        }
    )


def update_sale_payment_totals(cursor, sale_id):
    business_id = current_business_id()
    cursor.execute(
        """
        SELECT COALESCE(total_amount, 0)
        FROM sales
        WHERE id = ? AND business_id = ?
        """,
        (sale_id, business_id),
    )
    row = cursor.fetchone()
    if not row:
        raise ValueError("Sale not found.")

    total_amount = float(row[0] or 0)
    cursor.execute(
        """
        SELECT COALESCE(SUM(amount_paid), 0)
        FROM payments
        WHERE sale_id = ?
            AND business_id = ?
            AND COALESCE(payment_status, 'Active') = 'Active'
        """,
        (sale_id, business_id),
    )
    amount_paid = float(cursor.fetchone()[0] or 0)
    balance, payment_status = calculate_payment_status(total_amount, amount_paid)

    cursor.execute(
        """
        SELECT payment_method, COALESCE(SUM(amount_paid), 0)
        FROM payments
        WHERE sale_id = ?
            AND business_id = ?
            AND COALESCE(payment_status, 'Active') = 'Active'
        GROUP BY payment_method
        ORDER BY MIN(id)
        """,
        (sale_id, business_id),
    )
    payment_summary = "; ".join(
        f"{method} {format_currency(amount)}" for method, amount in cursor.fetchall()
    )

    cursor.execute(
        """
        UPDATE sales
        SET amount_paid = ?,
            balance = ?,
            payment_status = ?,
            payment_method = ?
        WHERE id = ? AND business_id = ?
        """,
        (amount_paid, balance, payment_status, payment_summary, sale_id, business_id),
    )
    return amount_paid, balance, payment_status


def save_sale_transaction(
    cart_items,
    payment_lines,
    customer_type,
    customer_name,
    phone,
    address,
    vehicle_type,
    notes,
    promised_payment_date,
    follow_up_note,
    sale_date,
):
    business_id = current_business_id()
    if not cart_items:
        return False, "Add at least one tyre item before saving the sale."

    if customer_type == REGULAR_CUSTOMER and not customer_name.strip():
        return False, "Customer name is required for a regular customer."

    for payment in payment_lines:
        if float(payment["amount_paid"]) <= 0:
            return False, "Payment amount must be greater than zero."
        if payment["payment_method"] not in PAYMENT_METHODS:
            return False, "Please select a valid payment method."

    conn = get_connection()
    cursor = conn.cursor()

    try:
        stock_ids = [int(item["stock_id"]) for item in cart_items]
        placeholders = ",".join("?" for _ in stock_ids)
        cursor.execute(
            f"""
            SELECT id, quantity
            FROM stock
            WHERE business_id = ? AND id IN ({placeholders})
            """,
            [business_id] + stock_ids,
        )
        available_quantities = {row[0]: row[1] for row in cursor.fetchall()}

        totals_by_stock = {}
        for item in cart_items:
            stock_id = int(item["stock_id"])
            totals_by_stock[stock_id] = totals_by_stock.get(stock_id, 0) + int(item["quantity_sold"])

        for stock_id, quantity_sold in totals_by_stock.items():
            available_quantity = available_quantities.get(stock_id)
            if available_quantity is None:
                raise ValueError("One of the selected stock items no longer exists.")
            if quantity_sold > available_quantity:
                raise ValueError(
                    f"Not enough stock for item ID {stock_id}. Available: {available_quantity}, requested: {quantity_sold}."
                )

        customer_id, saved_customer_name = get_or_create_customer(
            cursor,
            customer_type,
            customer_name,
            phone,
            address,
            vehicle_type,
            notes,
        )

        total_quantity = sum(int(item["quantity_sold"]) for item in cart_items)
        total_amount = sum(float(item["line_total"]) for item in cart_items)
        total_cost = sum(float(item["line_cost"]) for item in cart_items)
        total_profit = total_amount - total_cost
        amount_paid = sum(float(payment["amount_paid"]) for payment in payment_lines)
        balance, payment_status = calculate_payment_status(total_amount, amount_paid)
        payment_method = get_payment_methods_summary(payment_lines)
        first_item = cart_items[0]
        now = datetime.now().isoformat(timespec="seconds")

        cursor.execute(
            """
            INSERT INTO sales
            (
                business_id,
                invoice_number,
                customer_id,
                customer_type,
                customer_name,
                phone,
                address,
                vehicle_type,
                customer_notes,
                total_quantity,
                total_amount,
                total_cost,
                total_profit,
                payment_method,
                amount_paid,
                balance,
                payment_status,
                promised_payment_date,
                follow_up_note,
                sale_date,
                created_at,
                stock_id,
                size,
                brand,
                pattern_model,
                condition,
                quantity_sold,
                selling_price,
                buying_price,
                profit,
                sale_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                business_id,
                "",
                customer_id,
                customer_type,
                saved_customer_name,
                phone.strip(),
                address.strip(),
                vehicle_type.strip(),
                notes.strip(),
                total_quantity,
                total_amount,
                total_cost,
                total_profit,
                payment_method,
                amount_paid,
                balance,
                payment_status,
                str(promised_payment_date) if promised_payment_date else "",
                follow_up_note.strip(),
                str(sale_date),
                now,
                int(first_item["stock_id"]),
                first_item["size"],
                first_item["brand"],
                first_item["pattern_model"],
                first_item["condition"],
                int(first_item["quantity_sold"]),
                float(first_item["selling_price"]),
                float(first_item["buying_price"]),
                float(first_item["line_profit"]),
                "Active",
            ),
        )
        sale_id = cursor.lastrowid
        invoice_number = make_invoice_number(sale_id)

        for payment in payment_lines:
            cursor.execute(
                """
                INSERT INTO payments
                (business_id, sale_id, payment_date, payment_method, amount_paid, payment_note, created_at, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    business_id,
                    sale_id,
                    payment["payment_date"],
                    payment["payment_method"],
                    float(payment["amount_paid"]),
                    payment["payment_note"],
                    now,
                    "Active",
                ),
            )

        for item in cart_items:
            cursor.execute(
                """
                INSERT INTO sale_items
                (
                    sale_id,
                    business_id,
                    stock_id,
                    size,
                    brand,
                    pattern_model,
                    condition,
                    quantity_sold,
                    selling_price,
                    buying_price,
                    line_total,
                    line_cost,
                    line_profit,
                    item_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sale_id,
                    business_id,
                    int(item["stock_id"]),
                    item["size"],
                    item["brand"],
                    item["pattern_model"],
                    item["condition"],
                    int(item["quantity_sold"]),
                    float(item["selling_price"]),
                    float(item["buying_price"]),
                    float(item["line_total"]),
                    float(item["line_cost"]),
                    float(item["line_profit"]),
                    "Active",
                ),
            )
            cursor.execute(
                """
                UPDATE stock
                SET quantity = quantity - ?
                WHERE id = ? AND business_id = ?
                """,
                (int(item["quantity_sold"]), int(item["stock_id"]), business_id),
            )

        cursor.execute(
            "UPDATE sales SET invoice_number = ? WHERE id = ? AND business_id = ?",
            (invoice_number, sale_id, business_id),
        )
        conn.commit()
        return True, f"Sale saved as {invoice_number}. Balance: {format_naira(balance)}."
    except Exception as error:
        conn.rollback()
        return False, str(error)
    finally:
        conn.close()


def record_followup_payment(sale_id, payment_date, payment_method, amount_paid, payment_note):
    business_id = current_business_id()
    if float(amount_paid) <= 0:
        return False, "Payment amount must be greater than zero."
    if payment_method not in PAYMENT_METHODS:
        return False, "Please select a valid payment method."

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT invoice_number, COALESCE(total_amount, 0), COALESCE(amount_paid, 0)
            FROM sales
            WHERE id = ?
                AND business_id = ?
                AND COALESCE(sale_status, 'Active') = 'Active'
            """,
            (sale_id, business_id),
        )
        sale = cursor.fetchone()
        if not sale:
            raise ValueError("Sale not found.")

        now = datetime.now().isoformat(timespec="seconds")
        cursor.execute(
            """
            INSERT INTO payments
            (business_id, sale_id, payment_date, payment_method, amount_paid, payment_note, created_at, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                business_id,
                sale_id,
                str(payment_date),
                payment_method,
                float(amount_paid),
                payment_note.strip(),
                now,
                "Active",
            ),
        )
        _, balance, payment_status = update_sale_payment_totals(cursor, sale_id)
        conn.commit()
        return True, f"Payment saved. New balance: {format_currency(balance)}. Status: {payment_status}."
    except Exception as error:
        conn.rollback()
        return False, str(error)
    finally:
        conn.close()


def delete_payment(payment_id):
    business_id = current_business_id()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT p.sale_id, COALESCE(s.sale_status, 'Active')
            FROM payments p
            JOIN sales s ON s.id = p.sale_id
            WHERE p.id = ?
                AND p.business_id = ?
                AND s.business_id = ?
                AND COALESCE(p.payment_status, 'Active') = 'Active'
            """,
            (payment_id, business_id, business_id),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("Payment not found or already removed.")

        sale_id, sale_status = row
        if sale_status != "Active":
            raise ValueError("Payments cannot be changed for a cancelled sale.")

        cursor.execute("DELETE FROM payments WHERE id = ? AND business_id = ?", (payment_id, business_id))
        _, balance, payment_status = update_sale_payment_totals(cursor, sale_id)
        conn.commit()
        return True, f"Payment removed. New balance: {format_currency(balance)}. Status: {payment_status}."
    except Exception as error:
        conn.rollback()
        return False, str(error)
    finally:
        conn.close()


def cancel_sale(sale_id, cancellation_reason):
    business_id = current_business_id()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT COALESCE(sale_status, 'Active')
            FROM sales
            WHERE id = ? AND business_id = ?
            """,
            (sale_id, business_id),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("Sale not found.")
        if row[0] == "Cancelled":
            raise ValueError("This sale is already cancelled.")

        cursor.execute(
            """
            SELECT stock_id, COALESCE(quantity_sold, 0)
            FROM sale_items
            WHERE sale_id = ?
                AND business_id = ?
                AND COALESCE(item_status, 'Active') = 'Active'
            """,
            (sale_id, business_id),
        )
        sale_items = cursor.fetchall()
        now = datetime.now().isoformat(timespec="seconds")

        for stock_id, quantity_sold in sale_items:
            cursor.execute(
                """
                UPDATE stock
                SET quantity = quantity + ?
                WHERE id = ? AND business_id = ?
                """,
                (int(quantity_sold or 0), int(stock_id), business_id),
            )

        cursor.execute(
            """
            UPDATE sale_items
            SET item_status = 'Cancelled'
            WHERE sale_id = ? AND business_id = ?
            """,
            (sale_id, business_id),
        )
        cursor.execute(
            """
            UPDATE payments
            SET payment_status = 'Cancelled',
                cancelled_at = ?
            WHERE sale_id = ? AND business_id = ?
            """,
            (now, sale_id, business_id),
        )
        cursor.execute(
            """
            UPDATE sales
            SET sale_status = 'Cancelled',
                cancellation_reason = ?,
                cancelled_at = ?,
                balance = 0,
                payment_status = 'Cancelled'
            WHERE id = ? AND business_id = ?
            """,
            (cancellation_reason.strip(), now, sale_id, business_id),
        )
        conn.commit()
        return True, "Sale cancelled. Stock quantities have been restored."
    except Exception as error:
        conn.rollback()
        return False, str(error)
    finally:
        conn.close()


def get_stock_dataframe(available_only=False):
    business_id = current_business_id()
    where_clause = "WHERE business_id = ?"
    if available_only:
        where_clause += " AND quantity > 0"
    return run_query(
        f"""
        SELECT
            id,
            size,
            brand,
            COALESCE(pattern_model, '') AS pattern_model,
            condition,
            quantity,
            buying_price,
            selling_price,
            supplier,
            date_added
        FROM stock
        {where_clause}
        ORDER BY brand, pattern_model, size, id
        """,
        (business_id,),
    )


def get_low_stock_dataframe():
    business_id = current_business_id()
    low_stock_limit = get_low_stock_alert_level()
    return run_query(
        """
        SELECT
            size AS "Tyre Size",
            brand AS "Brand",
            COALESCE(pattern_model, '') AS "Pattern / Model",
            condition AS "Condition",
            quantity AS "Quantity Left",
            buying_price AS "Buying Price",
            selling_price AS "Selling Price",
            quantity * selling_price AS "Total Stock Value",
            date_added AS "Date Added"
        FROM stock
        WHERE business_id = ? AND quantity <= ?
        ORDER BY quantity ASC, brand, pattern_model, size
        """,
        (business_id, low_stock_limit),
    )


def format_stock_label(row):
    pattern = row["pattern_model"] or ""
    return (
        f"ID {row['id']} | {str(row['brand']).title()} | {pattern.upper()} | "
        f"{str(row['size']).upper()} | {str(row['condition']).title()} | {row['quantity']} left"
    )


def format_naira(amount):
    try:
        value = float(amount or 0)
    except (TypeError, ValueError):
        value = 0
    return f"₦{round(value):,}"


def parse_naira_input(value):
    if value is None:
        return 0.0

    text = str(value).strip()
    if not text:
        return 0.0

    clean_text = (
        text.replace("₦", "")
        .replace("NGN", "")
        .replace("ngn", "")
        .replace(",", "")
        .replace(" ", "")
    )

    if not re.fullmatch(r"\d+(\.\d+)?", clean_text):
        return None

    amount = float(clean_text)
    if amount < 0:
        return None
    return amount


def format_currency(amount):
    return format_naira(amount)


def format_money_text(value):
    if pd.isna(value):
        return value

    def replace_match(match):
        return format_naira(match.group(1).replace(",", ""))

    return re.sub(r"NGN\s+([0-9,]+(?:\.[0-9]+)?)", replace_match, str(value))


def format_money_dataframe(df):
    if df.empty:
        return df

    money_columns = {
        "buying_price",
        "selling_price",
        "Buying Price",
        "Selling Price",
        "Line Total",
        "Line Cost",
        "Line Profit",
        "Total Amount",
        "Amount Paid",
        "Outstanding Balance",
        "Profit",
        "Total Cost",
        "Total Profit",
        "Total Stock Value",
        "Total Sales Value",
        "Running Total Paid",
        "Remaining Balance",
    }
    money_text_columns = {
        "Items Sold",
        "Payment Methods Used",
        "Payment History Summary",
    }

    display_df = df.copy()
    for column in display_df.columns:
        if column in money_columns:
            display_df[column] = display_df[column].apply(format_naira)
        elif column in money_text_columns:
            display_df[column] = display_df[column].apply(format_money_text)

    return display_df


def show_money_dataframe(df, **kwargs):
    st.dataframe(format_money_dataframe(df), **kwargs)


def render_page_header(title, subtitle=APP_SUBTITLE):
    st.markdown(
        f"""
        <div class="app-hero">
            <h1>{escape(title)}</h1>
            <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(title, subtitle=""):
    subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="section-title">
            <h2>{escape(title)}</h2>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label, value, detail="", tone=""):
    icon_map = {
        "stock": "▦",
        "sold": "✓",
        "sales": "₦",
        "profit": "↗",
        "balance": "◷",
        "low": "!",
        "business": "◆",
        "user": "●",
        "status": "•",
    }
    label_lower = str(label).lower()
    icon_key = next((key for key in icon_map if key in label_lower), "business")
    icon = icon_map[icon_key]
    detail_html = f'<div class="metric-detail">{escape(str(detail))}</div>' if detail else ""
    st.markdown(
        f"""
        <div class="metric-card {escape(tone)}">
            <div class="metric-icon">{escape(icon)}</div>
            <div class="metric-label">{escape(str(label))}</div>
            <div class="metric-value">{escape(str(value))}</div>
            {detail_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_naira_preview(items):
    preview_items = " | ".join(
        f"<strong>{escape(label)}:</strong> {escape(format_naira(value))}" for label, value in items
    )
    st.markdown(f'<div class="preview-strip">{preview_items}</div>', unsafe_allow_html=True)


def render_widget_label(label, helper_text=""):
    helper_html = f'<div class="visible-helper-text">{escape(helper_text)}</div>' if helper_text else ""
    st.markdown(
        f'<div class="visible-widget-label">{escape(label)}</div>{helper_html}',
        unsafe_allow_html=True,
    )


def render_receipt_summary(receipt):
    if not receipt:
        return

    settings = receipt.get("settings", DEFAULT_BUSINESS_SETTINGS)
    items_html = "".join(
        f"<li>{escape(str(item.get('brand', '')))} {escape(str(item.get('pattern_model', '')))} {escape(str(item.get('size', '')))} "
        f"x {escape(str(item['quantity_sold']))} @ {escape(format_naira(item['selling_price']))}</li>"
        for item in receipt.get("items", [])
    )
    st.markdown(
        f"""
        <div class="preview-strip">
            <strong>{escape(settings.get("business_name", DEFAULT_BUSINESS_SETTINGS["business_name"]))}</strong><br>
            {escape(settings.get("business_phone", ""))}<br>
            {escape(settings.get("business_address", ""))}
            <hr>
            <strong>Invoice:</strong> {escape(receipt.get("invoice_number", ""))}<br>
            <strong>Sale date:</strong> {escape(str(receipt.get("sale_date", "")))}<br>
            <strong>Customer:</strong> {escape(receipt.get("customer_name", WALK_IN_CUSTOMER))}<br>
            <strong>Items sold:</strong>
            <ul>{items_html}</ul>
            <strong>Total amount:</strong> {escape(format_naira(receipt.get("total_amount", 0)))}<br>
            <strong>Amount paid:</strong> {escape(format_naira(receipt.get("amount_paid", 0)))}<br>
            <strong>Outstanding balance:</strong> {escape(format_naira(receipt.get("balance", 0)))}<br>
            <strong>Payment method(s):</strong> {escape(receipt.get("payment_methods", ""))}<br>
            <br>{escape(settings.get("receipt_footer", DEFAULT_BUSINESS_SETTINGS["receipt_footer"]))}
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_dashboard():
    settings = get_business_settings()
    business_id = current_business_id()
    low_stock_limit = settings["low_stock_alert_level"]
    render_page_header(settings["business_name"], APP_SUBTITLE)
    if st.session_state.pop("show_new_account_welcome", False):
        st.success("Welcome to Tyre Stock Manager. Start by adding your current tyre stock, then record your first sale.")

    stock_df = run_query(
        """
        SELECT
            id,
            size,
            brand,
            COALESCE(pattern_model, '') AS "Pattern / Model",
            condition,
            quantity,
            buying_price,
            selling_price,
            supplier,
            date_added
        FROM stock
        WHERE business_id = ?
        """
        ,
        (business_id,),
    )
    sales_df = run_query(
        """
        SELECT
            COALESCE(total_quantity, quantity_sold, 0) AS total_quantity,
            COALESCE(total_amount, 0) AS total_amount,
            COALESCE(total_profit, profit, 0) AS total_profit,
            COALESCE(balance, 0) AS balance
        FROM sales
        WHERE business_id = ?
            AND COALESCE(sale_status, 'Active') = 'Active'
        """
        ,
        (business_id,),
    )

    total_stock = int(stock_df["quantity"].sum()) if not stock_df.empty else 0
    total_sales = int(sales_df["total_quantity"].sum()) if not sales_df.empty else 0
    total_sales_value = float(sales_df["total_amount"].sum()) if not sales_df.empty else 0.0
    total_profit = float(sales_df["total_profit"].sum()) if not sales_df.empty else 0.0
    outstanding_balance = float(sales_df["balance"].sum()) if not sales_df.empty else 0.0
    low_stock_df = stock_df[stock_df["quantity"] <= low_stock_limit] if not stock_df.empty else stock_df
    low_stock_count = len(low_stock_df) if not low_stock_df.empty else 0

    render_section("Business Overview", "The numbers that matter most for today’s stock and sales.")
    metric_cols = st.columns(3)
    with metric_cols[0]:
        render_metric_card("Total Tyres In Stock", total_stock, "Available inventory")
    with metric_cols[1]:
        render_metric_card("Total Tyres Sold", total_sales, "Active sales only")
    with metric_cols[2]:
        render_metric_card("Total Sales Value", format_currency(total_sales_value), "Active sales only", "gold")

    metric_cols = st.columns(3)
    with metric_cols[0]:
        render_metric_card("Total Profit", format_currency(total_profit), "From active sales", "gold")
    with metric_cols[1]:
        render_metric_card("Outstanding Balance", format_currency(outstanding_balance), "Money still expected", "warning")
    with metric_cols[2]:
        render_metric_card("Low Stock Items", low_stock_count, f"{low_stock_limit} tyres or fewer")

    render_section("Low Stock Alerts", "Items that may need restocking soon.")

    if low_stock_df.empty:
        st.success("No low-stock items right now. Stock levels look healthy.")
    else:
        st.warning(f"These items have {low_stock_limit} tyres or fewer left.")
        show_money_dataframe(low_stock_df, width="stretch")


def show_add_stock():
    render_page_header("Add Stock", "Build accurate inventory records in a simple, guided flow.")
    suggestions = get_business_stock_suggestions()

    with st.form("add_stock_form"):
        render_section("Tyre Details", "Identify the tyre clearly for search, sale, and reporting.")
        detail_col1, detail_col2 = st.columns(2)
        size = detail_col1.selectbox(
            "Tyre size", suggestions["sizes"], index=None,
            placeholder="Type a size or choose a suggestion", accept_new_options=True,
        ) or ""
        brand = detail_col2.selectbox(
            "Brand", suggestions["brands"], index=None,
            placeholder="Type a brand or choose a suggestion", accept_new_options=True,
        ) or ""
        pattern_model = suggestion_input(
            "Pattern / Model", suggestions["patterns"], "add_stock_pattern",
            placeholder="Type a new model or choose an existing one",
        )
        condition = detail_col2.selectbox("Condition", ["New", "Used", "Retread"])

        render_section("Supplier Details", "Keep supplier information business-specific and easy to reuse.")
        supplier = suggestion_input(
            "Supplier name", suggestions["suppliers"], "add_stock_supplier",
            placeholder="Type a new supplier or choose an existing one",
        )

        render_section("Pricing", "Enter prices naturally, with or without commas or the Naira sign.")
        buying_price_input = st.text_input(
            "Buying price per tyre",
            placeholder="Example: 350000, 350,000, or ₦350,000",
        )
        selling_price_input = st.text_input(
            "Selling price per tyre",
            placeholder="Example: 360000, 360,000, or ₦360,000",
        )
        buying_price = parse_naira_input(buying_price_input)
        selling_price = parse_naira_input(selling_price_input)

        if buying_price is None:
            st.warning("Enter a valid buying price, for example 350000, 350,000, or ₦350,000.")
        if selling_price is None:
            st.warning("Enter a valid selling price, for example 360000, 360,000, or ₦360,000.")

        render_section("Quantity / Notes", "Set the quantity and date for this inventory entry.")
        quantity = st.number_input("Quantity", min_value=1, step=1)

        if buying_price is not None and selling_price is not None:
            profit_per_tyre = selling_price - buying_price
            total_stock_cost = buying_price * int(quantity)
            total_stock_value = selling_price * int(quantity)
            render_naira_preview(
                [
                    ("Buying price", buying_price),
                    ("Selling price", selling_price),
                    ("Profit per tyre", profit_per_tyre),
                    ("Total stock cost", total_stock_cost),
                    ("Total stock value", total_stock_value),
                ]
            )

        date_added = st.date_input("Date added", value=date.today())

        submitted = st.form_submit_button("Save Stock")

    if submitted:
        if not size.strip() or not brand.strip():
            st.error("Please enter tyre size and brand.")
        elif buying_price is None or selling_price is None:
            st.error("Please enter valid buying and selling prices before saving.")
        elif selling_price < buying_price:
            st.error("Selling price should not be less than buying price.")
        else:
            add_stock(
                size.strip(),
                brand.strip(),
                pattern_model.strip(),
                condition,
                int(quantity),
                float(buying_price),
                float(selling_price),
                supplier.strip(),
                date_added,
            )
            st.success(f"Stock added successfully: {quantity} tyre(s) saved for {brand.strip().title()}.")


def show_all_stock():
    render_page_header("View Stock", "Review inventory, prices, suppliers, and available quantities.")

    stock_df = run_query(
        """
        SELECT
            id,
            size,
            brand,
            COALESCE(pattern_model, '') AS "Pattern / Model",
            condition,
            quantity,
            buying_price,
            selling_price,
            supplier,
            date_added
        FROM stock
        WHERE business_id = ?
        ORDER BY id DESC
        """,
        (current_business_id(),),
    )

    if stock_df.empty:
        st.info("No stock has been added yet. Add your first tyre item from the Add Stock page.")
    else:
        add_csv_download("Download stock list CSV", stock_df, "stock-list.csv")
        show_money_dataframe(stock_df, width="stretch")
        render_section("Delete Stock Item", "Remove incorrect stock entries while keeping historical sales intact.")
        st.warning("Deleting stock removes it from current stock only. Old sales reports keep their saved tyre details.")

        for row in stock_df.itertuples(index=False):
            row_id = int(row.id)
            pattern = f" {getattr(row, '_3')}" if getattr(row, "_3") else ""
            label = f"ID {row_id} - {row.brand}{pattern} {row.size} ({row.condition})"
            with st.expander(label):
                confirm = st.checkbox(
                    "I understand this stock item will be deleted.",
                    key=f"confirm_delete_stock_{row_id}",
                )
                delete_stock_text = st.text_input("Type DELETE to confirm", key=f"delete_stock_text_{row_id}")
                if st.button(
                    "Delete this stock item",
                    key=f"delete_stock_{row_id}",
                    disabled=not confirm or delete_stock_text != "DELETE",
                ):
                    delete_stock_item(row_id)
                    st.success("Stock item deleted.")
                    st.rerun()

    render_section("Clear All Data", "Use only when you intentionally want to empty this app database.")
    st.warning(
        "This clears stock, sales, sale items, and saved customers inside the app. "
        "It does not delete app.py, requirements.txt, README.md, or the database file."
    )
    with st.expander("Clear all app data"):
        confirmation_text = st.text_input("Type DELETE to confirm", key="clear_all_confirmation")
        if st.button("Clear all data", disabled=confirmation_text != "DELETE"):
            clear_all_app_data()
            st.success("All app records have been cleared. The database file is still in place.")
            st.rerun()


def show_low_stock_items():
    settings = get_business_settings()
    low_stock_limit = settings["low_stock_alert_level"]
    render_page_header("Low Stock Items", f"Tyres with {low_stock_limit} or fewer pieces left.")

    low_stock_df = get_low_stock_dataframe()
    suggestions = get_business_stock_suggestions()
    search_term = suggestion_input(
        "Search low-stock tyres",
        unique_suggestions(
            suggestions["sizes"] + suggestions["brands"] + suggestions["patterns"]
        ),
        "low_stock_search",
        placeholder="Type or choose a size, brand, or pattern",
    )
    visible_df = filter_dataframe_by_search(low_stock_df, search_term)

    if visible_df.empty:
        st.info("No low-stock tyres right now.")
        return

    add_csv_download("Download low-stock CSV", visible_df, "low-stock-items.csv")
    show_money_dataframe(visible_df, width="stretch")


def show_search():
    render_page_header("Search Tyres", "Quickly find tyres by size, brand, pattern, or condition.")
    suggestions = get_business_stock_suggestions()

    col1, col2, col3 = st.columns(3)
    size = col1.selectbox(
        "Search by size", suggestions["sizes"], index=None,
        placeholder="Any size", accept_new_options=True,
    ) or ""
    brand = col2.selectbox(
        "Search by brand", suggestions["brands"], index=None,
        placeholder="Any brand", accept_new_options=True,
    ) or ""
    pattern_model = col3.selectbox(
        "Search by pattern/model", suggestions["patterns"], index=None,
        placeholder="Any pattern", accept_new_options=True,
    ) or ""
    condition = col1.selectbox("Condition", ["Any", "New", "Used", "Retread"])
    supplier = col2.selectbox(
        "Search by supplier", suggestions["suppliers"], index=None,
        placeholder="Any supplier", accept_new_options=True,
    ) or ""

    query = """
        SELECT
            id,
            size,
            brand,
            COALESCE(pattern_model, '') AS "Pattern / Model",
            condition,
            quantity,
            buying_price,
            selling_price,
            supplier,
            date_added
        FROM stock
        WHERE business_id = ?
    """
    params = [current_business_id()]

    if size.strip():
        query += " AND size LIKE ?"
        params.append(f"%{size.strip()}%")

    if brand.strip():
        query += " AND brand LIKE ?"
        params.append(f"%{brand.strip()}%")

    if pattern_model.strip():
        query += " AND pattern_model LIKE ?"
        params.append(f"%{pattern_model.strip()}%")

    if condition != "Any":
        query += " AND condition = ?"
        params.append(condition)

    if supplier.strip():
        query += " AND supplier LIKE ?"
        params.append(f"%{supplier.strip()}%")

    query += " ORDER BY id DESC"
    results_df = run_query(query, params)

    if results_df.empty:
        st.info("No tyres match this search. Try a different size, brand, pattern, or condition.")
    else:
        add_csv_download("Download search results CSV", results_df, "tyre-search-results.csv")
        show_money_dataframe(results_df, width="stretch")


def add_item_to_cart(stock_row, quantity_sold, selling_price):
    line_total = float(selling_price) * int(quantity_sold)
    line_cost = float(stock_row["buying_price"]) * int(quantity_sold)
    item = {
        "stock_id": int(stock_row["id"]),
        "brand": stock_row["brand"],
        "pattern_model": stock_row["pattern_model"],
        "size": stock_row["size"],
        "condition": stock_row["condition"],
        "quantity_sold": int(quantity_sold),
        "selling_price": float(selling_price),
        "buying_price": float(stock_row["buying_price"]),
        "line_total": line_total,
        "line_cost": line_cost,
        "line_profit": line_total - line_cost,
    }
    st.session_state.sale_cart.append(item)


def get_cart_dataframe():
    if not st.session_state.sale_cart:
        return pd.DataFrame()
    cart_df = pd.DataFrame(st.session_state.sale_cart)
    return cart_df.rename(
        columns={
            "stock_id": "Stock ID",
            "brand": "Brand",
            "pattern_model": "Pattern / Model",
            "size": "Size",
            "condition": "Condition",
            "quantity_sold": "Quantity",
            "selling_price": "Selling Price",
            "buying_price": "Buying Price",
            "line_total": "Line Total",
            "line_cost": "Line Cost",
            "line_profit": "Line Profit",
        }
    )


def show_customer_fields(customer_type):
    customer_name = ""
    phone = ""
    address = ""
    vehicle_type = ""
    notes = ""

    if customer_type == WALK_IN_CUSTOMER:
        render_widget_label("Customer name (optional)")
        customer_name = st.text_input(
            "Customer name (optional)",
            placeholder="Leave blank for Walk-in Customer",
            label_visibility="collapsed",
        )
    else:
        customers_df = run_query(
            """
            SELECT id, name, phone, address, vehicle_type, notes
            FROM customers
            WHERE business_id = ? AND customer_type = ?
            ORDER BY name
            """,
            (current_business_id(), REGULAR_CUSTOMER),
        )
        customer_choices = []
        customer_lookup = {}
        for row in customers_df.itertuples(index=False):
            customer_choices.append(row.name)
            customer_lookup.setdefault(str(row.name).casefold(), row)

        selected_customer = st.selectbox(
            "Customer name",
            unique_suggestions(customer_choices),
            index=None,
            placeholder="Type a new name or choose an existing customer",
            accept_new_options=True,
            key="sale_customer_name",
        ) or ""
        selected = customer_lookup.get(selected_customer.casefold())
        if selected is not None:
            customer_name = selected.name or ""
            phone = selected.phone or ""
            address = selected.address or ""
            vehicle_type = selected.vehicle_type or ""
            notes = selected.notes or ""
        else:
            customer_name = selected_customer

        phone_choices = unique_suggestions(customers_df["phone"].tolist())
        phone = st.selectbox(
            "Customer phone",
            phone_choices,
            index=phone_choices.index(phone) if phone in phone_choices else None,
            placeholder="Type a new phone or choose an existing one",
            accept_new_options=True,
            key=f"sale_customer_phone_{selected_customer}",
        ) or phone
        render_widget_label("Address / Location")
        address = st.text_input("Address / Location", value=address, label_visibility="collapsed")
        render_widget_label("Vehicle type")
        vehicle_type = st.text_input(
            "Vehicle type",
            value=vehicle_type,
            placeholder="Example: Toyota Camry",
            label_visibility="collapsed",
        )
        notes = st.text_area("Notes", value=notes)

    return customer_name, phone, address, vehicle_type, notes


def show_record_sale():
    render_page_header("Record Sale", "Checkout tyres, collect payments, and track balances in one flow.")
    if st.session_state.get("last_receipt"):
        render_section("Last Sale Receipt", "Receipt summary from the most recently saved sale.")
        render_receipt_summary(st.session_state.last_receipt)

    if "sale_cart" not in st.session_state:
        st.session_state.sale_cart = []
    if "sale_payments" not in st.session_state:
        st.session_state.sale_payments = []

    stock_df = get_stock_dataframe(available_only=True)

    if stock_df.empty:
        st.info("There is no available stock to sell.")
    else:
        stock_df["label"] = stock_df.apply(format_stock_label, axis=1)

        render_section("1. Select Tyre Items", "Search available stock and add items to the current sale.")
        stock_suggestions = get_business_stock_suggestions()
        search_term = suggestion_input(
            "Search by brand, pattern / model, size, condition, or stock ID",
            unique_suggestions(
                stock_suggestions["sizes"]
                + stock_suggestions["brands"]
                + stock_suggestions["patterns"]
                + ["New", "Used", "Retread"]
            ),
            "sale_stock_search",
            placeholder="Type or choose a size, brand, pattern, or condition",
        )
        filtered_stock_df = stock_df.copy()
        if search_term.strip():
            search_value = search_term.strip().lower().replace("id ", "")
            search_text = (
                filtered_stock_df["id"].astype(str)
                + " "
                + filtered_stock_df["brand"].fillna("").astype(str)
                + " "
                + filtered_stock_df["pattern_model"].fillna("").astype(str)
                + " "
                + filtered_stock_df["size"].fillna("").astype(str)
                + " "
                + filtered_stock_df["condition"].fillna("").astype(str)
            ).str.lower()
            filtered_stock_df = filtered_stock_df[search_text.str.contains(search_value, regex=False)]

        if filtered_stock_df.empty:
            st.info("No available tyres match that search.")
        else:
            selected_label = st.selectbox("Choose tyre from stock", filtered_stock_df["label"].tolist())
            selected_row = filtered_stock_df[filtered_stock_df["label"] == selected_label].iloc[0]
            st.caption(selected_label)
            col1, col2 = st.columns(2)
            quantity_sold = col1.number_input(
                "Quantity sold",
                min_value=1,
                max_value=int(selected_row["quantity"]),
                step=1,
            )
            selling_price_input = col2.text_input(
                "Selling price per tyre",
                value=format_naira(selected_row["selling_price"]),
                key=f"selling_price_{selected_row['id']}",
            )
            selling_price = parse_naira_input(selling_price_input)
            if selling_price is None:
                st.warning("Enter a valid selling price, for example 350000, 350,000, or ₦350,000.")
            else:
                line_total = selling_price * int(quantity_sold)
                line_profit = line_total - (float(selected_row["buying_price"]) * int(quantity_sold))
                render_naira_preview(
                    [
                        ("Selling price", selling_price),
                        ("Line total", line_total),
                        ("Line profit", line_profit),
                    ]
                )

            if st.button("Add Item to Sale"):
                existing_quantity = sum(
                    item["quantity_sold"]
                    for item in st.session_state.sale_cart
                    if item["stock_id"] == int(selected_row["id"])
                )
                if selling_price is None:
                    st.error("Please enter a valid selling price before adding this item.")
                elif existing_quantity + int(quantity_sold) > int(selected_row["quantity"]):
                    st.error("Not enough stock available for this tyre item.")
                else:
                    add_item_to_cart(selected_row, int(quantity_sold), float(selling_price))
                    st.success("Item added to current sale.")
                    st.rerun()

    render_section("2. Current Sale / Cart", "Review selected tyres before saving the sale.")
    cart_df = get_cart_dataframe()
    if cart_df.empty:
        st.info("No items added yet.")
    else:
        show_money_dataframe(cart_df, width="stretch")
        item_options = [
            f"{index + 1}. ID {item['stock_id']} | {item['brand']} | {item['pattern_model']} | {item['size']} x {item['quantity_sold']}"
            for index, item in enumerate(st.session_state.sale_cart)
        ]
        item_to_remove = st.selectbox("Remove item from current sale", item_options)
        if st.button("Remove selected item"):
            remove_index = item_options.index(item_to_remove)
            st.session_state.sale_cart.pop(remove_index)
            st.success("Item removed from current sale.")
            st.rerun()

    total_quantity = sum(item["quantity_sold"] for item in st.session_state.sale_cart)
    total_amount = sum(item["line_total"] for item in st.session_state.sale_cart)
    total_cost = sum(item["line_cost"] for item in st.session_state.sale_cart)
    total_profit = total_amount - total_cost

    render_section("3. Payment Details", "Record cash, POS, transfer, credit, or other payment details.")
    with st.form("add_sale_payment_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        payment_date = col1.date_input("Payment date", value=date.today())
        payment_method = col2.selectbox("Payment method", PAYMENT_METHODS)
        payment_amount_input = col3.text_input(
            "Amount paid",
            placeholder="Example: 50000, 50,000, or ₦50,000",
        )
        payment_amount = parse_naira_input(payment_amount_input)
        if payment_amount is None:
            st.warning("Enter a valid payment amount, for example 50000, 50,000, or ₦50,000.")
        else:
            st.caption(f"Amount paid: {format_naira(payment_amount)}")
        payment_note = st.text_input("Payment note / reference (optional)")
        add_payment_submitted = st.form_submit_button("Add Payment")

    if add_payment_submitted:
        if payment_amount is None:
            st.error("Please enter a valid payment amount.")
        elif payment_amount <= 0:
            st.error("Enter an amount greater than zero.")
        else:
            add_payment_to_current_sale(payment_date, payment_method, float(payment_amount), payment_note)
            st.success("Payment added to current sale.")
            st.rerun()

    payments_df = get_payments_dataframe()
    if payments_df.empty:
        st.info("No payment added yet. Leave empty for an unpaid sale.")
    else:
        show_money_dataframe(payments_df, width="stretch")
        payment_options = [
            f"{index + 1}. {payment['payment_date']} | {payment['payment_method']} | {format_currency(payment['amount_paid'])}"
            for index, payment in enumerate(st.session_state.sale_payments)
        ]
        payment_to_remove = st.selectbox("Remove payment from current sale", payment_options)
        if st.button("Remove selected payment"):
            remove_index = payment_options.index(payment_to_remove)
            st.session_state.sale_payments.pop(remove_index)
            st.success("Payment removed from current sale.")
            st.rerun()

    total_paid = sum(payment["amount_paid"] for payment in st.session_state.sale_payments)
    balance, payment_status = calculate_payment_status(total_amount, total_paid)
    overpayment = max(total_paid - total_amount, 0.0) if total_amount > 0 else 0.0

    render_section("4. Sale Summary", "Confirm the checkout totals before saving.")
    summary_cols = st.columns(4)
    with summary_cols[0]:
        render_metric_card("Total Quantity", total_quantity)
    with summary_cols[1]:
        render_metric_card("Total Amount", format_currency(total_amount), tone="gold")
    with summary_cols[2]:
        render_metric_card("Amount Paid", format_currency(total_paid))
    with summary_cols[3]:
        render_metric_card("Outstanding Balance", format_currency(balance), tone="warning")

    summary_cols = st.columns(3)
    with summary_cols[0]:
        render_metric_card("Total Cost", format_currency(total_cost))
    with summary_cols[1]:
        render_metric_card("Total Profit", format_currency(total_profit), tone="gold")
    with summary_cols[2]:
        render_metric_card("Payment Status", payment_status)

    if overpayment > 0:
        st.warning(f"Overpayment: {format_currency(overpayment)}. Confirm before saving this sale.")
        confirm_overpayment = st.checkbox("I confirm this overpayment is correct")
    else:
        confirm_overpayment = True

    render_section("5. Customer And Follow-up", "Attach customer details and promised payment dates when needed.")
    render_widget_label("Customer type")
    customer_type = st.radio(
        "Customer type",
        [WALK_IN_CUSTOMER, REGULAR_CUSTOMER],
        horizontal=True,
        label_visibility="collapsed",
    )
    customer_name, phone, address, vehicle_type, notes = show_customer_fields(customer_type)
    render_widget_label("Sale date")
    sale_date = st.date_input("Sale date", value=date.today(), label_visibility="collapsed")
    promised_payment_date = None
    follow_up_note = ""
    if balance > 0:
        render_widget_label("Promised Payment Date")
        promised_payment_date = st.date_input(
            "Promised Payment Date",
            value=date.today(),
            label_visibility="collapsed",
        )
        follow_up_note = st.text_area(
            "Payment Follow-up Note",
            placeholder="Example: Customer promised to pay balance after delivery",
        )
    else:
        st.caption("Promised Payment Date and Follow-up Note are only needed when there is an outstanding balance.")

    if st.button("Save Full Sale", disabled=not st.session_state.sale_cart or not confirm_overpayment):
        success, message = save_sale_transaction(
            st.session_state.sale_cart,
            st.session_state.sale_payments,
            customer_type,
            customer_name,
            phone,
            address,
            vehicle_type,
            notes,
            promised_payment_date,
            follow_up_note,
            sale_date,
        )

        if success:
            invoice_match = re.search(r"(INV-\d+)", message)
            invoice_number = invoice_match.group(1) if invoice_match else ""
            st.session_state.last_receipt = {
                "settings": get_business_settings(),
                "invoice_number": invoice_number,
                "sale_date": sale_date,
                "customer_name": customer_name.strip() or WALK_IN_CUSTOMER,
                "items": [item.copy() for item in st.session_state.sale_cart],
                "total_amount": total_amount,
                "amount_paid": total_paid,
                "balance": balance,
                "payment_methods": get_payment_methods_summary(st.session_state.sale_payments),
            }
            st.session_state.sale_cart = []
            st.session_state.sale_payments = []
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    render_section("Recent Sales", "Latest sales saved in the app.")
    recent_sales_df = get_sales_report_dataframe(limit=20)
    if recent_sales_df.empty:
        st.info("No sales have been recorded yet.")
    else:
        show_money_dataframe(recent_sales_df, width="stretch")


def get_sales_report_dataframe(limit=None, sale_status="Active"):
    business_id = current_business_id()
    limit_clause = f"LIMIT {int(limit)}" if limit else ""
    if using_postgres():
        return run_query(
            f"""
            SELECT
                s.id AS "Sale ID",
                s.invoice_number AS "Invoice Number",
                s.sale_date AS "Date",
                COALESCE(s.customer_type, ?) AS "Customer Type",
                COALESCE(s.customer_name, ?) AS "Customer Name",
                COALESCE(s.phone, '') AS "Phone Number",
                COALESCE(s.address, '') AS "Address / Location",
                STRING_AGG(
                    si.brand || ' ' ||
                    CASE
                        WHEN COALESCE(si.pattern_model, '') = '' THEN ''
                        ELSE si.pattern_model || ' '
                    END ||
                    si.size || ' (' || si.condition || ') x ' ||
                    si.quantity_sold::text || ' @ NGN ' ||
                    TO_CHAR(si.selling_price, 'FM999999999999990.00'),
                    '; '
                    ORDER BY si.id
                ) AS "Items Sold",
                COALESCE(s.total_amount, SUM(si.line_total), 0) AS "Total Amount",
                COALESCE(s.amount_paid, 0) AS "Amount Paid",
                COALESCE(s.balance, 0) AS "Outstanding Balance",
                COALESCE(s.total_profit, SUM(si.line_profit), 0) AS "Profit",
                COALESCE(s.payment_status, '') AS "Payment Status",
                COALESCE(s.promised_payment_date, '') AS "Promised Payment Date",
                COALESCE(payments.payment_methods, COALESCE(s.payment_method, '')) AS "Payment Methods Used",
                COALESCE(payments.payment_history, '') AS "Payment History Summary",
                COALESCE(s.sale_status, 'Active') AS "Sale Status",
                COALESCE(s.cancellation_reason, '') AS "Cancellation Reason",
                COALESCE(s.cancelled_at, '') AS "Cancelled At"
            FROM sales s
            LEFT JOIN sale_items si ON si.sale_id = s.id
                AND si.business_id = s.business_id
                AND COALESCE(si.item_status, 'Active') = COALESCE(s.sale_status, 'Active')
            LEFT JOIN (
                SELECT
                    sale_id,
                    STRING_AGG(payment_method || ' ' || 'NGN ' || TO_CHAR(amount_paid, 'FM999999999999990.00'), '; ' ORDER BY id) AS payment_methods,
                    STRING_AGG(payment_date || ' | ' || payment_method || ' | NGN ' || TO_CHAR(amount_paid, 'FM999999999999990.00'), '; ' ORDER BY id) AS payment_history
                FROM payments
                WHERE business_id = ?
                    AND COALESCE(payment_status, 'Active') = ?
                GROUP BY sale_id
            ) payments ON payments.sale_id = s.id
            WHERE s.business_id = ?
                AND COALESCE(s.sale_status, 'Active') = ?
            GROUP BY s.id, payments.payment_methods, payments.payment_history
            ORDER BY s.sale_date DESC, s.id DESC
            {limit_clause}
            """,
            (WALK_IN_CUSTOMER, WALK_IN_CUSTOMER, business_id, sale_status, business_id, sale_status),
        )

    return run_query(
        f"""
        SELECT
            s.id AS "Sale ID",
            s.invoice_number AS "Invoice Number",
            s.sale_date AS "Date",
            COALESCE(s.customer_type, ?) AS "Customer Type",
            COALESCE(s.customer_name, ?) AS "Customer Name",
            COALESCE(s.phone, '') AS "Phone Number",
            COALESCE(s.address, '') AS "Address / Location",
            GROUP_CONCAT(
                si.brand || ' ' ||
                CASE
                    WHEN COALESCE(si.pattern_model, '') = '' THEN ''
                    ELSE si.pattern_model || ' '
                END ||
                si.size || ' (' || si.condition || ') x ' ||
                si.quantity_sold || ' @ NGN ' ||
                printf('%.2f', si.selling_price),
                '; '
            ) AS "Items Sold",
            COALESCE(s.total_amount, SUM(si.line_total), 0) AS "Total Amount",
            COALESCE(s.amount_paid, 0) AS "Amount Paid",
            COALESCE(s.balance, 0) AS "Outstanding Balance",
            COALESCE(s.total_profit, SUM(si.line_profit), 0) AS "Profit",
            COALESCE(s.payment_status, '') AS "Payment Status",
            COALESCE(s.promised_payment_date, '') AS "Promised Payment Date",
            COALESCE(payments.payment_methods, COALESCE(s.payment_method, '')) AS "Payment Methods Used",
            COALESCE(payments.payment_history, '') AS "Payment History Summary",
            COALESCE(s.sale_status, 'Active') AS "Sale Status",
            COALESCE(s.cancellation_reason, '') AS "Cancellation Reason",
            COALESCE(s.cancelled_at, '') AS "Cancelled At"
        FROM sales s
        LEFT JOIN sale_items si ON si.sale_id = s.id
            AND si.business_id = s.business_id
            AND COALESCE(si.item_status, 'Active') = COALESCE(s.sale_status, 'Active')
        LEFT JOIN (
            SELECT
                sale_id,
                GROUP_CONCAT(payment_method || ' ' || 'NGN ' || printf('%.2f', amount_paid), '; ') AS payment_methods,
                GROUP_CONCAT(payment_date || ' | ' || payment_method || ' | NGN ' || printf('%.2f', amount_paid), '; ') AS payment_history
            FROM payments
            WHERE business_id = ?
                AND COALESCE(payment_status, 'Active') = ?
            GROUP BY sale_id
        ) payments ON payments.sale_id = s.id
        WHERE s.business_id = ?
            AND COALESCE(s.sale_status, 'Active') = ?
        GROUP BY s.id
        ORDER BY s.sale_date DESC, s.id DESC
        {limit_clause}
        """,
        (WALK_IN_CUSTOMER, WALK_IN_CUSTOMER, business_id, sale_status, business_id, sale_status),
    )


def get_outstanding_balances_dataframe(filter_option="All"):
    business_id = current_business_id()
    today = str(date.today())
    where_clause = "WHERE s.business_id = ? AND COALESCE(s.balance, 0) > 0 AND COALESCE(s.sale_status, 'Active') = 'Active'"
    params = [WALK_IN_CUSTOMER, WALK_IN_CUSTOMER, business_id]

    if filter_option == "Due today":
        where_clause += " AND s.promised_payment_date = ?"
        params.append(today)
    elif filter_option == "Overdue":
        where_clause += " AND s.promised_payment_date <> '' AND s.promised_payment_date < ?"
        params.append(today)
    elif filter_option == "Upcoming":
        where_clause += " AND s.promised_payment_date <> '' AND s.promised_payment_date > ?"
        params.append(today)
    elif filter_option in ["Part Payment", "Unpaid"]:
        where_clause += " AND COALESCE(s.payment_status, '') = ?"
        params.append(filter_option)

    if using_postgres():
        return run_query(
            f"""
            SELECT
                s.id AS "Sale ID",
                s.invoice_number AS "Invoice Number",
                s.sale_date AS "Sale Date",
                COALESCE(s.customer_type, ?) AS "Customer Type",
                COALESCE(s.customer_name, ?) AS "Customer Name",
                COALESCE(s.phone, '') AS "Phone Number",
                COALESCE(s.total_amount, 0) AS "Total Amount",
                COALESCE(s.amount_paid, 0) AS "Amount Paid",
                COALESCE(s.balance, 0) AS "Outstanding Balance",
                COALESCE(s.promised_payment_date, '') AS "Promised Payment Date",
                COALESCE(s.payment_status, '') AS "Payment Status",
                COALESCE(s.follow_up_note, '') AS "Follow-up Note",
                COALESCE(items.items_sold, '') AS "Items Sold",
                COALESCE(items.brands, '') AS "Tyre Brands",
                COALESCE(items.patterns, '') AS "Pattern / Models",
                COALESCE(items.sizes, '') AS "Tyre Sizes"
            FROM sales s
            LEFT JOIN (
                SELECT
                    sale_id,
                    STRING_AGG(
                        brand || ' ' ||
                        CASE
                            WHEN COALESCE(pattern_model, '') = '' THEN ''
                            ELSE pattern_model || ' '
                        END ||
                        size || ' x ' || quantity_sold::text,
                        '; '
                        ORDER BY id
                    ) AS items_sold,
                    STRING_AGG(DISTINCT brand, ', ') AS brands,
                    STRING_AGG(DISTINCT COALESCE(pattern_model, ''), ', ') AS patterns,
                    STRING_AGG(DISTINCT size, ', ') AS sizes
                FROM sale_items
                WHERE business_id = ?
                    AND COALESCE(item_status, 'Active') = 'Active'
                GROUP BY sale_id
            ) items ON items.sale_id = s.id
            {where_clause}
            ORDER BY
                CASE WHEN COALESCE(s.promised_payment_date, '') = '' THEN 1 ELSE 0 END,
                s.promised_payment_date,
                s.sale_date DESC,
                s.id DESC
            """,
            [WALK_IN_CUSTOMER, WALK_IN_CUSTOMER, business_id, business_id] + params[3:],
        )

    return run_query(
        f"""
        SELECT
            s.id AS "Sale ID",
            s.invoice_number AS "Invoice Number",
            s.sale_date AS "Sale Date",
            COALESCE(s.customer_type, ?) AS "Customer Type",
            COALESCE(s.customer_name, ?) AS "Customer Name",
            COALESCE(s.phone, '') AS "Phone Number",
            COALESCE(s.total_amount, 0) AS "Total Amount",
            COALESCE(s.amount_paid, 0) AS "Amount Paid",
            COALESCE(s.balance, 0) AS "Outstanding Balance",
            COALESCE(s.promised_payment_date, '') AS "Promised Payment Date",
            COALESCE(s.payment_status, '') AS "Payment Status",
            COALESCE(s.follow_up_note, '') AS "Follow-up Note",
            COALESCE(items.items_sold, '') AS "Items Sold",
            COALESCE(items.brands, '') AS "Tyre Brands",
            COALESCE(items.patterns, '') AS "Pattern / Models",
            COALESCE(items.sizes, '') AS "Tyre Sizes"
        FROM sales s
        LEFT JOIN (
            SELECT
                sale_id,
                GROUP_CONCAT(
                    brand || ' ' ||
                    CASE
                        WHEN COALESCE(pattern_model, '') = '' THEN ''
                        ELSE pattern_model || ' '
                    END ||
                    size || ' x ' || quantity_sold,
                    '; '
                ) AS items_sold,
                GROUP_CONCAT(DISTINCT brand) AS brands,
                GROUP_CONCAT(DISTINCT COALESCE(pattern_model, '')) AS patterns,
                GROUP_CONCAT(DISTINCT size) AS sizes
            FROM sale_items
            WHERE business_id = ?
                AND COALESCE(item_status, 'Active') = 'Active'
            GROUP BY sale_id
        ) items ON items.sale_id = s.id
        {where_clause}
        ORDER BY
            CASE WHEN COALESCE(s.promised_payment_date, '') = '' THEN 1 ELSE 0 END,
            s.promised_payment_date,
            s.sale_date DESC,
            s.id DESC
        """,
        [WALK_IN_CUSTOMER, WALK_IN_CUSTOMER, business_id, business_id] + params[3:],
    )


def get_payment_history_dataframe(sale_id):
    business_id = current_business_id()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COALESCE(total_amount, 0)
        FROM sales
        WHERE id = ? AND business_id = ?
        """,
        (sale_id, business_id),
    )
    sale = cursor.fetchone()
    if not sale:
        conn.close()
        return pd.DataFrame()

    total_amount = float(sale[0] or 0)
    payments_df = run_query(
        """
        SELECT
            id,
            payment_date,
            payment_method,
            amount_paid,
            COALESCE(payment_note, '') AS payment_note
        FROM payments
        WHERE sale_id = ?
            AND business_id = ?
            AND COALESCE(payment_status, 'Active') = 'Active'
        ORDER BY payment_date, id
        """,
        (sale_id, business_id),
    )
    conn.close()

    if payments_df.empty:
        return payments_df

    running_total = 0.0
    remaining_balances = []
    running_totals = []
    for amount in payments_df["amount_paid"]:
        running_total += float(amount or 0)
        running_totals.append(running_total)
        remaining_balances.append(max(total_amount - running_total, 0.0))

    payments_df["running_total_paid"] = running_totals
    payments_df["remaining_balance"] = remaining_balances
    return payments_df.rename(
        columns={
            "id": "Payment ID",
            "payment_date": "Payment Date",
            "payment_method": "Payment Method",
            "amount_paid": "Amount Paid",
            "payment_note": "Payment Note / Reference",
            "running_total_paid": "Running Total Paid",
            "remaining_balance": "Remaining Balance",
        }
    )


def get_all_payment_history_dataframe():
    business_id = current_business_id()
    return run_query(
        """
        SELECT
            p.id AS "Payment ID",
            s.id AS "Sale ID",
            COALESCE(s.invoice_number, '') AS "Invoice Number",
            COALESCE(s.customer_name, ?) AS "Customer Name",
            COALESCE(s.phone, '') AS "Phone Number",
            p.payment_date AS "Payment Date",
            p.payment_method AS "Payment Method",
            p.amount_paid AS "Amount Paid",
            COALESCE(p.payment_note, '') AS "Payment Note / Reference"
        FROM payments p
        JOIN sales s ON s.id = p.sale_id
        WHERE p.business_id = ?
            AND s.business_id = ?
            AND COALESCE(p.payment_status, 'Active') = 'Active'
            AND COALESCE(s.sale_status, 'Active') = 'Active'
        ORDER BY p.payment_date DESC, p.id DESC
        """,
        (WALK_IN_CUSTOMER, business_id, business_id),
    )


def filter_dataframe_by_search(df, search_value):
    if df.empty or not search_value.strip():
        return df
    search_text = search_value.strip().lower()
    combined = df.fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    return df[combined.str.contains(search_text, regex=False)]


def filter_dataframe_by_date_range(df, column_name, start_date=None, end_date=None):
    if df.empty or column_name not in df.columns:
        return df
    filtered_df = df.copy()
    dates = pd.to_datetime(filtered_df[column_name], errors="coerce")
    if start_date:
        filtered_df = filtered_df[dates >= pd.to_datetime(str(start_date))]
        dates = dates.loc[filtered_df.index]
    if end_date:
        filtered_df = filtered_df[dates <= pd.to_datetime(str(end_date))]
    return filtered_df


def show_payment_history(sale_id, label, allow_delete=False):
    with st.expander(f"Payment History - {label}"):
        history_df = get_payment_history_dataframe(sale_id)
        if history_df.empty:
            st.info("No payments recorded for this sale yet.")
        else:
            payment_search = st.text_input(
                "Search this payment history",
                placeholder="Example: Cash, Bank Transfer, 2026-06-25, 50000, transfer ref",
                key=f"payment_history_search_{sale_id}",
            )
            visible_history_df = filter_dataframe_by_search(history_df, payment_search)
            add_csv_download(
                "Download this payment history CSV",
                visible_history_df,
                f"payment-history-{sale_id}.csv",
                hidden_columns=["Payment ID"],
            )
            show_money_dataframe(visible_history_df.drop(columns=["Payment ID"]), width="stretch")

            if allow_delete:
                st.subheader("Delete Wrong Payment")
                payment_options = {}
                for _, row in history_df.iterrows():
                    payment_id = int(row["Payment ID"])
                    label_text = (
                        f"{row['Payment Date']} | {row['Payment Method']} | "
                        f"{format_currency(row['Amount Paid'])}"
                    )
                    payment_options[label_text] = payment_id

                selected_payment = st.selectbox(
                    "Select payment to delete",
                    list(payment_options.keys()),
                    key=f"delete_payment_select_{sale_id}",
                )
                confirm_payment_delete = st.checkbox(
                    "I understand this payment record will be removed and the outstanding balance will be recalculated.",
                    key=f"confirm_delete_payment_{sale_id}",
                )
                delete_payment_text = st.text_input(
                    "Type DELETE to confirm payment removal",
                    key=f"delete_payment_text_{sale_id}",
                )
                if st.button(
                    "Delete selected payment",
                    key=f"delete_payment_button_{sale_id}",
                    disabled=not confirm_payment_delete or delete_payment_text != "DELETE",
                ):
                    success, message = delete_payment(payment_options[selected_payment])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)


def show_outstanding_balances():
    render_page_header("Outstanding Balances", "Track unpaid and part-paid invoices that need follow-up.")
    customer_suggestions = get_business_customer_suggestions()

    render_widget_label("Filter outstanding balances")
    filter_option = st.radio(
        "Filter outstanding balances",
        ["All", "Due today", "Overdue", "Upcoming", "Part Payment", "Unpaid"],
        horizontal=True,
        label_visibility="collapsed",
    )
    outstanding_df = get_outstanding_balances_dataframe(filter_option)
    render_widget_label("Search outstanding balances")
    search_term = suggestion_input(
        "Search outstanding balances",
        unique_suggestions(customer_suggestions["names"] + customer_suggestions["phones"]),
        "outstanding_search",
        placeholder="Type or choose a customer name or phone",
        label_visibility="collapsed",
    )

    with st.expander("Date filters"):
        col1, col2 = st.columns(2)
        use_sale_date_filter = col1.checkbox("Filter by sale date")
        use_promised_date_filter = col2.checkbox("Filter by promised payment date")

        sale_from = sale_to = promised_from = promised_to = None
        if use_sale_date_filter:
            sale_col1, sale_col2 = st.columns(2)
            sale_from = sale_col1.date_input("Sale date from", value=date.today())
            sale_to = sale_col2.date_input("Sale date to", value=date.today())
        if use_promised_date_filter:
            promised_col1, promised_col2 = st.columns(2)
            promised_from = promised_col1.date_input("Promised payment date from", value=date.today())
            promised_to = promised_col2.date_input("Promised payment date to", value=date.today())

    outstanding_df = filter_dataframe_by_search(outstanding_df, search_term)
    outstanding_df = filter_dataframe_by_date_range(outstanding_df, "Sale Date", sale_from, sale_to)
    outstanding_df = filter_dataframe_by_date_range(
        outstanding_df,
        "Promised Payment Date",
        promised_from,
        promised_to,
    )

    if outstanding_df.empty:
        if filter_option == "All" and not search_term.strip():
            st.info("No outstanding balances right now.")
        else:
            st.info("No outstanding balances match this filter.")
        return

    add_csv_download(
        "Download outstanding balances CSV",
        outstanding_df,
        "outstanding-balances.csv",
        hidden_columns=["Sale ID"],
    )
    show_money_dataframe(outstanding_df.drop(columns=["Sale ID"]), width="stretch")

    render_section("Record Balance Payment", "Choose an invoice and save a follow-up payment.")
    sale_options = {}
    for _, row in outstanding_df.iterrows():
        sale_id = int(row["Sale ID"])
        invoice_number = row["Invoice Number"]
        customer_name = row["Customer Name"]
        balance = row["Outstanding Balance"]
        label = f"{invoice_number} | {customer_name} | Balance {format_currency(balance)}"
        sale_options[label] = sale_id

    selected_sale_label = st.selectbox("Select sale / invoice with outstanding balance", list(sale_options.keys()))
    selected_sale_id = sale_options[selected_sale_label]
    selected_row = outstanding_df[outstanding_df["Sale ID"] == selected_sale_id].iloc[0]

    balance_cols = st.columns(3)
    with balance_cols[0]:
        render_metric_card("Current Total Amount", format_currency(selected_row["Total Amount"]), tone="gold")
    with balance_cols[1]:
        render_metric_card("Amount Paid", format_currency(selected_row["Amount Paid"]))
    with balance_cols[2]:
        render_metric_card("Balance", format_currency(selected_row["Outstanding Balance"]), tone="warning")

    with st.form("record_balance_payment_form"):
        col1, col2, col3 = st.columns(3)
        later_payment_date = col1.date_input("New payment date", value=date.today())
        later_payment_method = col2.selectbox("New payment method", PAYMENT_METHODS)
        later_payment_amount_input = col3.text_input(
            "New payment amount",
            placeholder="Example: 50000, 50,000, or ₦50,000",
        )
        later_payment_amount = parse_naira_input(later_payment_amount_input)
        if later_payment_amount is None:
            st.warning("Enter a valid payment amount, for example 50000, 50,000, or ₦50,000.")
        else:
            st.caption(f"New payment amount: {format_naira(later_payment_amount)}")
        later_payment_note = st.text_input("Payment note / reference")
        save_later_payment = st.form_submit_button("Save Payment")

    if save_later_payment:
        if later_payment_amount is None:
            st.error("Please enter a valid payment amount.")
        elif later_payment_amount <= 0:
            st.error("Enter a payment amount greater than zero.")
        else:
            success, message = record_followup_payment(
                selected_sale_id,
                later_payment_date,
                later_payment_method,
                float(later_payment_amount),
                later_payment_note,
            )
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    show_payment_history(selected_sale_id, selected_sale_label)


def show_sales_report():
    render_page_header("Sales Report", "Review sales, payment history, profit, and cancelled records.")

    sales_df = get_sales_report_dataframe()

    if sales_df.empty:
        st.info("No sales have been recorded yet.")
    else:
        customer_suggestions = get_business_customer_suggestions()
        search_term = suggestion_input(
            "Search sales",
            unique_suggestions(customer_suggestions["names"] + customer_suggestions["phones"]),
            "sales_report_search",
            placeholder="Type or choose a customer name or phone",
        )
        col1, col2 = st.columns(2)
        status_filter = col1.selectbox("Payment status", ["Any", "Paid", "Part Payment", "Unpaid"])
        method_filter = col2.selectbox("Payment method", ["Any"] + PAYMENT_METHODS)

        with st.expander("Sale date filter"):
            use_sale_date_filter = st.checkbox("Filter sales by date")
            report_sale_from = report_sale_to = None
            if use_sale_date_filter:
                date_col1, date_col2 = st.columns(2)
                report_sale_from = date_col1.date_input("Sale report date from", value=date.today())
                report_sale_to = date_col2.date_input("Sale report date to", value=date.today())

        filtered_sales_df = filter_dataframe_by_search(sales_df, search_term)
        if status_filter != "Any":
            filtered_sales_df = filtered_sales_df[filtered_sales_df["Payment Status"] == status_filter]
        if method_filter != "Any":
            method_text = filtered_sales_df["Payment Methods Used"].fillna("").astype(str)
            filtered_sales_df = filtered_sales_df[method_text.str.contains(method_filter, case=False, regex=False)]
        filtered_sales_df = filter_dataframe_by_date_range(
            filtered_sales_df,
            "Date",
            report_sale_from,
            report_sale_to,
        )

        if filtered_sales_df.empty:
            st.info("No sales match this search or filter.")
        else:
            hidden_columns = ["Sale ID", "Sale Status", "Cancellation Reason", "Cancelled At"]
            add_csv_download(
                "Download sales report CSV",
                filtered_sales_df,
                "sales-report.csv",
                hidden_columns=hidden_columns,
            )
            show_money_dataframe(filtered_sales_df.drop(columns=hidden_columns), width="stretch")

        render_section("Payment History", "All active payment records across invoices.")
        payment_history_df = get_all_payment_history_dataframe()
        payment_search = st.text_input(
            "Search all payment records",
            placeholder="Example: customer, phone, invoice, payment date, Cash, amount, note/reference",
        )
        visible_payment_history_df = filter_dataframe_by_search(payment_history_df, payment_search)
        if visible_payment_history_df.empty:
            st.info("No payment records match this search.")
        else:
            add_csv_download(
                "Download payment history CSV",
                visible_payment_history_df,
                "payment-history.csv",
                hidden_columns=["Payment ID", "Sale ID"],
            )
            show_money_dataframe(visible_payment_history_df.drop(columns=["Payment ID", "Sale ID"]), width="stretch")

        invoice_options = {}
        sales_lookup_df = run_query(
            """
            SELECT id, invoice_number, COALESCE(customer_name, ?) AS customer_name
            FROM sales
            WHERE business_id = ?
                AND COALESCE(sale_status, 'Active') = 'Active'
            ORDER BY sale_date DESC, id DESC
            """,
            (WALK_IN_CUSTOMER, current_business_id()),
        )
        for row in sales_lookup_df.itertuples(index=False):
            label = f"{row.invoice_number} | {row.customer_name}"
            invoice_options[label] = int(row.id)
        if invoice_options:
            selected_invoice = st.selectbox("Select invoice for detailed payment history", list(invoice_options.keys()))
            selected_sale_id = invoice_options[selected_invoice]
            show_payment_history(selected_sale_id, selected_invoice, allow_delete=True)

            render_section("Cancel/Delete This Sale", "Use this only for sales that were recorded by mistake.")
            st.warning(
                "Only use this for a sale recorded by mistake. The sale will be marked Cancelled, "
                "payments will be marked Cancelled, and sold tyre quantities will be restored to stock."
            )
            with st.expander("Cancel/Delete selected sale"):
                cancellation_reason = st.text_area(
                    "Cancellation reason",
                    placeholder="Example: Sale entered by mistake",
                    key=f"cancel_reason_{selected_sale_id}",
                )
                confirm_cancel_sale = st.checkbox(
                    "I understand this will cancel/delete this sale and update stock records.",
                    key=f"confirm_cancel_sale_{selected_sale_id}",
                )
                delete_text = st.text_input(
                    "Type DELETE to confirm",
                    key=f"cancel_delete_text_{selected_sale_id}",
                )
                if st.button(
                    "Cancel/Delete This Sale",
                    key=f"cancel_sale_button_{selected_sale_id}",
                    disabled=not confirm_cancel_sale or delete_text != "DELETE",
                ):
                    success, message = cancel_sale(selected_sale_id, cancellation_reason)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    cancelled_sales_df = get_sales_report_dataframe(sale_status="Cancelled")
    if not cancelled_sales_df.empty:
        render_section("Cancelled Sales", "Cancelled sales are kept for audit only.")
        st.caption("Cancelled sales are kept for audit only and do not count in dashboard totals, revenue, profit, or outstanding balances.")
        show_money_dataframe(cancelled_sales_df.drop(columns=["Sale ID"]), width="stretch")


def show_business_settings():
    settings = get_business_settings()
    render_page_header("Business Settings", "Customize the business details shown across the app and receipts.")

    with st.form("business_settings_form"):
        render_section("Business Details", "These details appear in the sidebar, dashboard, and receipt summary.")
        business_name = st.text_input("Business name", value=settings["business_name"])
        business_phone = st.text_input("Business phone / WhatsApp", value=settings["business_phone"])
        country = country_selectbox("Country", saved_country=settings["country"], key="settings_country")
        business_address = st.text_area("Business address", value=settings["business_address"])

        render_section("Alerts And Receipt", "Control low-stock alerts and the receipt footer message.")
        low_stock_alert_level = st.number_input(
            "Low stock alert level",
            min_value=1,
            value=int(settings["low_stock_alert_level"]),
            step=1,
        )
        receipt_footer = st.text_area("Receipt footer message", value=settings["receipt_footer"])
        submitted = st.form_submit_button("Save Business Settings")

    if submitted:
        if not country:
            st.error("Please select your country before saving business settings.")
        else:
            save_business_settings(
                business_name,
                business_phone,
                business_address,
                country,
                int(low_stock_alert_level),
                receipt_footer,
            )
            st.success("Business settings saved.")
            st.rerun()


def show_help_page():
    render_page_header("Help / How to Use", "Simple guide for running your tyre business in the app.")
    render_section("Add Stock", "Go to Add Stock, enter the tyre details, quantity, buying price, selling price, and supplier, then save.")
    st.markdown("- Add all tyres currently in your shop first.\n- Use clear brand, size, and pattern/model names so searching is easy.")

    render_section("View Or Search Stock", "Use View Stock to see everything, or Search Tyres to quickly find tyres for a customer.")
    st.markdown("- Search by size, brand, pattern/model, or condition.\n- Low quantities will appear on the Low Stock Items page.")

    render_section("Record A Sale", "Open Record Sale, select tyre items, add them to the cart, enter customer details, then add payment details.")
    st.markdown("- You can sell more than one tyre item in the same sale.\n- Check the sale summary before saving.")

    render_section("Part Payments", "If a customer pays only part of the amount, enter the amount paid and save the sale.")
    st.markdown("- The app will keep the remaining balance as outstanding.\n- Later payments can be added from Outstanding Balances.")

    render_section("Outstanding Balances", "Use this page to see customers who still owe money.")
    st.markdown("- Filter by overdue, upcoming, part payment, or unpaid.\n- Select an invoice and record follow-up payments.")

    render_section("Low Stock Items", "This page shows tyres at or below your low-stock alert level.")
    st.markdown("- Change the alert level from Business Settings.\n- Download the low-stock list when you need to restock.")

    render_section("Download Reports", "Use CSV download buttons on stock, sales, outstanding balances, low stock, and payment history pages.")
    st.markdown("- CSV files can be opened in Excel or Google Sheets.")

    render_section("Business Settings", "Update your business name, phone, country, address, low-stock level, and receipt footer.")

    render_section("Support / Contact", "Use these details if you need help with the app.")
    support_email, support_whatsapp = get_support_contacts()
    if support_email or support_whatsapp:
        support_lines = []
        if support_email:
            support_lines.append(f"Support email: {support_email}")
        if support_whatsapp:
            support_lines.append(f"Support WhatsApp: {support_whatsapp}")
        st.info("\n\n".join(support_lines))
    else:
        st.info(SUPPORT_CONTACT_NOT_CONFIGURED)


def show_terms_page():
    render_page_header("Terms of Use", "Simple terms for using Tyre Stock Manager.")
    st.markdown(
        """
        - Tyre Stock Manager helps tyre businesses manage stock, sales, payments, outstanding balances, and reports.
        - Users are responsible for entering accurate business, stock, customer, sales, and payment information.
        - Users must keep their login details safe and must not share accounts with unauthorized people.
        - The platform owner may suspend accounts that misuse the platform or create risk for other users.
        - This app is a basic operational/business tool. It is not financial, tax, accounting, or legal advice.
        - By creating an account, you agree to use the app responsibly and keep your information accurate.
        """
    )


def show_privacy_page():
    render_page_header("Privacy Policy", "How business data is handled in Tyre Stock Manager.")
    st.markdown(
        """
        - The app stores business registration details such as business name, owner name, email, phone, country, and account status.
        - The app stores stock, sales, customer, payment, outstanding balance, report, and business settings data entered by each business.
        - Each normal business account can only see its own business data.
        - The platform owner can view platform and business information for support, safety, and management.
        - Login passwords for normal business users are stored as secure hashes, not plain text.
        - Database credentials and secrets must be kept in Streamlit secrets or environment variables, never hard-coded into the app.
        """
    )


def get_platform_summary():
    businesses_df = run_query(
        """
        SELECT
            COUNT(*) AS total_count,
            SUM(CASE WHEN COALESCE(status, 'active') = 'active' THEN 1 ELSE 0 END) AS active_count,
            SUM(CASE WHEN COALESCE(status, 'active') = 'suspended' THEN 1 ELSE 0 END) AS suspended_count
        FROM businesses
        """
    )
    users_df = run_query("SELECT COUNT(*) AS count FROM users")
    stock_df = run_query("SELECT COUNT(*) AS count FROM stock WHERE business_id IS NOT NULL")
    sales_df = run_query(
        """
        SELECT
            COUNT(*) AS sales_count,
            COALESCE(SUM(total_amount), 0) AS sales_value,
            COALESCE(SUM(balance), 0) AS outstanding_balance
        FROM sales
        WHERE COALESCE(sale_status, 'Active') = 'Active'
            AND business_id IS NOT NULL
        """
    )
    return {
        "businesses": int(businesses_df.iloc[0]["total_count"] or 0),
        "active_businesses": int(businesses_df.iloc[0]["active_count"] or 0),
        "suspended_businesses": int(businesses_df.iloc[0]["suspended_count"] or 0),
        "users": int(users_df.iloc[0]["count"] or 0),
        "stock_records": int(stock_df.iloc[0]["count"] or 0),
        "sales_count": int(sales_df.iloc[0]["sales_count"] or 0),
        "sales_value": float(sales_df.iloc[0]["sales_value"] or 0),
        "outstanding_balance": float(sales_df.iloc[0]["outstanding_balance"] or 0),
    }


def get_platform_businesses_dataframe():
    return run_query(
        """
        SELECT
            b.id AS "Business ID",
            b.business_name AS "Business Name",
            b.owner_full_name AS "Owner Name",
            b.email AS "Email",
            COALESCE(b.phone, '') AS "Phone / WhatsApp",
            COALESCE(b.country, '') AS "Country",
            b.created_at AS "Date Registered",
            COALESCE(b.status, 'active') AS "Status",
            COALESCE(stock_counts.stock_items, 0) AS "Inventory Items",
            COALESCE(stock_counts.total_tyres, 0) AS "Total Tyres in Stock",
            COALESCE(stock_counts.low_stock_items, 0) AS "Low Stock Items",
            COALESCE(sales_counts.sales_count, 0) AS "Sales Recorded",
            COALESCE(sales_counts.total_sales_value, 0) AS "Total Sales Value",
            COALESCE(sales_counts.outstanding_balance, 0) AS "Outstanding Balance",
            COALESCE(activity.last_activity, '') AS "Last Activity"
        FROM businesses b
        LEFT JOIN (
            SELECT
                s.business_id,
                COUNT(*) AS stock_items,
                COALESCE(SUM(s.quantity), 0) AS total_tyres,
                COALESCE(SUM(
                    CASE
                        WHEN s.quantity <= COALESCE(bs.low_stock_alert_level, ?) THEN 1
                        ELSE 0
                    END
                ), 0) AS low_stock_items
            FROM stock s
            LEFT JOIN business_settings bs ON bs.business_id = s.business_id
            GROUP BY s.business_id
        ) stock_counts ON stock_counts.business_id = b.id
        LEFT JOIN (
            SELECT
                business_id,
                COUNT(*) AS sales_count,
                COALESCE(SUM(total_amount), 0) AS total_sales_value,
                COALESCE(SUM(balance), 0) AS outstanding_balance
            FROM sales
            WHERE COALESCE(sale_status, 'Active') = 'Active'
            GROUP BY business_id
        ) sales_counts ON sales_counts.business_id = b.id
        LEFT JOIN (
            SELECT business_id, MAX(activity_date) AS last_activity
            FROM (
                SELECT business_id, created_at AS activity_date FROM sales
                UNION ALL
                SELECT business_id, created_at AS activity_date FROM payments
                UNION ALL
                SELECT business_id, date_added AS activity_date FROM stock
            ) activity_rows
            WHERE business_id IS NOT NULL
            GROUP BY business_id
        ) activity ON activity.business_id = b.id
        ORDER BY b.created_at DESC, b.id DESC
        """,
        (LOW_STOCK_LIMIT,),
    )


def update_business_status(business_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE businesses
        SET status = ?
        WHERE id = ?
        """,
        (status, int(business_id)),
    )
    conn.commit()
    conn.close()


def delete_business_account(business_id):
    conn = get_connection()
    cursor = conn.cursor()
    business_id = int(business_id)
    try:
        cursor.execute("DELETE FROM payments WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM sale_items WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM sales WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM customers WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM stock WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM business_settings WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM users WHERE business_id = ?", (business_id,))
        cursor.execute("DELETE FROM businesses WHERE id = ?", (business_id,))
        conn.commit()
        return True, "Business account and its data have been deleted."
    except Exception as error:
        conn.rollback()
        return False, str(error)
    finally:
        conn.close()


def show_platform_dashboard():
    render_page_header("Platform Dashboard", "Owner overview across all tyre businesses on the platform.")
    summary = get_platform_summary()
    render_section("Platform Overview", "High-level usage across all registered businesses.")
    cols = st.columns(3)
    with cols[0]:
        render_metric_card("Registered Businesses", summary["businesses"])
    with cols[1]:
        render_metric_card("Active Businesses", summary["active_businesses"])
    with cols[2]:
        render_metric_card("Suspended Businesses", summary["suspended_businesses"], tone="warning")

    cols = st.columns(3)
    with cols[0]:
        render_metric_card("Registered Users", summary["users"])
    with cols[1]:
        render_metric_card("Inventory Items", summary["stock_records"])
    with cols[2]:
        render_metric_card("Sales Recorded", summary["sales_count"])

    render_section("Business Insight", "Select one business to view its own platform summary.")
    businesses_df = get_platform_businesses_dataframe()
    if businesses_df.empty:
        st.info("No businesses have registered yet.")
        return

    business_options = {
        f"{row['Business Name']} | {row['Email']} | {row['Status']}": int(row["Business ID"])
        for _, row in businesses_df.iterrows()
    }
    selected_business = st.selectbox("Select business", list(business_options.keys()))
    selected_business_id = business_options[selected_business]
    row = businesses_df[businesses_df["Business ID"] == selected_business_id].iloc[0]

    info_cols = st.columns(3)
    with info_cols[0]:
        render_metric_card("Business Name", row["Business Name"])
    with info_cols[1]:
        render_metric_card("Owner Name", row["Owner Name"])
    with info_cols[2]:
        render_metric_card("Status", row["Status"], tone="warning" if row["Status"] == "suspended" else "")

    info_cols = st.columns(3)
    with info_cols[0]:
        render_metric_card("Email", row["Email"])
    with info_cols[1]:
        render_metric_card("Phone / WhatsApp", row["Phone / WhatsApp"] or "Not set")
    with info_cols[2]:
        render_metric_card("Country", row["Country"] or "Not set")

    info_cols = st.columns(4)
    with info_cols[0]:
        render_metric_card("Inventory Items", int(row["Inventory Items"]))
    with info_cols[1]:
        render_metric_card("Total Tyres in Stock", int(row["Total Tyres in Stock"]))
    with info_cols[2]:
        render_metric_card("Sales Recorded", int(row["Sales Recorded"]))
    with info_cols[3]:
        render_metric_card("Low Stock Items", int(row["Low Stock Items"]), tone="warning")

    info_cols = st.columns(4)
    with info_cols[0]:
        render_metric_card("Total Sales Value", format_currency(row["Total Sales Value"]), tone="gold")
    with info_cols[1]:
        render_metric_card("Outstanding Balance", format_currency(row["Outstanding Balance"]), tone="warning")
    with info_cols[2]:
        render_metric_card("Date Registered", row["Date Registered"])
    with info_cols[3]:
        render_metric_card("Last Activity", row["Last Activity"] or "No activity yet")


def show_platform_businesses():
    render_page_header("Businesses", "Manage registered tyre businesses and account status.")
    businesses_df = get_platform_businesses_dataframe()
    if businesses_df.empty:
        st.info("No businesses have registered yet.")
        return

    table_columns = [
        "Business Name",
        "Owner Name",
        "Email",
        "Phone / WhatsApp",
        "Country",
        "Date Registered",
        "Status",
        "Inventory Items",
        "Sales Recorded",
        "Last Activity",
    ]
    table_df = businesses_df[["Business ID"] + table_columns]
    add_csv_download("Download businesses CSV", table_df, "platform-businesses.csv", hidden_columns=["Business ID"])
    show_money_dataframe(table_df.drop(columns=["Business ID"]), width="stretch")

    render_section("Suspend Or Reactivate Business", "Suspended businesses cannot log in until reactivated.")
    business_options = {
        f"{row['Business Name']} | {row['Email']} | {row['Status']}": int(row["Business ID"])
        for _, row in businesses_df.iterrows()
    }
    selected_business = st.selectbox("Select business", list(business_options.keys()))
    selected_business_id = business_options[selected_business]
    selected_row = businesses_df[businesses_df["Business ID"] == selected_business_id].iloc[0]
    current_status = selected_row["Status"]

    if current_status == "active":
        confirm_suspend = st.checkbox("I understand this business will be unable to log in.")
        suspend_text = st.text_input("Type SUSPEND to confirm")
        if st.button(
            "Suspend Business",
            type="primary",
            disabled=not confirm_suspend or suspend_text != "SUSPEND",
        ):
            update_business_status(selected_business_id, "suspended")
            st.success("Business suspended.")
            st.rerun()
    else:
        confirm_reactivate = st.checkbox("I understand this business will regain access.")
        reactivate_text = st.text_input("Type REACTIVATE to confirm")
        if st.button("Reactivate Business", disabled=not confirm_reactivate or reactivate_text != "REACTIVATE"):
            update_business_status(selected_business_id, "active")
            st.success("Business reactivated.")
            st.rerun()

    render_section("Delete Test Business Account", "Platform owner only. Use this for test/demo accounts that should be removed.")
    st.warning(
        "Deleting a business will delete its stock, sales, payments, reports, settings, users, and business account. "
        "This cannot be undone."
    )
    confirm_delete_business = st.checkbox(
        "I understand this will permanently delete the selected business and all its data.",
        key=f"confirm_delete_business_{selected_business_id}",
    )
    delete_business_text = st.text_input(
        "Type DELETE to permanently delete this business",
        key=f"delete_business_text_{selected_business_id}",
    )
    if st.button(
        "Delete Business Account",
        type="primary",
        disabled=not confirm_delete_business or delete_business_text != "DELETE",
    ):
        success, message = delete_business_account(selected_business_id)
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)


def show_platform_owner_app():
    st.sidebar.markdown(
        f"""
        <div class="sidebar-brand">
            <div class="title">🛞 Platform Owner</div>
            <div class="subtitle">{escape(APP_NAME)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_nav = st.sidebar.selectbox("Owner navigation", list(OWNER_NAV_ITEMS.keys()), label_visibility="collapsed")
    page = OWNER_NAV_ITEMS[selected_nav]
    st.sidebar.markdown("---")
    st.sidebar.caption("Platform workspace")
    if st.sidebar.button("Logout"):
        for key in [
            "logged_in",
            "authenticated",
            "login_role",
            "role",
            "user_id",
            "business_id",
            "business_name",
            "user_email",
            "user_name",
            "sale_cart",
            "sale_payments",
            "last_receipt",
            "show_new_account_welcome",
        ]:
            st.session_state.pop(key, None)
        st.rerun()

    if page == "Platform Dashboard":
        show_platform_dashboard()
    elif page == "Businesses":
        show_platform_businesses()


def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🛞", layout="wide")
    inject_app_styles()
    create_tables()

    if not require_login():
        return
    if st.session_state.get("login_role") == "owner":
        show_platform_owner_app()
        return

    settings = get_business_settings()

    st.sidebar.markdown(
        f"""
        <div class="sidebar-brand">
            <div class="title">🛞 {escape(settings["business_name"])}</div>
            <div class="subtitle">{escape(APP_SUBTITLE)}</div>
            <div class="subtitle">{escape(APP_NAME)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_nav = st.sidebar.selectbox("Navigation", list(PAGE_NAV_ITEMS.keys()), label_visibility="collapsed")
    page = PAGE_NAV_ITEMS[selected_nav]

    st.sidebar.markdown("---")
    st.sidebar.caption("Business workspace")
    render_support_sidebar()

    st.sidebar.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    if st.sidebar.button("Logout"):
        for key in [
            "logged_in",
            "authenticated",
            "login_role",
            "role",
            "user_id",
            "business_id",
            "business_name",
            "user_email",
            "user_name",
            "sale_cart",
            "sale_payments",
            "last_receipt",
            "show_new_account_welcome",
        ]:
            st.session_state.pop(key, None)
        st.rerun()

    if page == "Dashboard":
        show_dashboard()
    elif page == "Add Stock":
        show_add_stock()
    elif page == "View Stock":
        show_all_stock()
    elif page == "Low Stock Items":
        show_low_stock_items()
    elif page == "Search Tyres":
        show_search()
    elif page == "Record Sale":
        show_record_sale()
    elif page == "Outstanding Balances":
        show_outstanding_balances()
    elif page == "Sales Report":
        show_sales_report()
    elif page == "Business Settings":
        show_business_settings()
    elif page == "Help / How to Use":
        show_help_page()
    elif page == "Terms of Use":
        show_terms_page()
    elif page == "Privacy Policy":
        show_privacy_page()


if __name__ == "__main__":
    main()
