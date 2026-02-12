# CLAUDE.md

## 프로젝트 개요

Claude Code 대화를 자동 로깅하는 플러그인 (v0.2.2). Python 3.6+, Claude Code v1.0.33+.
UserPromptSubmit/Stop 훅으로 세션별 단일 로그 파일에 시간순 기록. 포맷: plain text(기본) / Markdown.

## Commands

```bash
claude --plugin-dir ./conversation-logger   # 로컬 플러그인 테스트
python -m unittest discover tests/ -v       # 전체 테스트
python -m unittest tests/test_classify.py -v  # 단일 파일 테스트
```

- `/conversation-logger:setup` — 로그 포맷 설정 (text/markdown)

빌드 시스템, 린팅 없음. 외부 의존성 없는 순수 Python. 테스트는 unittest만 사용.

## 아키텍처

```
UserPromptSubmit 훅               Stop 훅
    │                              │
    ▼                              ▼
log-prompt.py                 log-response.py
    │                              │
    ├─ config 로드 (utils.py)      ├─ temp_session에서 포맷/경로 읽기
    ├─ 포맷별 프롬프트 기록          ├─ 세션 트랜스크립트(JSONL) 파싱
    └─ temp_session에               ├─ 포맷별 출력 생성
       cwd/format/path 저장         └─ 로그 파일에 추가
```

- `scripts/` — 핵심 로직 (3개 모듈). 외부 import 금지
  - `utils.py` — 공유 유틸리티 (config, encoding, 경로, temp 파일 I/O)
  - `log-prompt.py` — UserPromptSubmit 훅. 사용자 프롬프트 기록
  - `log-response.py` — Stop 훅. 응답 분류/추출/포맷팅
- `hooks/hooks.json` — 훅 등록. `${CLAUDE_PLUGIN_ROOT}` 경로 변수 사용
- `tests/` — unittest 기반. dev 브랜치에만 존재 (main 제외)
- `commands/setup.md` — `/conversation-logger:setup` 커맨드 정의

**Key Files**: `scripts/log-response.py` (핵심 로직), `scripts/utils.py` (공유 모듈), `hooks/hooks.json` (훅 등록)
**Data Flow**: stdin(JSON) → log-prompt.py → temp_session 파일 → log-response.py → 세션 트랜스크립트(JSONL) 파싱 → 로그 파일 append

## 설정

| Scope | 경로 |
|-------|------|
| Global | `~/.claude/conversation-logger-config.json` |
| Project | `{project}/.claude/conversation-logger-config.json` |

우선순위: `ENV (CONVERSATION_LOG_FORMAT)` > project config > user config > default (`"text"`)

## Code Style

- 포맷 함수 네이밍: text용 `format_*()`, markdown용 `format_*_md()` (e.g., `format_tool_input()` / `format_tool_input_md()`)
- 분류 함수: `classify_user_entry()`가 반환하는 타입 문자열로 처리 분기 (e.g., `"TOOL_REJECTION"`, `"PLAN_MODE"`)
- config 로드: `utils.py`의 우선순위 체인 함수 사용 (e.g., `get_log_format(cwd)`)
- 디버그: `utils.py`의 `DEBUG = True`로 변경 → `.claude/logs/debug-response.log`에 기록

## Critical Rules

- NEVER print 문에 유니코드 문자 사용 — Windows 호환성 깨짐 (e.g., `print("✓")` 금지)
- NEVER `python3` 명령 사용 — Windows PATH 호환성 위해 항상 `python` 사용
- NEVER 문자열 매칭 시 ASCII 아포스트로피(`'`)만 가정 — Claude 응답에 유니코드 아포스트로피(`\u2019`)가 포함됨
- ALWAYS `tests/` 디렉토리는 dev 브랜치에만 유지 — main 머지 시 반드시 제외 (`.claude/rules/merge-strategy.md` 참조)
- ALWAYS 로그 파일 경로: `{프로젝트}/.claude/logs/YYYY-MM-DD_{session_id}_conversation-log.{txt|md}`
