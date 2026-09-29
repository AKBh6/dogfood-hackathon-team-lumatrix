# fix_static.py
import os

css = """
* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; }
body { background-color: #0f172a; color: #f8fafc; line-height: 1.6; display: flex; flex-direction: column; min-height: 100vh; }
a { color: #38bdf8; text-decoration: none; }
a:hover { color: #7dd3fc; text-decoration: underline; }

.navbar { background-color: #1e293b; border-bottom: 1px solid #334155; padding: 1rem 0; }
.nav-container { max-width: 1000px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; padding: 0 1.5rem; }
.brand { font-size: 1.25rem; font-weight: 700; color: #f8fafc; text-decoration: none !important; }
.nav-links a { color: #cbd5e1; font-weight: 500; }
.nav-links a:hover { color: #f8fafc; }

.container { max-width: 1000px; margin: 2.5rem auto; padding: 0 1.5rem; flex-grow: 1; width: 100%; }
.card { background-color: #1e293b; padding: 2.5rem; border-radius: 8px; border: 1px solid #334155; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); margin: 0 auto; max-width: 650px; }

h1, h2, h3, h4 { color: #f8fafc; font-weight: 600; margin-bottom: 0.5rem; }
p { color: #94a3b8; }

.form-group { display: flex; flex-direction: column; gap: 1.25rem; margin-top: 1rem; }
.field { display: flex; flex-direction: column; gap: 0.5rem; }
.field label { font-size: 0.875rem; color: #cbd5e1; font-weight: 500; }
.field input, .field textarea, .field select { padding: 0.75rem 1rem; border-radius: 6px; border: 1px solid #475569; background-color: #0f172a; color: #f8fafc; width: 100%; font-size: 1rem; }
.field input:focus, .field textarea:focus, .field select:focus { outline: none; border-color: #38bdf8; box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2); }
.field input[readonly], .field textarea[readonly] { background-color: #1e293b; border-color: #334155; cursor: not-allowed; }

.btn { padding: 0.75rem 1.5rem; border-radius: 6px; border: none; cursor: pointer; font-weight: 600; text-align: center; display: inline-block; font-size: 1rem; text-decoration: none !important; }
.btn-primary { background-color: #0284c7; color: #ffffff; }
.btn-primary:hover { background-color: #0369a1; }

.alert { padding: 1rem 1.25rem; border-radius: 6px; margin-bottom: 1.5rem; font-size: 0.95rem; }
.alert-success { background-color: #064e3b; color: #34d399; border: 1px solid #059669; }
.alert-danger { background-color: #7f1d1d; color: #fca5a5; border: 1px solid #991b1b; }
"""

os.makedirs("app/static", exist_ok=True)
os.makedirs("app/static/css", exist_ok=True)

with open("app/static/style.css", "w", encoding="utf-8") as f:
    f.write(css.strip())

with open("app/static/css/style.css", "w", encoding="utf-8") as f:
    f.write(css.strip())

print("Static CSS files written successfully to both paths!")