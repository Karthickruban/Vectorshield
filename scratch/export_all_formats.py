import os
import json
import re
import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

transcript_full_path = r"C:\Users\vsvig\.gemini\antigravity\brain\2674dfdc-9aed-4718-9c1f-f876d1a268fe\.system_generated\logs\transcript_full.jsonl"
export_dir = r"d:\College stuff\Sem7\Project"

turns = []
current_turn = None

with open(transcript_full_path, "r", encoding="utf-8", errors="ignore") as f:
    for line_idx, line in enumerate(f):
        try:
            data = json.loads(line)
        except Exception:
            continue
        
        step_type = data.get("type")
        source = data.get("source")
        content = data.get("content", "")
        tool_calls = data.get("tool_calls", [])
        created_at = data.get("created_at", "")
        step_index = data.get("step_index", line_idx)
        
        if step_type == "USER_INPUT":
            user_text = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", content, flags=re.DOTALL)
            user_text = re.sub(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", user_text, flags=re.DOTALL)
            user_text = re.sub(r"</?USER_REQUEST>", "", user_text).strip()
            
            if current_turn:
                turns.append(current_turn)
                
            current_turn = {
                "turn_index": len(turns) + 1,
                "timestamp": created_at,
                "user_prompt": user_text,
                "messages": []
            }
        elif current_turn is not None and step_type == "PLANNER_RESPONSE":
            t_calls_summary = []
            if tool_calls:
                for tc in tool_calls:
                    fn = tc.get("function", {}) if isinstance(tc, dict) else {}
                    name = fn.get("name", "tool")
                    args = fn.get("arguments", {})
                    summary = args.get("toolSummary", "") if isinstance(args, dict) else ""
                    cmd = args.get("CommandLine", "") if isinstance(args, dict) else ""
                    path = args.get("Path", "") if isinstance(args, dict) else ""
                    t_calls_summary.append({
                        "name": name,
                        "summary": summary,
                        "target": (cmd[:60] if cmd else path)
                    })
            
            if (content and content.strip()) or t_calls_summary:
                current_turn["messages"].append({
                    "step_index": step_index,
                    "timestamp": created_at,
                    "content": content.strip() if content else "",
                    "tool_calls": t_calls_summary
                })

if current_turn:
    turns.append(current_turn)

print(f"Loaded {len(turns)} conversation turns.")

# ==========================================
# 1. EXPORT TO JSON
# ==========================================
json_output_path = os.path.join(export_dir, "VectorShield_Full_Antigravity_Chat_History.json")
with open(json_output_path, "w", encoding="utf-8") as f:
    json.dump({
        "project": "VectorShield - Sem7 Capstone Project",
        "conversation_id": "2674dfdc-9aed-4718-9c1f-f876d1a268fe",
        "exported_at": datetime.datetime.now().isoformat(),
        "total_turns": len(turns),
        "turns": turns
    }, f, indent=2, ensure_ascii=False)
print("Exported JSON successfully.")

# ==========================================
# 2. EXPORT TO MARKDOWN
# ==========================================
md_output_path = os.path.join(export_dir, "VectorShield_Full_Antigravity_Chat_History.md")
with open(md_output_path, "w", encoding="utf-8") as f:
    f.write("# VectorShield: Complete Antigravity Chat History\n\n")
    f.write(f"- **Project**: VectorShield (Sem 7 Final Year Project)\n")
    f.write(f"- **Conversation ID**: `2674dfdc-9aed-4718-9c1f-f876d1a268fe`\n")
    f.write(f"- **Timeline**: September 18, 2026 – October 25, 2026\n")
    f.write(f"- **Total Interaction Turns**: {len(turns)}\n")
    f.write(f"- **Exported On**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write("---\n\n")
    f.write("## Table of Contents\n\n")
    for t in turns:
        title_snippet = t['user_prompt'].split('\n')[0][:70].replace('[', '').replace(']', '')
        f.write(f"- [Turn {t['turn_index']}: {title_snippet}](#turn-{t['turn_index']})\n")
    f.write("\n---\n\n")
    
    for t in turns:
        f.write(f"## Turn {t['turn_index']}\n\n")
        f.write(f"**Timestamp**: `{t['timestamp']}`\n\n")
        f.write("### 👤 User Prompt\n\n")
        f.write(f"> {t['user_prompt'].replace(chr(10), chr(10) + '> ')}\n\n")
        
        f.write("### 🤖 Antigravity Response\n\n")
        has_assistant_text = False
        for m in t["messages"]:
            if m["content"]:
                has_assistant_text = True
                f.write(f"{m['content']}\n\n")
            if m["tool_calls"]:
                tool_lines = []
                for tc in m["tool_calls"]:
                    desc = f"`{tc['name']}`"
                    if tc['summary']:
                        desc += f" - {tc['summary']}"
                    elif tc['target']:
                        desc += f" - {tc['target']}"
                    tool_lines.append(desc)
                f.write("<details><summary>🛠️ <i>Tools Executed (" + str(len(tool_lines)) + ")</i></summary>\n\n")
                for tl in tool_lines:
                    f.write(f"- {tl}\n")
                f.write("\n</details>\n\n")
        
        if not has_assistant_text:
            f.write("*[Background tool execution and environment operations completed]*\n\n")
        f.write("---\n\n")

print("Exported Markdown successfully.")

# ==========================================
# 3. EXPORT TO INTERACTIVE HTML
# ==========================================
html_output_path = os.path.join(export_dir, "VectorShield_Full_Antigravity_Chat_History.html")

html_turns = []
for t in turns:
    # Build assistant messages
    assistant_parts = []
    for m in t["messages"]:
        if m["content"]:
            # Basic markdown replacement for html preview
            content_html = m["content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            # code blocks
            content_html = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', content_html, flags=re.DOTALL)
            content_html = content_html.replace("\n", "<br>")
            assistant_parts.append(f"<div class='msg-bubble assistant-bubble'>{content_html}</div>")
        if m["tool_calls"]:
            tools_html = "<div class='tools-box'><strong>🛠️ Actions & Tools:</strong><ul>"
            for tc in m["tool_calls"]:
                name = tc.get("name", "")
                summary = tc.get("summary") or tc.get("target") or ""
                tools_html += f"<li><code>{name}</code> {summary}</li>"
            tools_html += "</ul></div>"
            assistant_parts.append(tools_html)
    
    user_escaped = t['user_prompt'].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    
    html_turns.append(f"""
    <div class="turn-card" id="turn-{t['turn_index']}">
        <div class="turn-header">
            <span class="turn-badge">Turn #{t['turn_index']}</span>
            <span class="turn-date">🕒 {t['timestamp']}</span>
        </div>
        <div class="chat-section">
            <div class="user-label">👤 User</div>
            <div class="msg-bubble user-bubble">{user_escaped}</div>
        </div>
        <div class="chat-section">
            <div class="assistant-label">🤖 Antigravity</div>
            {''.join(assistant_parts) if assistant_parts else '<div class="msg-bubble assistant-bubble"><em>[Executed automated pipeline tasks]</em></div>'}
        </div>
    </div>
    """)

nav_links = "".join([f'<li><a href="#turn-{t["turn_index"]}">Turn {t["turn_index"]}: {t["user_prompt"][:45].replace("<","&lt;")}...</a></li>' for t in turns])

full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VectorShield - Complete Antigravity Chat Export</title>
<style>
    :root {{
        --bg-color: #0f172a;
        --sidebar-bg: #1e293b;
        --card-bg: #1e293b;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --accent: #38bdf8;
        --user-bg: #0369a1;
        --assistant-bg: #334155;
        --border-color: #334155;
        --code-bg: #0b1120;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: var(--bg-color);
        color: var(--text-primary);
        line-height: 1.6;
        display: flex;
        height: 100vh;
        overflow: hidden;
    }}
    #sidebar {{
        width: 320px;
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border-color);
        display: flex;
        flex-direction: column;
        flex-shrink: 0;
    }}
    #sidebar-header {{
        padding: 20px;
        border-bottom: 1px solid var(--border-color);
    }}
    #sidebar-header h2 {{
        font-size: 1.1rem;
        color: var(--accent);
        margin-bottom: 6px;
    }}
    #sidebar-header p {{
        font-size: 0.8rem;
        color: var(--text-secondary);
    }}
    #nav-list {{
        overflow-y: auto;
        padding: 10px 0;
        list-style: none;
        flex-grow: 1;
    }}
    #nav-list li a {{
        display: block;
        padding: 8px 16px;
        color: var(--text-secondary);
        text-decoration: none;
        font-size: 0.85rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        border-left: 3px solid transparent;
        transition: all 0.2s;
    }}
    #nav-list li a:hover {{
        background-color: rgba(56, 189, 248, 0.1);
        color: var(--text-primary);
        border-left-color: var(--accent);
    }}
    #main-content {{
        flex-grow: 1;
        overflow-y: auto;
        padding: 40px;
        scroll-behavior: smooth;
    }}
    .container {{
        max-width: 900px;
        margin: 0 auto;
    }}
    .hero {{
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 30px;
    }}
    .hero h1 {{
        color: var(--accent);
        font-size: 1.8rem;
        margin-bottom: 10px;
    }}
    .hero-meta {{
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        font-size: 0.85rem;
        color: var(--text-secondary);
    }}
    .hero-meta span {{
        background: rgba(255,255,255,0.05);
        padding: 4px 10px;
        border-radius: 6px;
    }}
    .turn-card {{
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }}
    .turn-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--border-color);
    }}
    .turn-badge {{
        background-color: var(--accent);
        color: #0f172a;
        font-weight: bold;
        font-size: 0.8rem;
        padding: 3px 10px;
        border-radius: 20px;
    }}
    .turn-date {{
        font-size: 0.8rem;
        color: var(--text-secondary);
    }}
    .chat-section {{
        margin-bottom: 16px;
    }}
    .user-label, .assistant-label {{
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .user-label {{ color: #38bdf8; }}
    .assistant-label {{ color: #a855f7; }}
    .msg-bubble {{
        padding: 14px 18px;
        border-radius: 8px;
        font-size: 0.95rem;
        line-height: 1.6;
        word-break: break-word;
    }}
    .user-bubble {{
        background-color: var(--user-bg);
        color: #ffffff;
        border-left: 4px solid #7dd3fc;
    }}
    .assistant-bubble {{
        background-color: var(--assistant-bg);
        color: #f8fafc;
        border-left: 4px solid #c084fc;
        margin-bottom: 10px;
    }}
    .tools-box {{
        background-color: var(--code-bg);
        border: 1px dashed #475569;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 0.82rem;
        color: var(--text-secondary);
        margin-top: 10px;
    }}
    .tools-box ul {{
        margin-left: 20px;
        margin-top: 5px;
    }}
    pre {{
        background-color: var(--code-bg);
        padding: 12px;
        border-radius: 6px;
        overflow-x: auto;
        font-family: Consolas, monospace;
        font-size: 0.85rem;
        margin: 10px 0;
        border: 1px solid #334155;
    }}
    code {{
        background-color: rgba(255,255,255,0.1);
        padding: 2px 5px;
        border-radius: 4px;
        font-family: Consolas, monospace;
        font-size: 0.85rem;
    }}
    pre code {{
        background-color: transparent;
        padding: 0;
    }}
</style>
</head>
<body>
    <div id="sidebar">
        <div id="sidebar-header">
            <h2>🛡️ VectorShield</h2>
            <p>Antigravity Chat Sessions</p>
        </div>
        <ul id="nav-list">
            {nav_links}
        </ul>
    </div>
    <div id="main-content">
        <div class="container">
            <div class="hero">
                <h1>VectorShield: Complete Project Chat History</h1>
                <div class="hero-meta">
                    <span>📁 Sem7 Final Year Project</span>
                    <span>🆔 Session: 2674dfdc...</span>
                    <span>💬 {len(turns)} Turns</span>
                    <span>📅 Sept 18 - Oct 25, 2026</span>
                </div>
            </div>
            {''.join(html_turns)}
        </div>
    </div>
</body>
</html>
"""

with open(html_output_path, "w", encoding="utf-8") as f:
    f.write(full_html)
print("Exported HTML successfully.")

# ==========================================
# 4. EXPORT TO DOCX
# ==========================================
docx_path = os.path.join(export_dir, "VectorShield_Full_Antigravity_Chat_History.docx")
doc = Document()

# Document title
title = doc.add_heading("VectorShield: Complete Antigravity Chat History", level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

p_meta = doc.add_paragraph()
p_meta.add_run("Project: ").bold = True
p_meta.add_run("VectorShield (Sem 7 Capstone Project)\n")
p_meta.add_run("Session ID: ").bold = True
p_meta.add_run("2674dfdc-9aed-4718-9c1f-f876d1a268fe\n")
p_meta.add_run("Timeline: ").bold = True
p_meta.add_run("September 18, 2026 – October 25, 2026\n")
p_meta.add_run("Total Turns: ").bold = True
p_meta.add_run(f"{len(turns)}\n")
p_meta.add_run("Exported On: ").bold = True
p_meta.add_run(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

doc.add_heading("Conversation Transcript", level=1)

for t in turns:
    h2 = doc.add_heading(f"Turn #{t['turn_index']} ({t['timestamp']})", level=2)
    
    # User prompt box
    p_user_hdr = doc.add_paragraph()
    r_user = p_user_hdr.add_run("👤 USER:")
    r_user.bold = True
    r_user.font.color.rgb = RGBColor(0x02, 0x84, 0xC7)
    
    p_user = doc.add_paragraph(t['user_prompt'])
    p_user.paragraph_format.left_indent = Inches(0.2)
    
    # Assistant
    p_asst_hdr = doc.add_paragraph()
    r_asst = p_asst_hdr.add_run("🤖 ANTIGRAVITY:")
    r_asst.bold = True
    r_asst.font.color.rgb = RGBColor(0x7C, 0x3A, 0xED)
    
    has_text = False
    for m in t["messages"]:
        if m["content"]:
            has_text = True
            p_msg = doc.add_paragraph(m["content"][:3000] + ("\n... [truncated for docx readability]" if len(m["content"]) > 3000 else ""))
            p_msg.paragraph_format.left_indent = Inches(0.2)
        if m["tool_calls"]:
            p_tools = doc.add_paragraph()
            p_tools.paragraph_format.left_indent = Inches(0.4)
            r_tool = p_tools.add_run(f"🛠️ Actions executed ({len(m['tool_calls'])} tool calls)")
            r_tool.font.italic = True
            r_tool.font.size = Pt(9)
            r_tool.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
            
    if not has_text:
        p_empty = doc.add_paragraph("[Executed workspace actions and pipeline tasks]")
        p_empty.paragraph_format.left_indent = Inches(0.2)
        
    doc.add_paragraph("─" * 40)

doc.save(docx_path)
print("Exported DOCX successfully.")

# ==========================================
# 5. EXPORT TO PDF VIA REPORTLAB
# ==========================================
pdf_path = os.path.join(export_dir, "VectorShield_Full_Antigravity_Chat_History.pdf")

doc_pdf = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    leftMargin=36,
    rightMargin=36,
    topMargin=36,
    bottomMargin=36
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "TitleStyle",
    parent=styles["Title"],
    fontSize=18,
    leading=22,
    textColor=colors.HexColor("#0f172a"),
    alignment=1
)
subtitle_style = ParagraphStyle(
    "SubtitleStyle",
    parent=styles["Normal"],
    fontSize=9,
    leading=13,
    textColor=colors.HexColor("#475569"),
    alignment=1
)
turn_hdr_style = ParagraphStyle(
    "TurnHdr",
    parent=styles["Heading2"],
    fontSize=12,
    leading=15,
    textColor=colors.HexColor("#0369a1")
)
user_style = ParagraphStyle(
    "UserStyle",
    parent=styles["Normal"],
    fontSize=9,
    leading=12,
    textColor=colors.HexColor("#0c4a6e")
)
asst_style = ParagraphStyle(
    "AsstStyle",
    parent=styles["Normal"],
    fontSize=8.5,
    leading=11.5,
    textColor=colors.HexColor("#1e293b")
)

story = []
story.append(Paragraph("<b>VectorShield: Complete Antigravity Chat History</b>", title_style))
story.append(Spacer(1, 6))
story.append(Paragraph(f"<b>Session ID:</b> 2674dfdc-9aed-4718-9c1f-f876d1a268fe | <b>Timeline:</b> Sept 18 - Oct 25, 2026 | <b>Turns:</b> {len(turns)}", subtitle_style))
story.append(Spacer(1, 14))

def clean_for_rl(txt):
    if not txt:
        return ""
    # XML escape
    txt = txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    txt = txt.replace("\n", "<br/>")
    return txt

for t in turns:
    story.append(Paragraph(f"<b>Turn #{t['turn_index']}</b> &nbsp; <font color='#64748b' size='7'>{t['timestamp']}</font>", turn_hdr_style))
    story.append(Spacer(1, 4))
    
    # User Box
    u_txt = clean_for_rl(t['user_prompt'])
    u_table = Table([[Paragraph(f"<b>👤 User:</b><br/>{u_txt}", user_style)]], colWidths=[540])
    u_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#e0f2fe")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#7dd3fc")),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(u_table)
    story.append(Spacer(1, 6))
    
    # Assistant Box
    asst_text_full = ""
    for m in t["messages"]:
        if m["content"]:
            asst_text_full += m["content"] + "\n\n"
        if m["tool_calls"]:
            asst_text_full += f"<i>[Executed {len(m['tool_calls'])} tools: " + ", ".join([tc['name'] for tc in m['tool_calls'][:5]]) + (", ..." if len(m['tool_calls']) > 5 else "") + "]</i>\n\n"
    
    if not asst_text_full.strip():
        asst_text_full = "<i>[Workspace actions and automated tasks executed successfully]</i>"
        
    # Cap per turn to prevent gigantic single page overflows in reportlab
    if len(asst_text_full) > 4000:
        asst_text_full = asst_text_full[:4000] + "\n... [truncated for PDF summary - view .html or .md for full content]"
        
    a_txt = clean_for_rl(asst_text_full)
    a_table = Table([[Paragraph(f"<b>🤖 Antigravity:</b><br/>{a_txt}", asst_style)]], colWidths=[540])
    a_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(a_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceBefore=4, spaceAfter=8))

doc_pdf.build(story)
print("Exported PDF successfully.")
