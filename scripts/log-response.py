#!/usr/bin/env python
"""
Claude Code Hook: Unified Conversation Logging (Response)
Triggered on Stop events to record all terminal output.
Formats output similarly to the terminal display.
"""
import json
import sys
import os
from datetime import datetime
import glob

# Ensure stdout/stderr can handle Unicode on Windows
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

DEBUG = False  # Debug mode

def debug_log(log_dir, message):
    """Write debug log entry."""
    if not DEBUG:
        return
    try:
        debug_file = os.path.join(log_dir, "debug-response.log")
        with open(debug_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

def format_tool_input(tool_name, tool_input):
    """Format tool input in terminal style."""
    if not tool_input:
        return f"● {tool_name}()"

    # Show only key parameters briefly
    params = []
    for key in ['pattern', 'command', 'file_path', 'path', 'query', 'description']:
        if key in tool_input:
            value = tool_input[key]
            if isinstance(value, str):
                # Truncate long values
                if len(value) > 60:
                    value = value[:57] + "..."
                params.append(f"{key}={value}")

    if params:
        return f"● {tool_name}({', '.join(params)})"
    return f"● {tool_name}(...)"

def format_tool_result(content, max_lines=10):
    """Format tool result in terminal style."""
    if not content:
        return "  ⎿  (no output)"

    lines = content.strip().split('\n')
    if len(lines) <= max_lines:
        formatted = '\n'.join([f"  ⎿  {line}" for line in lines])
    else:
        # Show first few lines and truncate the rest
        shown = lines[:max_lines-1]
        formatted = '\n'.join([f"  ⎿  {line}" for line in shown])
        formatted += f"\n  ⎿  ... +{len(lines) - max_lines + 1} lines"

    return formatted

def extract_full_content(entry):
    """Extract full content from entry in terminal format."""
    parts = []
    entry_type = entry.get("type", "")

    # Assistant type (main response)
    if entry_type == "assistant":
        message = entry.get("message", {})
        for item in message.get("content", []):
            if item.get("type") == "text":
                text = item.get("text", "")
                if text.strip():
                    parts.append(("text", f"● {text}"))

            elif item.get("type") == "tool_use":
                tool_name = item.get("name", "unknown")
                tool_input = item.get("input", {})
                formatted = format_tool_input(tool_name, tool_input)
                parts.append(("tool_use", formatted))

    # Tool result (tool execution output)
    elif entry_type == "tool_result":
        content = entry.get("content", "")
        if isinstance(content, str) and content.strip():
            formatted = format_tool_result(content)
            parts.append(("tool_result", formatted))
        elif isinstance(content, list):
            texts = []
            for item in content:
                if item.get("type") == "text":
                    text = item.get("text", "")
                    if text.strip():
                        texts.append(text)
            if texts:
                combined = '\n'.join(texts)
                formatted = format_tool_result(combined)
                parts.append(("tool_result", formatted))

    return parts

def classify_user_entry(entry):
    """Classify user-type entries to determine processing method."""
    message = entry.get("message", {})
    content = message.get("content", [])

    # Raw string = actual user prompt
    if isinstance(content, str):
        return "PROMPT"

    if isinstance(content, list):
        tool_results = [c for c in content if c.get("type") == "tool_result"]
        if tool_results:
            result_raw = tool_results[0].get("content", "")
            # If content is a list (e.g., [{type:"text"}]), classify as regular TOOL_RESULT
            if not isinstance(result_raw, str):
                return "TOOL_RESULT"
            result_text = result_raw.strip()

            if result_text.startswith("User has answered your questions:"):
                return "USER_ANSWER"
            elif result_text.startswith("User has approved your plan"):
                return "PLAN_APPROVAL"
            elif result_text.startswith("Exit plan mode?"):
                return "PLAN_APPROVAL"
            elif result_text.startswith("The user doesn\u2019t want to proceed"):
                return "TOOL_REJECTION"
            else:
                return "TOOL_RESULT"

        # Text content
        text_items = [c for c in content if c.get("type") == "text"]
        if text_items:
            text = text_items[0].get("text", "")
            if "[Request interrupted" in text:
                return "INTERRUPT"
            return "PROMPT"

    return "UNKNOWN"

def extract_user_interaction(entry, classification):
    """Extract user's actual answer/feedback from follow-up interactions."""
    message = entry.get("message", {})
    content = message.get("content", [])

    for c in (content if isinstance(content, list) else []):
        if c.get("type") != "tool_result":
            continue
        result_raw = c.get("content", "")
        result = result_raw if isinstance(result_raw, str) else str(result_raw)

        if classification == "USER_ANSWER":
            prefix = "User has answered your questions: "
            if prefix in result:
                start = result.index(prefix) + len(prefix)
                end = result.find(". You can now")
                return result[start:end] if end > start else result[start:start+300]

        elif classification == "TOOL_REJECTION":
            if "the user said:" in result:
                start = result.index("the user said:") + len("the user said:")
                return result[start:].strip()[:300]
            return ""

        elif classification == "PLAN_REJECTION":
            if "the user said:" in result:
                start = result.index("the user said:") + len("the user said:")
                return result[start:].strip()[:300]
            return "(plan rejected by user)"

        elif classification == "PLAN_APPROVAL":
            return "(plan approved)"

    return ""

def log_response():
    try:
        # Read JSON data from stdin
        input_data = json.load(sys.stdin)

        # Prevent duplicate logging when another Stop hook blocks and re-triggers
        if input_data.get("stop_hook_active", False):
            sys.exit(0)

        transcript_path = input_data.get("transcript_path", "")
        session_id = input_data.get("session_id", "")
        cwd = input_data.get("cwd", os.getcwd())

        # Log directory (project root/.claude/logs)
        log_dir = os.path.join(cwd, ".claude", "logs")
        os.makedirs(log_dir, exist_ok=True)

        debug_log(log_dir, f"=== Stop hook started ===")
        debug_log(log_dir, f"transcript_path: {transcript_path}")
        debug_log(log_dir, f"session_id: {session_id}")

        if not transcript_path or not os.path.exists(transcript_path):
            debug_log(log_dir, f"No transcript path found or file doesn't exist")
            print("No transcript path found", file=sys.stderr)
            sys.exit(0)

        # Log file (per date + session)
        date_prefix = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f"{date_prefix}_{session_id}_conversation-log.txt")

        # Extract all outputs from the last turn in the transcript
        follow_ups = []   # [(label, text), ...]
        all_outputs = []
        entry_types_found = []
        collecting = False

        with open(transcript_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

            debug_log(log_dir, f"Total lines in transcript: {len(lines)}")

            for i, line in enumerate(lines):
                try:
                    entry = json.loads(line.strip())
                    entry_type = entry.get("type", "unknown")
                    entry_types_found.append(entry_type)

                    if entry_type == "user":
                        classification = classify_user_entry(entry)
                        debug_log(log_dir, f"Line {i}: user entry classified as {classification}")

                        if classification == "PROMPT":
                            # New prompt -> full reset (already recorded by log-prompt.py)
                            collecting = True
                            follow_ups = []
                            all_outputs = []

                        elif classification == "USER_ANSWER":
                            # Follow-up interaction -> collect, reset assistant outputs only
                            text = extract_user_interaction(entry, classification)
                            follow_ups.append(("answer", text))
                            all_outputs = []

                        elif classification == "PLAN_APPROVAL":
                            # Plan approval -> record, reset assistant outputs
                            text = extract_user_interaction(entry, classification)
                            follow_ups.append(("plan approved", text))
                            all_outputs = []

                        elif classification == "TOOL_REJECTION":
                            # Tool rejection -> record inline (preserve preceding output)
                            text = extract_user_interaction(entry, classification)
                            if text:
                                all_outputs.append(("tool_rejection", f"  ⎿  Tool use rejected with user message: {text}"))
                            else:
                                all_outputs.append(("tool_rejection", "  ⎿  Tool use rejected"))

                        elif classification == "INTERRUPT":
                            # Interrupt -> record inline
                            all_outputs.append(("interrupt", "  ⎿  Interrupted"))

                        elif classification == "TOOL_RESULT":
                            # Regular tool_result -> reset assistant outputs only (keep follow_ups)
                            all_outputs = []

                        # UNKNOWN -> ignore
                        continue

                    # Collect assistant/other entries (after first user entry)
                    if collecting:
                        parts = extract_full_content(entry)
                        all_outputs.extend(parts)
                        if parts:
                            debug_log(log_dir, f"Line {i}: Extracted {len(parts)} parts from {entry_type}")

                except json.JSONDecodeError:
                    continue

        debug_log(log_dir, f"Entry types found: {set(entry_types_found)}")
        debug_log(log_dir, f"Total outputs collected: {len(all_outputs)}")
        debug_log(log_dir, f"Follow-ups collected: {len(follow_ups)}")

        # Format output and write to log
        with open(log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Record follow-up interactions
            for label, text in follow_ups:
                if text:
                    f.write(f"👤 USER ({label}):\n{text}\n")
                else:
                    f.write(f"👤 USER ({label})\n")
                f.write(f"{'-'*80}\n")

            # Record response
            formatted_output = [content for _, content in all_outputs]
            response_text = "\n\n".join(formatted_output) if formatted_output else "[No output found]"
            f.write(f"🤖 CLAUDE [{timestamp}]:\n")
            f.write(f"{response_text}\n")
            f.write(f"{'='*80}\n\n")

        # Clean up temporary session file
        temp_file = os.path.join(log_dir, f".temp_session_{session_id}.json")
        if os.path.exists(temp_file):
            os.remove(temp_file)

        # Clean up stale temporary files (older than 1 hour)
        temp_pattern = os.path.join(log_dir, ".temp_session_*.json")
        for temp_f in glob.glob(temp_pattern):
            try:
                if os.path.getmtime(temp_f) < (datetime.now().timestamp() - 3600):
                    os.remove(temp_f)
            except:
                pass

        print("Response logged")

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error logging response: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    log_response()
    sys.exit(0)
