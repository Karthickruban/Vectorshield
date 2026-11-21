import os
import json
import re

transcript_full_path = r"C:\Users\vsvig\.gemini\antigravity\brain\2674dfdc-9aed-4718-9c1f-f876d1a268fe\.system_generated\logs\transcript_full.jsonl"

turns = []
current_turn = None

with open(transcript_full_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            data = json.loads(line)
        except Exception:
            continue
        
        step_type = data.get("type")
        source = data.get("source")
        content = data.get("content", "")
        thinking = data.get("thinking", "")
        tool_calls = data.get("tool_calls", [])
        created_at = data.get("created_at", "")
        
        if step_type == "USER_INPUT":
            # Strip tags like <USER_REQUEST>, <ADDITIONAL_METADATA>, etc.
            user_text = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", content, flags=re.DOTALL)
            user_text = re.sub(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", user_text, flags=re.DOTALL)
            user_text = re.sub(r"</?USER_REQUEST>", "", user_text).strip()
            
            current_turn = {
                "turn_index": len(turns) + 1,
                "timestamp": created_at,
                "user_prompt": user_text,
                "assistant_responses": [],
                "tool_calls": []
            }
            turns.append(current_turn)
            
        elif step_type == "PLANNER_RESPONSE" and current_turn is not None:
            if content and content.strip():
                current_turn["assistant_responses"].append({
                    "text": content.strip(),
                    "timestamp": created_at
                })
            if tool_calls:
                for tc in tool_calls:
                    fn = tc.get("function", {}) if isinstance(tc, dict) else {}
                    current_turn["tool_calls"].append({
                        "name": fn.get("name", "tool"),
                        "summary": fn.get("arguments", {}).get("toolSummary", "")
                    })

print(f"Total turns parsed: {len(turns)}")
for t in turns:
    print(f"Turn {t['turn_index']} [{t['timestamp']}]:")
    print(f"  User: {t['user_prompt'][:100]}...")
    print(f"  Assistant msgs: {len(t['assistant_responses'])}, Tool calls: {len(t['tool_calls'])}")
