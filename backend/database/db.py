import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parents[2] / "brandshield.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes all necessary tables for BrandShield and seeds demo data."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Users table (if not exists)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Organizations / Brand Profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                industry TEXT,
                tagline TEXT,
                description TEXT,
                website TEXT,
                tone_of_voice TEXT,
                target_audience TEXT,
                primary_color TEXT DEFAULT '#8955D9',
                secondary_color TEXT DEFAULT '#D0B7FF',
                accent_color TEXT DEFAULT '#1C1428',
                logo_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # 3. Brand Rules table (supports vector retrieval)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brand_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                rule_title TEXT NOT NULL,
                rule_description TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                is_enabled INTEGER DEFAULT 1,
                embedding TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)

        # Safely migrate existing tables if columns are missing
        try:
            cursor.execute("ALTER TABLE brand_rules ADD COLUMN is_enabled INTEGER DEFAULT 1")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE organizations ADD COLUMN preferred_phrases TEXT")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE organizations ADD COLUMN prohibited_phrases TEXT")
        except Exception:
            pass

        # 4. Guideline Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guideline_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT,
                file_size INTEGER,
                extracted_text TEXT,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)

        # 5. Analyses table (Content and Visual verification audits)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                target_channel TEXT,
                input_content TEXT,
                image_path TEXT,
                compliance_score INTEGER NOT NULL,
                status TEXT NOT NULL,
                corrected_content TEXT,
                summary TEXT,
                full_report_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # 6. Activity Logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER,
                user_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # 7. App Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()
        
        # Check and seed default demo data if organizations table is empty
        cursor.execute("SELECT COUNT(*) FROM organizations")
        if cursor.fetchone()[0] == 0:
            seed_demo_data(cursor)
            conn.commit()

def seed_demo_data(cursor):
    """Seeds a comprehensive demo brand profile with rules and sample activity."""
    # Find demo user id
    cursor.execute("SELECT id FROM users WHERE email = 'demo@brandshield.ai'")
    user_row = cursor.fetchone()
    demo_user_id = user_row["id"] if user_row else 1

    # Insert default BrandShield AI organization
    cursor.execute("""
        INSERT INTO organizations (
            user_id, name, industry, tagline, description, website,
            tone_of_voice, target_audience, primary_color, secondary_color, accent_color
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        demo_user_id,
        "BrandShield AI",
        "Artificial Intelligence & Cybersecurity",
        "Protect Your Identity. Every Asset. Every Detail.",
        "BrandShield provides enterprise-grade AI brand compliance, monitoring, and visual asset verification.",
        "https://brandshield.ai",
        "Authoritative, Visionary, Precise, Empowering",
        "Enterprise marketing teams, creative directors, and brand compliance officers",
        "#8955D9",  # BrandShield Signature Purple
        "#D0B7FF",  # Soft Lavender
        "#100C18"   # Deep Void Surface
    ))
    org_id = cursor.lastrowid

    # Seed core brand rules for BrandShield
    demo_rules = [
        (
            org_id,
            "Tone & Voice",
            "Maintain Authoritative and Direct Phrasing",
            "Avoid overly casual slang (e.g. 'gonna', 'wanna', 'super cool', 'insane deal'). Use clear, crisp, executive language.",
            "high"
        ),
        (
            org_id,
            "Prohibited Claims",
            "No Unverifiable Absolute Guarantees",
            "Do not use phrases like '100% hack-proof', 'zero risk guaranteed', or 'the only solution in the world'. Frame claims around reliability and continuous protection.",
            "high"
        ),
        (
            org_id,
            "Brand Naming",
            "Proper Capitalization of BrandShield",
            "BrandShield must always be written in CamelCase as 'BrandShield' or 'BRANDSHIELD'. Never write 'brandshield', 'Brandshield', or 'Brand Shield' with a space.",
            "high"
        ),
        (
            org_id,
            "Visual & Colors",
            "Strict Adherence to Cyber-Purple Palette",
            "Primary visuals must be grounded in BrandShield Purple (#8955D9), Lavender (#D0B7FF), or Deep Charcoal/Void (#100C18). Harsh neon greens or bright warm yellows are prohibited unless indicating status alerts.",
            "medium"
        ),
        (
            org_id,
            "Legal & Disclaimers",
            "Mandatory Trademark and Evaluation Notice",
            "Promotional offers, beta announcements, or feature releases must include: 'BrandShield is a registered trademark. Features subject to service availability.'",
            "medium"
        ),
        (
            org_id,
            "Typography & Slogans",
            "Official Slogan Usage",
            "When including the company slogan, use: 'Protect your identity. Every asset. Every detail.' Ensure correct punctuation.",
            "low"
        )
    ]

    for rule in demo_rules:
        cursor.execute("""
            INSERT INTO brand_rules (org_id, category, rule_title, rule_description, severity)
            VALUES (?, ?, ?, ?, ?)
        """, rule)

    # Seed sample past analyses for rich dashboard experience
    demo_analyses = [
        (
            org_id,
            demo_user_id,
            "Q4 Product Launch Press Release",
            "text",
            "Press Release",
            "brandshield announces 100% guaranteed brand safety solution that wipes out all competitors! Try our super cool AI now.",
            92,
            "Warning",
            "BrandShield announces an enterprise-grade brand safety platform engineered to safeguard digital identity. Explore our next-generation AI brand intelligence suite.",
            "Minor tone and capitalization violations detected. Prohibited absolute guarantee flagged.",
            json.dumps({
                "tone_score": 85,
                "vocab_score": 90,
                "visual_score": 100,
                "violations": [
                    {"category": "Brand Naming", "severity": "High", "issue": "Lowercase 'brandshield' used instead of 'BrandShield'.", "suggestion": "Capitalize as BrandShield."},
                    {"category": "Prohibited Claims", "severity": "High", "issue": "Phrase '100% guaranteed' violates claim guidelines.", "suggestion": "Use 'enterprise-grade assurance'."},
                    {"category": "Tone & Voice", "severity": "Medium", "issue": "'super cool' is too casual for enterprise PR.", "suggestion": "Replace with 'next-generation'."}
                ]
            })
        ),
        (
            org_id,
            demo_user_id,
            "Social Media Feature Spotlight",
            "text",
            "Social Media",
            "BrandShield ensures every asset aligns with your brand guidelines. Protect your identity. Every asset. Every detail.",
            98,
            "Passed",
            "BrandShield ensures every asset aligns with your brand guidelines. Protect your identity. Every asset. Every detail.",
            "Content is fully compliant with brand voice, approved naming, and slogan guidelines.",
            json.dumps({
                "tone_score": 100,
                "vocab_score": 98,
                "visual_score": 100,
                "violations": []
            })
        )
    ]

    for analysis in demo_analyses:
        cursor.execute("""
            INSERT INTO analyses (
                org_id, user_id, title, asset_type, target_channel, input_content,
                compliance_score, status, corrected_content, summary, full_report_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, analysis)

    # Seed sample activity logs
    demo_logs = [
        (org_id, demo_user_id, "PROFILE_CREATED", "Brand profile 'BrandShield AI' created"),
        (org_id, demo_user_id, "RULE_ADDED", "Added 6 core brand compliance rules"),
        (org_id, demo_user_id, "ANALYSIS_RUN", "Analyzed 'Social Media Feature Spotlight' (Score: 98%)"),
        (org_id, demo_user_id, "ANALYSIS_RUN", "Analyzed 'Q4 Product Launch Press Release' (Score: 92%)")
    ]

    for log in demo_logs:
        cursor.execute("""
            INSERT INTO activity_logs (org_id, user_id, action_type, description)
            VALUES (?, ?, ?, ?)
        """, log)

# Helper functions for database operations

def log_activity(user_id, action_type, description, org_id=None):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO activity_logs (org_id, user_id, action_type, description)
            VALUES (?, ?, ?, ?)
        """, (org_id, user_id, action_type, description))
        conn.commit()

def get_organizations(user_id=None):
    with get_connection() as conn:
        if user_id:
            cursor = conn.execute("SELECT * FROM organizations WHERE user_id = ? ORDER BY id ASC", (user_id,))
        else:
            cursor = conn.execute("SELECT * FROM organizations ORDER BY id ASC")
        return [dict(row) for row in cursor.fetchall()]

def get_organization_by_id(org_id):
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_organization_by_name(name):
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM organizations WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_organization(user_id, name, industry, tagline, description, website, tone_of_voice, target_audience, primary_color, secondary_color, accent_color):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO organizations (
                user_id, name, industry, tagline, description, website,
                tone_of_voice, target_audience, primary_color, secondary_color, accent_color
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, name, industry, tagline, description, website,
            tone_of_voice, target_audience, primary_color, secondary_color, accent_color
        ))
        org_id = cursor.lastrowid
        conn.commit()
        log_activity(user_id, "PROFILE_CREATED", f"Created brand profile '{name}'", org_id)
        return org_id

def update_organization(org_id, name, industry, tagline, description, website, tone_of_voice, target_audience, primary_color, secondary_color, accent_color):
    with get_connection() as conn:
        conn.execute("""
            UPDATE organizations SET
                name = ?, industry = ?, tagline = ?, description = ?, website = ?,
                tone_of_voice = ?, target_audience = ?, primary_color = ?,
                secondary_color = ?, accent_color = ?
            WHERE id = ?
        """, (
            name, industry, tagline, description, website,
            tone_of_voice, target_audience, primary_color, secondary_color, accent_color, org_id
        ))
        conn.commit()

def delete_organization(org_id, user_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
        conn.commit()
        log_activity(user_id, "PROFILE_DELETED", f"Deleted brand profile ID #{org_id}")

def get_brand_rules(org_id, category=None, only_enabled=False):
    with get_connection() as conn:
        query = "SELECT * FROM brand_rules WHERE org_id = ?"
        params = [org_id]
        if category and category != "All":
            query += " AND category = ?"
            params.append(category)
        if only_enabled:
            query += " AND (is_enabled = 1 OR is_enabled IS NULL)"
        query += " ORDER BY id DESC"
        cursor = conn.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

def add_brand_rule(org_id, category, rule_title, rule_description, severity="medium", embedding=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO brand_rules (org_id, category, rule_title, rule_description, severity, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (org_id, category, rule_title, rule_description, severity, embedding))
        rule_id = cursor.lastrowid
        conn.commit()
        return rule_id

def update_brand_rule(rule_id, category, rule_title, rule_description, severity):
    with get_connection() as conn:
        conn.execute("""
            UPDATE brand_rules SET
                category = ?, rule_title = ?, rule_description = ?, severity = ?
            WHERE id = ?
        """, (category, rule_title, rule_description, severity, rule_id))
        conn.commit()

def delete_brand_rule(rule_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM brand_rules WHERE id = ?", (rule_id,))
        conn.commit()

def save_guideline_document(org_id, filename, file_type, file_size, extracted_text):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO guideline_documents (org_id, filename, file_type, file_size, extracted_text)
            VALUES (?, ?, ?, ?, ?)
        """, (org_id, filename, file_type, file_size, extracted_text))
        doc_id = cursor.lastrowid
        conn.commit()
        return doc_id

def get_guideline_documents(org_id):
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM guideline_documents WHERE org_id = ? ORDER BY id DESC", (org_id,))
        return [dict(row) for row in cursor.fetchall()]

def save_analysis(org_id, user_id, title, asset_type, target_channel, input_content, image_path, compliance_score, status, corrected_content, summary, full_report_json):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analyses (
                org_id, user_id, title, asset_type, target_channel, input_content,
                image_path, compliance_score, status, corrected_content, summary, full_report_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            org_id, user_id, title, asset_type, target_channel, input_content,
            image_path, compliance_score, status, corrected_content, summary, full_report_json
        ))
        analysis_id = cursor.lastrowid
        conn.commit()
        log_activity(user_id, "ANALYSIS_RUN", f"Ran compliance analysis for '{title}' (Score: {compliance_score}%)", org_id)
        return analysis_id

def get_analyses(org_id=None, limit=50):
    with get_connection() as conn:
        if org_id:
            cursor = conn.execute("""
                SELECT a.*, o.name as org_name
                FROM analyses a
                JOIN organizations o ON a.org_id = o.id
                WHERE a.org_id = ?
                ORDER BY a.id DESC LIMIT ?
            """, (org_id, limit))
        else:
            cursor = conn.execute("""
                SELECT a.*, o.name as org_name
                FROM analyses a
                JOIN organizations o ON a.org_id = o.id
                ORDER BY a.id DESC LIMIT ?
            """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

def get_analysis_by_id(analysis_id):
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT a.*, o.name as org_name
            FROM analyses a
            JOIN organizations o ON a.org_id = o.id
            WHERE a.id = ?
        """, (analysis_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_recent_activity(org_id=None, limit=10):
    with get_connection() as conn:
        if org_id:
            cursor = conn.execute("""
                SELECT l.*, o.name as org_name
                FROM activity_logs l
                LEFT JOIN organizations o ON l.org_id = o.id
                WHERE l.org_id = ?
                ORDER BY l.id DESC LIMIT ?
            """, (org_id, limit))
        else:
            cursor = conn.execute("""
                SELECT l.*, o.name as org_name
                FROM activity_logs l
                LEFT JOIN organizations o ON l.org_id = o.id
                ORDER BY l.id DESC LIMIT ?
            """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

def get_dashboard_metrics(org_id=None):
    with get_connection() as conn:
        if org_id:
            assets_count = conn.execute("SELECT COUNT(*) FROM analyses WHERE org_id = ?", (org_id,)).fetchone()[0]
            avg_score = conn.execute("SELECT AVG(compliance_score) FROM analyses WHERE org_id = ?", (org_id,)).fetchone()[0]
            violations_count = 0
            analyses = conn.execute("SELECT full_report_json FROM analyses WHERE org_id = ?", (org_id,)).fetchall()
        else:
            assets_count = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
            avg_score = conn.execute("SELECT AVG(compliance_score) FROM analyses").fetchone()[0]
            analyses = conn.execute("SELECT full_report_json FROM analyses").fetchall()

        org_count = conn.execute("SELECT COUNT(*) FROM organizations").fetchone()[0]

        total_violations = 0
        for a in analyses:
            if a["full_report_json"]:
                try:
                    report = json.loads(a["full_report_json"])
                    total_violations += len(report.get("violations", []))
                except Exception:
                    pass

        return {
            "assets_analysed": assets_count,
            "compliance_score": round(avg_score, 1) if avg_score is not None else 100.0,
            "violations_found": total_violations,
            "brand_profiles": org_count
        }

def get_setting(key, default=None):
    with get_connection() as conn:
        cursor = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

def set_setting(key, value):
    with get_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()


def toggle_rule_status(rule_id, is_enabled):
    with get_connection() as conn:
        conn.execute("UPDATE brand_rules SET is_enabled = ? WHERE id = ?", (1 if is_enabled else 0, rule_id))
        conn.commit()

def update_brand_phrases(org_id, preferred, prohibited):
    with get_connection() as conn:
        conn.execute("""
            UPDATE organizations SET
                preferred_phrases = ?,
                prohibited_phrases = ?
            WHERE id = ?
        """, (json.dumps(preferred), json.dumps(prohibited), org_id))
        conn.commit()

def update_brand_logo(org_id, logo_path):
    with get_connection() as conn:
        conn.execute("UPDATE organizations SET logo_path = ? WHERE id = ?", (logo_path, org_id))
        conn.commit()

def get_recurring_violations(org_id=None):
    with get_connection() as conn:
        if org_id:
            analyses = conn.execute("SELECT full_report_json FROM analyses WHERE org_id = ?", (org_id,)).fetchall()
        else:
            analyses = conn.execute("SELECT full_report_json FROM analyses").fetchall()

    issue_counts = {}
    category_counts = {}
    severity_counts = {"High": 0, "Medium": 0, "Low": 0}

    for a in analyses:
        if a["full_report_json"]:
            try:
                rep = json.loads(a["full_report_json"])
                for v in rep.get("violations", []):
                    issue = v.get("issue", "Unspecified issue")
                    cat = v.get("category", "General")
                    sev = v.get("severity", "Medium")
                    
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                    if sev in severity_counts:
                        severity_counts[sev] += 1
            except Exception:
                pass

    top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "top_issues": top_issues,
        "category_counts": category_counts,
        "severity_counts": severity_counts
    }

INDUSTRY_PRESETS = {
    "SaaS & Enterprise Tech": [
        ("Tone & Voice", "Executive Precision", "Communicate with clear, confident authority. Avoid hyper-casual slang ('super cool', 'insane deal').", "medium"),
        ("Prohibited Claims", "No Unverifiable Guarantees", "Never claim '100% hack-proof', 'zero risk', or 'the only solution in the world'.", "high"),
        ("Brand Naming", "Canonical Product Casing", "Maintain exact brand casing across all channels. Never split CamelCase brand names.", "high"),
        ("Legal & Disclaimers", "SOC2 and Security Notice", "All beta announcements or enterprise feature claims must note compliance certifications.", "medium"),
        ("Visual & Colors", "High-Contrast Enterprise Palette", "Grounded in cyber-purple and dark neutrals. Avoid unapproved neon accents.", "medium")
    ],
    "FinTech & Banking": [
        ("Legal & Disclaimers", "Mandatory Regulatory Disclosures", "All financial content must display required regulatory licenses and risk warnings.", "high"),
        ("Prohibited Claims", "Zero Guaranteed Investment Returns", "Never state or imply guaranteed capital returns, risk-free yields, or get-rich metrics.", "high"),
        ("Tone & Voice", "Transparent & Trustworthy Voice", "Ensure absolute precision in financial metrics, terms, and interest rate disclosures.", "high"),
        ("Visual & Colors", "Trust & Accessibility (WCAG AA)", "Visual charts must maintain 4.5:1 contrast ratio against backdrops.", "medium")
    ],
    "Healthcare & Life Sciences": [
        ("Legal & Disclaimers", "FDA & Clinical Trial Disclaimers", "All health or biological claims must state 'Statements not evaluated by FDA/CE'.", "high"),
        ("Prohibited Claims", "No Miracle or Cure Terminology", "Prohibit words like 'miracle cure', 'instant recovery', or 'guaranteed treatment'.", "high"),
        ("Tone & Voice", "Empathetic Clinical Rigor", "Balance human empathy with rigorous scientific accuracy.", "medium"),
        ("Visual & Colors", "Clean Serene Palette", "Calming blues, lavenders, and deep medical tones with clean typographic hierarchy.", "medium")
    ],
    "E-Commerce & DTC Retail": [
        ("Prohibited Claims", "Transparent Pricing & Scarcity", "No artificial countdowns or fabricated scarcity statements ('only 1 left forever').", "medium"),
        ("Legal & Disclaimers", "Clear Return & Shipping Policy", "Promotional campaigns must clearly reference return windows and standard conditions.", "medium"),
        ("Tone & Voice", "Vibrant Inspiring Storytelling", "High energy, customer-centric tone celebrating lifestyle and product quality.", "low"),
        ("Visual & Colors", "Vivid Brand Palette Alignment", "Strict adherence to primary product hero colors and high-res photography.", "medium")
    ]
}

def apply_industry_preset(org_id, industry_name):
    presets = INDUSTRY_PRESETS.get(industry_name, [])
    if not presets:
        return 0

    from processing.ai_engine.vector_store import index_brand_rule
    added_count = 0
    with get_connection() as conn:
        for cat, title, desc, sev in presets:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO brand_rules (org_id, category, rule_title, rule_description, severity, is_enabled)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (org_id, cat, title, desc, sev))
            r_id = cursor.lastrowid
            conn.commit()
            index_brand_rule(r_id, f"{cat} - {title}: {desc}")
            added_count += 1

    return added_count
