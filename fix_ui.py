# fix_static.py
import os

css = """
* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; }
html { scroll-behavior: smooth; }
body { background-color: #0f172a; background-image: radial-gradient(circle at 15% 0%, rgba(56, 189, 248, 0.08), transparent 45%), radial-gradient(circle at 85% 100%, rgba(99, 102, 241, 0.07), transparent 45%); background-attachment: fixed; color: #f8fafc; line-height: 1.6; display: flex; flex-direction: column; min-height: 100vh; -webkit-font-smoothing: antialiased; }
a { color: #38bdf8; text-decoration: none; transition: color 0.2s ease; }
a:hover { color: #7dd3fc; text-decoration: underline; }
::selection { background: rgba(56, 189, 248, 0.35); color: #ffffff; }

.navbar { background-color: rgba(30, 41, 59, 0.85); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); border-bottom: 1px solid #334155; padding: 1rem 0; position: sticky; top: 0; z-index: 100; box-shadow: 0 4px 12px -4px rgba(0, 0, 0, 0.4); }
.nav-container { max-width: 1000px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; padding: 0 1.5rem; }
.brand { font-size: 1.25rem; font-weight: 700; color: #f8fafc; text-decoration: none !important; letter-spacing: -0.01em; background: linear-gradient(90deg, #f8fafc, #7dd3fc); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.nav-links a { color: #cbd5e1; font-weight: 500; position: relative; padding: 0.25rem 0; margin-left: 1rem; }
.nav-links a:hover { color: #f8fafc; text-decoration: none; }
.nav-links a::after { content: ""; position: absolute; left: 0; bottom: -2px; width: 0; height: 2px; background: #38bdf8; transition: width 0.25s ease; }
.nav-links a:hover::after { width: 100%; }

.container { max-width: 1000px; margin: 2.5rem auto; padding: 0 1.5rem; flex-grow: 1; width: 100%; }
.card { background-color: #1e293b; padding: 2.5rem; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.02) inset; margin: 0 auto; max-width: 650px; animation: fadeUp 0.4s ease both; transition: border-color 0.2s ease, box-shadow 0.2s ease; }
.card:hover { border-color: #475569; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4); }

h1, h2, h3, h4 { color: #f8fafc; font-weight: 600; margin-bottom: 0.5rem; letter-spacing: -0.01em; }
h1 { font-size: 1.85rem; }
h2 { font-size: 1.5rem; }
p { color: #94a3b8; }

.form-group { display: flex; flex-direction: column; gap: 1.25rem; margin-top: 1rem; }
.field { display: flex; flex-direction: column; gap: 0.5rem; }
.field label { font-size: 0.875rem; color: #cbd5e1; font-weight: 500; }
.field input, .field textarea, .field select { padding: 0.75rem 1rem; border-radius: 6px; border: 1px solid #475569; background-color: #0f172a; color: #f8fafc; width: 100%; font-size: 1rem; transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease; }
.field input::placeholder, .field textarea::placeholder { color: #64748b; }
.field input:hover, .field textarea:hover, .field select:hover { border-color: #64748b; }
.field input:focus, .field textarea:focus, .field select:focus { outline: none; border-color: #38bdf8; box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2); }
.field input[readonly], .field textarea[readonly] { background-color: #1e293b; border-color: #334155; cursor: not-allowed; }
.field textarea { resize: vertical; min-height: 110px; }

.btn { padding: 0.75rem 1.5rem; border-radius: 6px; border: none; cursor: pointer; font-weight: 600; text-align: center; display: inline-block; font-size: 1rem; text-decoration: none !important; transition: background-color 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease; }
.btn:active { transform: translateY(1px); }
.btn:focus-visible { outline: 2px solid #7dd3fc; outline-offset: 2px; }
.btn:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-primary { background-color: #0284c7; color: #ffffff; box-shadow: 0 4px 10px -2px rgba(2, 132, 199, 0.4); }
.btn-primary:hover { background-color: #0369a1; transform: translateY(-1px); box-shadow: 0 6px 14px -2px rgba(2, 132, 199, 0.5); }

.alert { padding: 1rem 1.25rem; border-radius: 6px; margin-bottom: 1.5rem; font-size: 0.95rem; border-left-width: 4px; animation: fadeUp 0.3s ease both; }
.alert-success { background-color: #064e3b; color: #34d399; border: 1px solid #059669; }
.alert-danger { background-color: #7f1d1d; color: #fca5a5; border: 1px solid #991b1b; }

/* Extras: tables, footer, scrollbar (only apply if used in your templates) */
table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
th, td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #334155; }
th { color: #cbd5e1; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }
tr:hover td { background-color: rgba(51, 65, 85, 0.35); }
footer { text-align: center; padding: 1.5rem; color: #64748b; font-size: 0.875rem; border-top: 1px solid #1e293b; }

::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 6px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 600px) {
  .card { padding: 1.5rem; }
  .container { margin: 1.5rem auto; }
  .nav-container { padding: 0 1rem; }
}

@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
}
"""

os.makedirs("app/static", exist_ok=True)
os.makedirs("app/static/css", exist_ok=True)

with open("app/static/style.css", "w", encoding="utf-8") as f:
    f.write(css.strip())

with open("app/static/css/style.css", "w", encoding="utf-8") as f:
    f.write(css.strip())

print("Static CSS files written successfully to both paths!")