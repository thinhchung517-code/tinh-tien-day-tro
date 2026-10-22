import sqlite3
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# =========================================================
# CẤU HÌNH ỨNG DỤNG
# =========================================================
st.set_page_config(
    page_title="Quản lý tiền phòng trọ",
    page_icon="🏠",
    layout="wide",
)

DB_PATH = Path(__file__).with_name("quan_ly_tien_tro.db")
DEFAULTS = {
    "gia_dien": 3500,
    "gia_nuoc": 15000,
    "phi_khac": 150000,
    "so_phong": 10,
}


# =========================================================
# SQLITE
# =========================================================
def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS room_monthly (
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                room_number INTEGER NOT NULL,
                tenant_name TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                rent INTEGER NOT NULL DEFAULT 2500000,
                electric_old INTEGER NOT NULL DEFAULT 0,
                electric_new INTEGER NOT NULL DEFAULT 0,
                water_old INTEGER NOT NULL DEFAULT 0,
                water_new INTEGER NOT NULL DEFAULT 0,
                payment_status TEXT NOT NULL DEFAULT 'Chưa thanh toán',
                note TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (year, month, room_number)
            )
        """)
        for key, value in DEFAULTS.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(setting_key, setting_value) VALUES (?, ?)",
                (key, str(value)),
            )


def get_setting(key):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT setting_value FROM settings WHERE setting_key = ?", (key,)
        ).fetchone()
    return row["setting_value"] if row else str(DEFAULTS[key])


def set_setting(key, value):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO settings(setting_key, setting_value) VALUES (?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
        """, (key, str(value)))


def fetch_room(year, month, room_number):
    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM room_monthly
            WHERE year = ? AND month = ? AND room_number = ?
