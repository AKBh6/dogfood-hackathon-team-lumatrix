# restore_ui.py
import os

css_content = """
* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
body { background-color: #0f172a; color: #f8fafc; line-height: 1.6; display: flex; flex-direction: column; min-height: 100vh; }
a { color: #38bdf8; text-decoration: none; }
a:hover { text-decoration: underline; }

.navbar { background-color: #1e293b; padding: 1rem 0; border-bottom: 1px solid #334155; }
.nav-container { max-width: 1000px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; padding: 0 1rem; }
.brand { font-size: 1.25rem; font-weight: bold; color: #f8fafc; }

.container { max-width: 1000px; margin: 2rem auto; padding: 0 1rem; flex-grow: 1; }
.card { background-color: #1e293b; padding: 2.5rem; border-radius: 8px; border: 1px solid #334155; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin: 0 auto; max-width: 600px; }

.form-group { display: flex; flex-direction: column; gap: 1.25rem; }
.field { display: flex; flex-direction: column; gap: 0.5rem; }
.field label { font-size: 0.9rem; color: #cbd5e1; font-weight: 500; }
.field input, .field textarea { padding: 0.75rem; border-radius: 6px; border: 1px solid #475569; background-color: #0f172a; color: #f8fafc; width: 100%; font-size: 1rem; }
.field input:focus, .field textarea:focus { outline: none; border-color: #38bdf8; box-shadow: 0 0 0 1px #38bdf8; }

.btn { padding: 0.75rem 1.5rem; border-radius: 6px; border: none; cursor: pointer; font-weight: bold; text-align: center; display: inline-block; font-size: 1rem; transition: background-color 0.2s; }
.btn-primary { background-color: #0284c7; color: white; }
.btn-primary:hover { background-color: #0369a1; text-decoration: none; }

.alert { padding: 1rem; border-radius: 6px; margin-bottom: 1.5rem; }
.alert-success { background-color: #064e3b; color: #34d399; border: 1px solid #059669; }
.alert-danger { background-color: #7f1d1d; color: #fca5a5; border: 1px solid #991b1b; }

h1, h2, h3 { color: #f8fafc; margin-bottom: 0.5rem; }
p { color: #94a3b8; }
"""

os.makedirs("app/static/css", exist_ok=True)
with open("app/static/css/style.css", "w", encoding="utf-8") as f:
    f.write(css_content.strip())
print("app/static/css/style.css generated successfully!")