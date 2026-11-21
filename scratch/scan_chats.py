import os
import json
import re

brain_dir = r"C:\Users\vsvig\.gemini\antigravity\brain"

print("Scanning all brain directories...")
matching = []
for cid in os.listdir(brain_dir):
    cpath = os.path.join(brain_dir, cid)
    if not os.path.isdir(cpath):
        continue
    tp = os.path.join(cpath, ".system_generated", "logs", "transcript_full.jsonl")
    if not os.path.exists(tp):
        tp = os.path.join(cpath, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(tp):
            continue
    
    sz = os.path.getsize(tp)
    has_proj = False
    first_prompts = []
    try:
        with open(tp, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f):
                if idx > 200:
                    break
                if "College stuff\\Sem7\\Project" in line or "VectorShield" in line:
                    has_proj = True
                if '"type": "USER_INPUT"' in line or '"type":"USER_INPUT"' in line:
                    try:
                        d = json.loads(line)
                        content = d.get("content", "")
                        clean = re.sub(r"<[^>]+>", "", content).strip()
                        if clean:
                            first_prompts.append(clean[:80])
                    except:
                        pass
    except Exception as e:
        pass
    
    if has_proj:
        matching.append((cid, sz, first_prompts))

print(f"Found {len(matching)} matching conversation(s):")
for cid, sz, fps in matching:
    print(f"\nCID: {cid} ({sz} bytes)")
    for p in fps[:3]:
        print(f"  - {p}")
