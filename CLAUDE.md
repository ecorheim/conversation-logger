# CLAUDE.md

이 문서는 Claude Code (claude.ai/code)가 본 저장소에서 코드를 다룰 때 따라야 할 **행동 지침 및 프로젝트 정보**를 정의합니다.

- **실행 규칙**: `.claude/rules/` 디렉토리 (자동 로드)

---

## Scope

- CLAUDE.md는 **프로젝트 요약**만 제공, 행동 규칙은 `.claude/rules/`에서 자동 로드

---

## 프로젝트 개요

두 개의 훅 스크립트와 공유 유틸리티 모듈을 통해 Claude Code 대화를 자동으로 로깅하는 플러그인. 사용자 프롬프트(UserPromptSubmit 훅)와 Claude 응답 및 도구 사용 내역(Stop 훅)을 세션별 단일 로그 파일에 시간순으로 기록한다. 로그 포맷은 plain text(기본)와 Markdown 중 선택 가능하다.

## 개발 환경

**요구사항:** Python 3.6+, Claude Code v1.0.33+

**로컬 테스트:**
```bash
claude --plugin-dir ./conversation-logger
```

**단위 테스트:**
```bash
python -m unittest discover tests/ -v
```

**로그 위치:** `{프로젝트}/.claude/logs/YYYY-MM-DD_{session_id}_conversation-log.{txt|md}`

**디버그 모드:** `scripts/utils.py`의 `DEBUG = True`로 변경하면 `.claude/logs/debug-response.log`에 디버그 로그가 기록된다.

빌드 시스템, 린팅 없음. 외부 의존성 없는 순수 Python. 테스트는 `unittest` 표준 라이브러리만 사용.

## 설정 시스템

### 설정 파일 위치

| Scope | 경로 |
|-------|------|
| Global | `~/.claude/conversation-logger-config.json` |
| Project | `{project}/.claude/conversation-logger-config.json` |

### 우선순위: `ENV (CONVERSATION_LOG_FORMAT)` > project config > user config > default (`"text"`)

### Setup 커맨드: `/conversation-logger:setup`

## 아키텍처

세 Python 모듈이 공유 로그 파일과 임시 세션 파일로 연결된 파이프라인 구조:

```
UserPromptSubmit 훅               Stop 훅
    │                              │
    ▼                              ▼
log-prompt.py                 log-response.py
    │                              │
    ├─ config 로드 (utils.py)      ├─ temp_session에서 포맷/경로 읽기
    ├─ 포맷별 프롬프트 기록          ├─ 세션 트랜스크립트(JSONL) 읽기
    └─ temp_session에               ├─ 마지막 턴의 콘텐츠 추출
       cwd/format/path 저장         ├─ 포맷별 출력 생성 (text/markdown)
                                   ├─ 응답을 동일 로그 파일에 추가
                                   └─ 오래된 임시 파일 정리 (1시간 초과)
```

### `scripts/utils.py` 공유 모듈

- `setup_encoding()` — Windows UTF-8 래핑
- `get_log_dir(cwd)` / `get_log_file_path()` — 로그 경로 생성
- `load_config(cwd)` / `get_log_format(cwd)` — 우선순위 체인 config 로드
- `read_temp_session()` / `write_temp_session()` — 임시 세션 파일 I/O
- `cleanup_stale_temp_files()` — 1시간 초과 temp 파일 정리
- `debug_log()` — 디버그 로그 기록
- `calculate_fence()` — 동적 backtick 수 계산 (Markdown 코드 블록 충돌 방지)

### `scripts/log-response.py` 핵심 함수

- `classify_user_entry()` — 트랜스크립트의 항목 유형을 판별하여 처리 방식 결정
- `extract_full_content()` — 트랜스크립트 항목에서 텍스트, tool_use, tool_result 추출
- `format_tool_input()` / `format_tool_input_md()` — 도구 호출 포맷팅 (text/markdown)
- `format_tool_result()` / `format_tool_result_md()` — 도구 출력 포맷팅 (잘림 없음)
- `extract_user_interaction()` — 후속 상호작용에서 사용자의 실제 답변/피드백 추출

### 훅 설정

`hooks/hooks.json`에 두 스크립트가 등록되어 있다. 경로 해석에 `${CLAUDE_PLUGIN_ROOT}`를 사용한다. Windows 호환성을 위해 `python3`가 아닌 `python` 명령을 사용한다.

### 플러그인 메타데이터

- `.claude-plugin/plugin.json` — 플러그인 이름, 버전, 저자, commands
- `.claude-plugin/marketplace.json` — 마켓플레이스 카탈로그 설정 (ecorheim-plugins)

## Windows 호환성

`utils.py`의 `setup_encoding()`으로 `win32` 플랫폼에서 stdin/stdout/stderr를 UTF-8 TextIOWrapper로 래핑한다. PATH에 `python` 명령이 있어야 한다 (`python3` 아님). 호환성을 위해 print 문에서 유니코드 문자를 사용하지 않는다.