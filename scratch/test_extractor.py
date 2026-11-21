import os
import json
import re

transcript_full_path = r"C:\Users\vsvig\.gemini\antigravity\brain\2674dfdc-9aed-4718-9c1f-f876d1a268fe\.system_generated\logs\transcript_full.jsonl"

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
        thinking = data.get("thinking", "")
        tool_calls = data.get("tool_calls", [])
        created_at = data.get("created_at", "")
        step_index = data.get("step_index", line_idx)
        
        if step_type == "USER_INPUT":
            # Extract actual user text
            user_text = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", content, flags=re.DOTALL)
            user_text = re.sub(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", user_text, flags=re.DOTALL)
            user_text = re.sub(r"</?USER_REQUEST>", "", user_text).strip()
            
            # If there was a previous turn, save it
            if current_turn:
                turns.append(current_turn)
                
            current_turn = {
                "turn_index": len(turns) + 1,
                "timestamp": created_at,
                "user_prompt": user_text,
                "raw_user_content": content,
                "messages": [], # ordered list of assistant responses and actions
            }
        elif current_turn is not None:
            if step_type == "PLANNER_RESPONSE":
                # Check for tool calls or content
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
                            "target": cmd or path
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

print(f"Total turns: {len(turns)}")
total_msgs = sum(len(t["messages"]) for t in turns)
total_text_len = sum(sum(len(m["content"]) for m in t["messages"]) for t in turns)
print(f"Total assistant message events: {total_msgs}")
print(f"Total assistant text volume: {total_text_len} characters")
