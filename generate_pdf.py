import os
import subprocess
import markdown

def generate_pdf():
    md_path = os.path.join(os.path.dirname(__file__), "PROJECT_REPORT.md")
    html_path = os.path.join(os.path.dirname(__file__), "PROJECT_REPORT.html")
    pdf_path = os.path.join(os.path.dirname(__file__), "DevOps_Autopilot_Project_Report.pdf")

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Convert markdown to html with tables and code blocks
    body_html = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DevOps Autopilot – Infra Waste Resolver | Project Report</title>
<style>
  @page {{
    size: A4;
    margin: 18mm 15mm 18mm 15mm;
    @bottom-right {{
      content: counter(page);
    }}
  }}

  *, *:before, *:after {{
    box-sizing: border-box;
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    line-height: 1.55;
    font-size: 10pt;
    margin: 0;
    padding: 0;
  }}

  h1, h2, h3, h4, h5, h6 {{
    color: #0f172a;
    font-weight: 700;
    margin-top: 1.6em;
    margin-bottom: 0.6em;
    page-break-after: avoid;
    letter-spacing: -0.015em;
  }}

  h1 {{
    font-size: 20pt;
    line-height: 1.25;
    border-bottom: 2.5px solid #2563eb;
    padding-bottom: 8px;
    margin-top: 0;
    color: #1e3a8a;
  }}

  h2 {{
    font-size: 14pt;
    border-bottom: 1.5px solid #e2e8f0;
    padding-bottom: 6px;
    margin-top: 1.8em;
    color: #1d4ed8;
  }}

  h3 {{
    font-size: 11.5pt;
    color: #334155;
    margin-top: 1.4em;
  }}

  h4 {{
    font-size: 10.5pt;
    color: #475569;
  }}

  p, ul, ol {{
    margin-top: 0.5em;
    margin-bottom: 0.8em;
  }}

  li {{
    margin-bottom: 0.3em;
  }}

  hr {{
    border: none;
    border-top: 1px solid #cbd5e1;
    margin: 20px 0;
  }}

  /* Code & Syntax */
  pre {{
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #3b82f6;
    border-radius: 4px;
    padding: 10px 12px;
    font-family: "JetBrains Mono", Consolas, "Courier New", monospace;
    font-size: 8pt;
    line-height: 1.45;
    color: #0f172a;
    white-space: pre;
    overflow-x: auto;
    page-break-inside: avoid;
    margin: 10px 0 14px 0;
  }}

  code {{
    font-family: "JetBrains Mono", Consolas, "Courier New", monospace;
    font-size: 8.5pt;
    background-color: #f1f5f9;
    color: #0f172a;
    padding: 2px 5px;
    border-radius: 3px;
    border: 1px solid #e2e8f0;
  }}

  pre code {{
    background-color: transparent;
    padding: 0;
    border: none;
    font-size: 8pt;
  }}

  /* Tables */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0 18px 0;
    font-size: 8.5pt;
    page-break-inside: avoid;
  }}

  th, td {{
    border: 1px solid #cbd5e1;
    padding: 6px 10px;
    text-align: left;
    vertical-align: top;
  }}

  th {{
    background-color: #f1f5f9;
    color: #0f172a;
    font-weight: 600;
  }}

  tr:nth-child(even) td {{
    background-color: #f8fafc;
  }}

  /* Blockquotes */
  blockquote {{
    border-left: 4px solid #3b82f6;
    background-color: #eff6ff;
    margin: 12px 0;
    padding: 8px 14px;
    color: #1e40af;
    font-size: 9pt;
    border-radius: 0 4px 4px 0;
    page-break-inside: avoid;
  }}

  /* Badges & Meta */
  .doc-header {{
    background: linear-gradient(135deg, #1e3a8a, #0284c7);
    color: #ffffff;
    padding: 24px;
    border-radius: 8px;
    margin-bottom: 24px;
  }}

  .doc-header h1 {{
    color: #ffffff;
    border-bottom: 1px solid rgba(255,255,255,0.3);
    margin: 0 0 10px 0;
    font-size: 22pt;
  }}

  .doc-header p {{
    margin: 4px 0;
    font-size: 10pt;
    opacity: 0.95;
  }}

  .badge {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 7.5pt;
    font-weight: 700;
    text-transform: uppercase;
    background: #dbeafe;
    color: #1d4ed8;
    margin-right: 6px;
  }}
</style>
</head>
<body>
{body_html}
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"HTML rendered to: {html_path}")

    # Convert HTML to PDF via Chrome or Edge
    browser_exe = None
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

    if os.path.exists(chrome_path):
        browser_exe = chrome_path
    elif os.path.exists(edge_path):
        browser_exe = edge_path

    if not browser_exe:
        raise RuntimeError("No headless Chrome or Edge browser found.")

    cmd = [
        browser_exe,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={pdf_path}",
        html_path
    ]
    print(f"Generating PDF with: {browser_exe}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(pdf_path):
        size_kb = os.path.getsize(pdf_path) / 1024
        print(f"SUCCESS: PDF generated at: {pdf_path} ({size_kb:.1f} KB)")
    else:
        print("ERROR: PDF generation failed.")
        print(res.stderr)

if __name__ == "__main__":
    generate_pdf()
