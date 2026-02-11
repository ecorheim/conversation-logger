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

# Add scripts directory to path for utils import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    setup_encoding, get_log_dir, get_log_file_path, get_log_format,
    read_temp_session, cleanup_stale_temp_files, debug_log, calculate_fence
)

# Ensure stdout/stderr can handle Unicode on Windows
setup_encoding()


def format_tool_input(tool_name, tool_input):
    """Format tool input in terminal style (no truncation)."""
    if not tool_input:
        return f"\u25cf {tool_name}()"

    # Show key parameters
    params = []
    for key in ['pattern', 'command', 'file_path', 'path', 'query', 'description']:
        if key in tool_input:
            value = tool_input[key]
            if isinstance(value, str):
                params.append(f"{key}={value}")

    if params:
        return f"\u25cf {tool_name}({', '.join(params)})"
    return f"\u25cf {tool_name}(...)"


def format_tool_result(content):
    """Format tool result in terminal style (no truncation)."""
    if not content:
        return "  \u23bf  (no output)"

    lines = content.strip().split('\n')
    formatted = '\n'.join([f"  \u23bf  {line}" for line in lines])
    return formatted


def format_tool_input_md(tool_name, tool_input):
    """Format tool input as markdown heading with blockquote params."""
    # Heading
    heading = f"### \U0001f6e0\ufe0f Tool: `{tool_name}`"

    if not tool_input:
        return heading

    # Key parameters as blockquote
    params = []
    for key in ['pattern', 'command', 'file_path', 'path', 'query', 'description',
                 'old_string', 'new_string', 'content', 'url', 'prompt']:
        if key in tool_input:
            value = tool_input[key]
            if isinstance(value, str):
                # For display in blockquote, keep single-line
                display_val = value.replace('\n', ' ').strip()
                params.append(f"{key}={display_val}")

    if params:
        return f"{heading}\n> {', '.join(params)}"
    return heading


def format_tool_result_md(content):
    """Format tool result as markdown code block with dynamic fence."""
    if not content:
        return ""

    text = content.strip()
    fence = calculate_fence(text)
    return f"{fence}\n{text}\n{fence}"


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
                    parts.append(("text", text.strip()))

            elif item.get("type") == "tool_use":
                tool_name = item.get("name", "unknown")
                tool_input = item.get("input", {})
                parts.append(("tool_use", {
                    "name": tool_name,
                    "input": tool_input
                }))

    # Tool result (tool execution output)
    elif entry_type == "tool_result":
        content = entry.get("content", "")
        if isinstance(content, str) and content.strip():
            parts.append(("tool_result", content.strip()))
        elif isinstance(content, list):
            texts = []
            for item in content:
                if item.get("type") == "text":
                    text = item.get("text", "")
                    if text.strip():
                        texts.append(text)
            if texts:
                combined = '\n'.join(texts)
                parts.append(("tool_result", combined.strip()))

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


def _format_output_text(all_outputs):
    """Format collected outputs for text format."""
    formatted_parts = []
    for part_type, content in all_outputs:
        if part_type == "text":
            formatted_parts.append(f"\u25cf {content}")
        elif part_type == "tool_use":
            formatted_parts.append(format_tool_input(content["name"], content["input"]))
        elif part_type == "tool_result":
            formatted_parts.append(format_tool_result(content))
        elif part_type == "tool_rejection":
            formatted_parts.append(content)
        elif part_type == "interrupt":
            formatted_parts.append(content)
    return formatted_parts


def _format_output_markdown(all_outputs):
    """Format collected outputs for markdown format."""
    formatted_parts = []
    for part_type, content in all_outputs:
        if part_type == "text":
            formatted_parts.append(content)
        elif part_type == "tool_use":
            formatted_parts.append(format_tool_input_md(content["name"], content["input"]))
        elif part_type == "tool_result":
            md_result = format_tool_result_md(content)
            if md_result:
                formatted_parts.append(md_result)
        elif part_type == "tool_rejection":
            # Extract text from the formatted string
            if "user message:" in content:
                reason = content.split("user message:", 1)[-1].strip()
                formatted_parts.append(f"> **Tool Rejected**: {reason}")
            else:
                formatted_parts.append("> **Tool Rejected**")
        elif part_type == "interrupt":
            formatted_parts.append("> **Interrupted**")
    return formatted_parts


def _write_followups_text(f, follow_ups):
    """Write follow-up interactions in text format."""
    for label, text in follow_ups:
        if text:
            f.write(f"\U0001f464 USER ({label}):\n{text}\n")
        else:
            f.write(f"\U0001f464 USER ({label})\n")
        f.write(f"{'-'*80}\n")


def _write_followups_markdown(f, follow_ups):
    """Write follow-up interactions in markdown format."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    for label, text in follow_ups:
        if label == "answer":
            f.write(f"\n## \U0001f4ac User \u2014 {timestamp}\n")
            f.write(f"> **Answer**\n\n")
        elif label == "plan approved":
            f.write(f"\n## \u2705 User \u2014 {timestamp}\n")
            f.write(f"> **Plan Approved**\n\n")
        elif label == "tool rejected":
            f.write(f"\n## \u274c User \u2014 {timestamp}\n")
            reason = text if text else ""
            f.write(f"> **Tool Rejected**: {reason}\n\n") if reason else f.write(f"> **Tool Rejected**\n\n")
        elif label == "interrupt":
            f.write(f"\n## \u26a1 User \u2014 {timestamp}\n")
            f.write(f"> **Interrupted**\n\n")
        else:
            f.write(f"\n## \U0001f4ac User \u2014 {timestamp}\n")
            f.write(f"> **{label}**\n\n")

        if text and label not in ("tool rejected",):
            f.write(f"{text}\n")


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

        # Log directory
        log_dir = get_log_dir(cwd)

        debug_log(log_dir, f"=== Stop hook started ===")
        debug_log(log_dir, f"transcript_path: {transcript_path}")
        debug_log(log_dir, f"session_id: {session_id}")

        if not transcript_path or not os.path.exists(transcript_path):
            debug_log(log_dir, f"No transcript path found or file doesn't exist")
            print("No transcript path found", file=sys.stderr)
            sys.exit(0)

        # Read temp session to get format and log file path
        temp_data = read_temp_session(log_dir, session_id)
        if temp_data and temp_data.get("log_file_path"):
            log_format = temp_data.get("log_format", "text")
            log_file = temp_data.get("log_file_path")
        else:
            # Fallback: determine from config
            log_format = get_log_format(cwd)
            log_file = get_log_file_path(log_dir, session_id, log_format)

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
                            text = extract_user_interaction(entry, classification)
                            follow_ups.append(("answer", text))
                            all_outputs = []

                        elif classification == "PLAN_APPROVAL":
                            text = extract_user_interaction(entry, classification)
                            follow_ups.append(("plan approved", text))
                            all_outputs = []

                        elif classification == "TOOL_REJECTION":
                            text = extract_user_interaction(entry, classification)
                            if text:
                                all_outputs.append(("tool_rejection", f"  \u23bf  Tool use rejected with user message: {text}"))
                            else:
                                all_outputs.append(("tool_rejection", "  \u23bf  Tool use rejected"))

                        elif classification == "INTERRUPT":
                            all_outputs.append(("interrupt", "  \u23bf  Interrupted"))

                        elif classification == "TOOL_RESULT":
                            all_outputs = []

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
            timestamp = datetime.now().strftime('%H:%M:%S')

            if log_format == "markdown":
                _write_followups_markdown(f, follow_ups)

                formatted_parts = _format_output_markdown(all_outputs)
                response_text = "\n\n".join(formatted_parts) if formatted_parts else "[No output found]"
                f.write(f"\n## \U0001f916 Claude \u2014 {timestamp}\n\n")
                f.write(f"{response_text}\n")
            else:
                full_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                _write_followups_text(f, follow_ups)

                formatted_parts = _format_output_text(all_outputs)
                response_text = "\n\n".join(formatted_parts) if formatted_parts else "[No output found]"
                f.write(f"\U0001f916 CLAUDE [{full_timestamp}]:\n")
                f.write(f"{response_text}\n")
                f.write(f"{'='*80}\n\n")

        # Clean up temporary session file
        temp_file = os.path.join(log_dir, f".temp_session_{session_id}.json")
        if os.path.exists(temp_file):
            os.remove(temp_file)

        # Clean up stale temporary files
        cleanup_stale_temp_files(log_dir)

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
