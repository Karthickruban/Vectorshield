import os
import json
import re
import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
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
# GENERATE PDF WITH FLOWABLE PARAGRAPHS
# ==========================================
pdf_path = os.path.join(export_dir, "VectorShield_Full_Antigravity_Chat_History.pdf")

doc_pdf = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    leftMargin=40,
    rightMargin=40,
    topMargin=40,
    bottomMargin=40
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
    leading=16,
    textColor=colors.HexColor("#0284c7"),
    spaceBefore=12,
    spaceAfter=4,
    keepWithNext=True
)
user_label_style = ParagraphStyle(
    "UserLabel",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    fontName="Helvetica-Bold",
    textColor=colors.HexColor("#0369a1"),
    spaceBefore=6,
    spaceAfter=2,
    keepWithNext=True
)
user_text_style = ParagraphStyle(
    "UserText",
    parent=styles["Normal"],
    fontSize=9,
    leading=13,
    textColor=colors.HexColor("#0f172a"),
    leftIndent=12,
    spaceAfter=6
)
asst_label_style = ParagraphStyle(
    "AsstLabel",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    fontName="Helvetica-Bold",
    textColor=colors.HexColor("#7c3aed"),
    spaceBefore=6,
    spaceAfter=2,
    keepWithNext=True
)
asst_text_style = ParagraphStyle(
    "AsstText",
    parent=styles["Normal"],
    fontSize=8.5,
    leading=12,
    textColor=colors.HexColor("#1e293b"),
    leftIndent=12,
    spaceAfter=4
)
tools_style = ParagraphStyle(
    "ToolsStyle",
    parent=styles["Normal"],
    fontSize=7.5,
    leading=10,
    textColor=colors.HexColor("#64748b"),
    leftIndent=16,
    spaceAfter=4
)

def clean_for_rl(txt):
    if not txt:
        return ""
    txt = txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    txt = txt.replace("\n", "<br/>")
    return txt

story = []
story.append(Paragraph("<b>VectorShield: Complete Antigravity Chat History</b>", title_style))
story.append(Spacer(1, 4))
story.append(Paragraph(f"<b>Session ID:</b> 2674dfdc-9aed-4718-9c1f-f876d1a268fe | <b>Timeline:</b> Sept 18 - Oct 25, 2026 | <b>Turns:</b> {len(turns)}", subtitle_style))
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceBefore=2, spaceAfter=10))

for t in turns:
    story.append(Paragraph(f"<b>Turn #{t['turn_index']}</b> &nbsp; <font color='#64748b' size='8'>[{t['timestamp']}]</font>", turn_hdr_style))
    story.append(Paragraph("<b>👤 User Prompt:</b>", user_label_style))
    
    # Split user prompt by newlines into paragraphs so it breaks nicely
    u_paras = [p.strip() for p in t['user_prompt'].split('\n') if p.strip()]
    if not u_paras:
        u_paras = [t['user_prompt']]
    for up in u_paras:
        story.append(Paragraph(clean_for_rl(up), user_text_style))
        
    story.append(Paragraph("<b>🤖 Antigravity:</b>", asst_label_style))
    
    has_text = False
    for m in t["messages"]:
        if m["content"]:
            has_text = True
            # Split long content into blocks
            content_blocks = m["content"].split("\n\n")
            for block in content_blocks:
                b = block.strip()
                if b:
                    # Cap single huge blocks to avoid reportlab page overflow
                    if len(b) > 2500:
                        b = b[:2500] + "... [truncated in PDF - see HTML/MD for full text]"
                    story.append(Paragraph(clean_for_rl(b), asst_text_style))
                    
        if m["tool_calls"]:
            t_names = [tc['name'] + (f" ({tc['summary']})" if tc.get('summary') else "") for tc in m['tool_calls'][:6]]
            summary_line = f"🛠️ <i>Actions: {', '.join(t_names)}" + (f" and {len(m['tool_calls'])-6} more..." if len(m['tool_calls']) > 6 else "") + "</i>"
            story.append(Paragraph(summary_line, tools_style))
            
    if not has_text:
        story.append(Paragraph("<i>[Executed system commands, code updates, and environment tasks]</i>", asst_text_style))
        
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceBefore=8, spaceAfter=8))

doc_pdf.build(story)
print("Exported PDF successfully.")
