# CLAUDE.md

## 프로젝트 개요

Claude Code 대화를 자동 로깅하고 세션 간 컨텍스트를 유지하는 플러그인 (v0.4.0). Python 3.6+ (stdlib only), Claude Code v1.0.33+.
UserPromptSubmit/Stop 훅으로 세션별 단일 로그 파일에 시간순 기록. 포맷: plain text(기본) / Markdown.
SessionStart/PreCompact 훅으로 MEMORY.md에 작업 상태를 자동 저장/복원 (context-keeper 기능 내장).

## Commands

```bash
claude --plugin-dir ./conversation-logger   # 로컬 플러그인 테스트
python -m unittest discover tests/ -v       # 전체 테스트
python -m unittest tests/test_classify.py -v  # 단일 파일 테스트
python -m unittest tests.test_classify.TestClassifyUserEntry -v  # 단일 클래스
python -m unittest tests.test_classify.TestClassifyUserEntry.test_tool_rejection -v  # 단일 메서드
```

- `/conversation-logger:setup` — 로그 포맷 및 context-keeper 설정
- `/conversation-logger:context-keeper` — MEMORY.md 상태 확인 및 관리

빌드 시스템, 린팅 없음. 외부 의존성 없는 순수 Python (stdlib only). 테스트는 unittest만 사용.

## 아키텍처

```
UserPromptSubmit 훅 (10s)    Stop 훅 (30s)      SessionStart/PreCompact 훅 (10s)
    │                            │                        │
    ▼                            ▼                        ▼
log-prompt.py              log-response.py          log-event.py
    │                            │                        │
    ├─ config 로드 (utils.py)    ├─ temp_session 읽기     ├─ 로그 기록
    ├─ 포맷별 프롬프트 기록        ├─ JSONL 파싱            ├─ [SessionStart] MEMORY.md 읽기
    └─ temp_session에             ├─ 포맷별 출력 생성       │    → additionalContext JSON 출력
       cwd/format/path 저장       └─ 로그 파일 append      └─ [PreCompact] MEMORY.md에
                                                               compaction marker 기록
```

- `scripts/` — 핵심 로직 (4개 모듈). stdlib만 허용, 외부 패키지 import 금지
  - `utils.py` — 공유 유틸리티 (config, encoding, 경로, temp 파일 I/O, context-keeper 함수)
  - `log-prompt.py` — UserPromptSubmit 훅. 사용자 프롬프트 기록
  - `log-response.py` — Stop 훅. 응답 분류/추출/포맷팅
  - `log-event.py` — 세션 이벤트 훅. SessionStart/End, SubagentStart/Stop, PreCompact, PostToolUseFailure 처리
- `hooks/hooks.json` — 훅 등록. `${CLAUDE_PLUGIN_ROOT}` 경로 변수 사용
- `skills/context-keeper/` — `/conversation-logger:context-keeper` Skill 정의
- `tests/` — unittest 기반. dev 브랜치에만 존재 (main 제외). 스크립트 파일명에 하이픈이 있어 `conftest.py`의 `import_script()` 헬퍼로 import
- `commands/setup.md` — `/conversation-logger:setup` 커맨드 정의
- `docs/architecture.md` — 상세 아키텍처 문서 (main 브랜치에 포함)

**Config**: 우선순위 `ENV (CONVERSATION_LOG_FORMAT)` > project `.claude/conversation-logger-config.json` > user `~/.claude/conversation-logger-config.json` > default (`"text"`)

**Context Keeper Config** (context_keeper 섹션은 ENV 무시, 파일 체인만):
```json
{
  "log_format": "text",
  "context_keeper": {
    "enabled": true,
    "scope": "user"
  }
}
```
scope: `"user"` (기본, `~/.claude/projects/<sanitized>/memory/MEMORY.md`) | `"project"` (`<cwd>/.context-keeper/memory/`) | `"local"` (`<cwd>/.context-keeper/memory.local/`)

**Key Files**: `scripts/log-response.py` (핵심 로직), `scripts/utils.py` (공유 모듈), `hooks/hooks.json` (훅 등록)
**Data Flow**: stdin(JSON) → log-prompt.py → temp_session 파일 → log-response.py → 세션 트랜스크립트(JSONL) 파싱 → 로그 파일 append

**중복 로깅 방지**: Stop 훅 입력 JSON의 `stop_hook_active` 플래그가 `true`면 즉시 종료. 프롬프트 훅 실패 시 응답 훅은 config 체인(utils.py)으로 설정 복원.

## Code Style

- 포맷 함수 네이밍: text용 `format_*()`, markdown용 `format_*_md()` (e.g., `format_tool_input()` / `format_tool_input_md()`)
- 분류 함수: `classify_user_entry()`가 반환하는 타입 문자열로 처리 분기: `"PROMPT"`, `"USER_ANSWER"`, `"PLAN_APPROVAL"`, `"TOOL_REJECTION"`, `"INTERRUPT"`, `"TOOL_RESULT"`, `"UNKNOWN"`
- config 로드: `utils.py`의 우선순위 체인 함수 사용 (e.g., `get_log_format(cwd)`)
- 에러 핸들링: `try/except → print(msg, file=sys.stderr) → sys.exit(1)`
- 로컬 import: `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` 후 `from utils import ...`
- 문자열 포맷팅: f-strings 사용, 유니코드 이모지는 escape sequence 사용 (e.g., `\U0001f464`)
- 디버그: `utils.py`의 `DEBUG = True`로 변경 → `.claude/logs/debug-response.log`에 기록

## 개발 원칙

**주의**: 이 원칙들은 속도보다 신중함을 우선한다. 사소한 작업에는 판단을 적용한다.

### 1. 코딩 전 사고

**가정하지 않는다. 혼란을 숨기지 않는다. 트레이드오프를 드러낸다.**

구현 전에:
- 가정을 명시적으로 서술한다. 불확실하면 질문한다.
- 다수의 해석이 존재하면 제시한다 — 조용히 선택하지 않는다.
- 더 단순한 접근이 있으면 말한다. 필요하면 반론을 제기한다.
- 무언가 불명확하면 멈춘다. 혼란스러운 부분을 명명하고 질문한다.

### 2. 단순함 우선

**문제를 해결하는 최소한의 코드. 투기적 추가 금지.**

- 요청된 것 이상의 기능 추가 금지.
- 일회성 코드에 추상화 금지.
- 요청하지 않은 "유연성"이나 "설정 가능성" 금지.
- 불가능한 시나리오를 위한 에러 핸들링 금지.
- 200줄로 작성했는데 50줄로 가능하다면, 다시 작성한다.

스스로 묻는다: "시니어 엔지니어가 이게 과복잡하다고 할까?" 그렇다면 단순화한다.

### 3. 최소 변경

**반드시 필요한 것만 수정한다. 자신이 만든 mess만 정리한다.**

기존 코드를 수정할 때:
- 인접한 코드, 주석, 포맷을 "개선"하지 않는다.
- 망가지지 않은 것을 리팩터링하지 않는다.
- 다르게 하고 싶더라도 기존 스타일을 따른다.
- 무관한 dead code를 발견하면 언급한다 — 삭제하지 않는다.

자신의 변경이 orphan을 만들었을 때:
- 자신의 변경으로 unused가 된 import/변수/함수는 제거한다.
- 기존에 존재하던 dead code는 요청 없이 제거하지 않는다.

판단 기준: 변경된 모든 줄이 사용자의 요청으로 직접 추적되어야 한다.

### 4. 목표 기반 실행

**성공 기준을 정의한다. 검증될 때까지 반복한다.**

작업을 검증 가능한 목표로 변환한다:
- "유효성 검사 추가" → "잘못된 입력에 대한 테스트 작성 후 통과시키기"
- "버그 수정" → "재현 테스트 작성 후 통과시키기"
- "X 리팩터링" → "전후로 테스트 통과 확인"

다단계 작업에서는 간략한 계획을 제시한다:
```
1. [단계] → 검증: [확인 방법]
2. [단계] → 검증: [확인 방법]
3. [단계] → 검증: [확인 방법]
```

명확한 성공 기준은 독립적 반복을 가능하게 한다. 모호한 기준("작동하게 만들기")은 지속적인 명확화를 요구한다.

## Critical Rules

- NEVER print 문에 유니코드 문자 사용 — Windows 호환성 깨짐 (e.g., `print("✓")` 금지)
- NEVER `python3` 명령 사용 — Windows PATH 호환성 위해 항상 `python` 사용
- NEVER 문자열 매칭 시 ASCII 아포스트로피(`'`)만 가정 — Claude 응답에 유니코드 아포스트로피(`\u2019`)가 포함됨
- NEVER `scripts/` 디렉토리에서 외부 패키지 import — Python 표준 라이브러리만 허용
- ALWAYS `tests/` 디렉토리는 dev 브랜치에만 유지 — main 머지 시 반드시 제외 (`.claude/rules/merge-strategy.md` 참조)
- ALWAYS 로그 파일 경로: `{프로젝트}/.claude/logs/YYYY-MM-DD_{session_id}_conversation-log.{txt|md}`
