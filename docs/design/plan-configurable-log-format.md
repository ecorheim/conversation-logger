# Plan: Configurable Markdown Log Format with Setup Command

> **Status**: Planning complete, ready for implementation
> **Target Version**: 0.2.0
> **Date**: 2026-02-11

## Problem

conversation-logger 플러그인이 현재 plain text(`.txt`)로만 로그를 출력한다. VS Code, GitHub 등에서 가독성이 좋은 Markdown(`.md`) 포맷 옵션이 필요하다.

## Solution

사용자가 `/conversation-logger:setup` 슬래시 커맨드로 로그 포맷(text/markdown)을 선택할 수 있는 설정 시스템을 추가한다.

## Architecture

```
User runs /conversation-logger:setup
  -> Claude asks format preference (text/markdown)
  -> Writes config.json in plugin root

Hook fires (UserPromptSubmit / Stop)
  -> Python script reads config.json
  -> Outputs in selected format
```

## Design Decisions

### 1. 설정 저장 위치: `{plugin_root}/config.json`

- Claude Code에는 플러그인 설정 UI가 없음
- 플러그인 루트 경로는 `__file__` 기반 탐색으로 발견 (`os.path.dirname(script_dir)`)
- Setup command에서는 `!echo ${CLAUDE_PLUGIN_ROOT}`로 경로 주입

### 2. 포맷 우선순위

1. 환경변수 `CONVERSATION_LOG_FORMAT` (최우선)
2. `{plugin_root}/config.json`의 `log_format` 필드
3. 기본값 `"text"` (하위 호환성)

### 3. 세션 중 포맷 일관성 (Issue #5)

프롬프트-응답 쌍이 동일한 파일에 기록되도록 `temp_session` 파일에 `log_format`을 저장한다.

- `log-prompt.py`: `get_log_format()` 결과를 temp_session에 저장
- `log-response.py`: temp_session의 `log_format`을 우선 읽고, 없으면 `get_log_format()` fallback

## Known Issues & Mitigations

| # | Issue | Severity | Solution |
|---|-------|----------|----------|
| 1 | Tool results의 ``` 가 fenced code block과 충돌 | **High** | 4-backtick(``````) 펜싱 사용 |
| 2 | 빈 .md 파일의 `---` 시작이 YAML front matter로 해석 | **Medium** | 새 파일 생성 시 `# Conversation Log` 헤더 추가 |
| 3 | Claude Code에 플러그인 설정 UI 없음 | **Medium** | Setup slash command 패턴 사용 |
| 4 | Setup command에서 플러그인 루트 경로 모름 | **High** | `!echo ${CLAUDE_PLUGIN_ROOT}` 사용 |
| 5 | 세션 중 포맷 전환 시 프롬프트/응답 파일 분리 | **Medium** | temp_session에 log_format 저장 |
| 6 | 플러그인 캐시 업데이트 시 config.json 초기화 가능 | **Low** | README에 알려진 제한사항으로 문서화 |

## Files to Create/Modify

### 1. `commands/setup.md` (NEW)

Setup slash command 정의. `/conversation-logger:setup` 으로 실행된다.

```yaml
---
name: setup
description: Configure conversation-logger plugin settings (log format)
---
```

**내용 요약:**
- `!echo ${CLAUDE_PLUGIN_ROOT}`로 플러그인 루트 경로 주입
- Claude에게 5단계 지시: config 읽기 -> 현재 설정 표시 -> 포맷 선택 질문 -> config 쓰기 -> 확인
- 포맷 선택지: text (기본값), markdown

### 2. `.claude-plugin/plugin.json`

- `version`: `"0.1.3"` -> `"0.2.0"`
- `commands` 필드 추가: `["commands/"]`

### 3. `scripts/log-prompt.py`

**추가: `get_log_format()` 함수**
```python
def get_log_format():
    """Get log format: 'text' or 'markdown'."""
    # 1. Environment variable (highest priority)
    env_fmt = os.environ.get("CONVERSATION_LOG_FORMAT", "").lower()
    if env_fmt in ("text", "markdown"):
        return env_fmt
    # 2. Plugin root config.json (discovered via script path)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.dirname(script_dir)
    config_path = os.path.join(plugin_root, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                fmt = config.get("log_format", "").lower()
                if fmt in ("text", "markdown"):
                    return fmt
        except:
            pass
    # 3. Default
    return "text"
```

**수정: `log_prompt()` 함수**
- `log_format = get_log_format()` 호출
- 파일 확장자 분기: `.md` if markdown, `.txt` if text
- Markdown 포맷 출력 분기:
  - 새 파일: `# Conversation Log -- {date}` 헤더
  - 프롬프트: `---` + `## 👤 User -- {timestamp}` + `> Session: \`{id}\`` + 본문
- Text 포맷: 기존 코드 유지 (하위 호환)
- temp_session에 `"log_format": log_format` 필드 추가

### 4. `scripts/log-response.py`

**추가: 동일한 `get_log_format()` 함수**

**수정: `format_tool_input()` — `use_markdown` 파라미터 추가**
- Markdown: ``- **Tool:** `{tool_name}({params})`  ``
- Text: 기존 `● {tool_name}({params})` 유지

**수정: `format_tool_result()` — `use_markdown` 파라미터 추가**
- Markdown: 4-backtick 코드 블록으로 감싸기
- Text: 기존 `  ⎿  {line}` 유지

**수정: `extract_full_content()` — `use_markdown` 파라미터 추가**
- Markdown에서는 text 항목에 `●` 접두사 제거
- `format_tool_input()`, `format_tool_result()` 호출 시 `use_markdown` 전달

**수정: `log_response()` 함수**
- temp_session에서 `log_format` 우선 읽기 (프롬프트-응답 일관성)
- fallback: `get_log_format()` 호출
- 파일 확장자 분기
- tool_rejection, interrupt 마크다운 포맷 분기
- Smart join: markdown에서 tool_use + tool_result 연결
- 출력 포맷 분기:
  - Markdown: `## 👤 User _({label})_` + `## 🤖 Claude -- {timestamp}`
  - Text: 기존 포맷 유지

### 5. `README.md`

- **Configuration** 섹션 추가: setup command 설명, config.json 구조
- 두 포맷 예시 (text, markdown) 추가
- 파일 확장자 `.txt`/`.md` 병기
- 플러그인 업데이트 후 setup 재실행 안내 추가
- Plugin Structure에 `commands/` 디렉토리 추가

### 6. `.claude-plugin/marketplace.json`

- `metadata.version`: `"0.1.3"` -> `"0.2.0"`
- `plugins[0].version`: `"0.1.3"` -> `"0.2.0"`

### 7. `CHANGELOG.md`

```markdown
## [0.2.0] - YYYY-MM-DD

### Added
- Setup command (`/conversation-logger:setup`) for interactive configuration
- Configurable log format: plain text (default) or Markdown
- Plugin root config.json for persistent settings (discovered via script path)
- Environment variable override (CONVERSATION_LOG_FORMAT)
- Markdown format: headings, code blocks, horizontal rules, blockquotes
- Document header for new Markdown logs to prevent YAML front matter misinterpretation
- 4-backtick fencing in Markdown to prevent triple-backtick collision in tool results
```

## Output Format Examples

### Plain text (default, unchanged)

```
================================================================================
[2026-02-09 08:17:27] Session: abc123
================================================================================
👤 USER:
Write a hello world program
--------------------------------------------------------------------------------
🤖 CLAUDE [2026-02-09 08:21:57]:
● Here's the program.

● Write(file_path=hello.py)
  ⎿  print('Hello, World!')
================================================================================
```

### Markdown (opt-in)

````markdown
# Conversation Log — 2026-02-09

---

## 👤 User — 2026-02-09 08:17:27
> Session: `abc123`

Write a hello world program

## 🤖 Claude — 2026-02-09 08:21:57

Here's the program.

- **Tool:** `Write(file_path=hello.py)`
  ````
  print('Hello, World!')
  ````
````

## Verification Checklist

- [ ] 설정 없이 기본 `.txt` 출력 (하위 호환)
- [ ] `/conversation-logger:setup`으로 markdown 선택 -> `config.json` 생성 확인
- [ ] Markdown 설정 후 세션 -> `.md` 파일 생성 및 포맷 확인
- [ ] `CONVERSATION_LOG_FORMAT=markdown` 환경변수가 config.json 오버라이드
- [ ] Tool result에 triple backtick 포함 시 4-backtick 정상 동작
- [ ] Follow-up, interrupt, tool rejection 마크다운 포맷
- [ ] 포맷 text로 변경 -> `.txt` 출력 복원
- [ ] 세션 중 포맷 전환 시 프롬프트-응답 동일 파일 기록
