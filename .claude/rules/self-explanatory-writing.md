# 자기 설명적 작성 원칙

## 적용 범위

- CHANGELOG.md
- 커밋 메시지
- 사용자에게 보이는 모든 텍스트

## 금지: 내부 용어 사용

프로젝트 내부에서만 통용되는 용어를 사용자 대면 텍스트에 사용하지 않는다.

**내부 용어 예시**:
- `Phase 0`, `Phase 1`, `Phase 3G`, `Phase 3I`, `Phase 3A`, `Phase 3S`, `Phase 4`
- `RC-1`, `RC-2` 등 내부 추적 ID
- `Step 1 — Pruning`, `Step 2 — Progressive Disclosure` 등 내부 워크플로우 단계명

## 원칙: 기능 중심 서술

내부 구현 위치가 아닌, **사용자가 체감하는 기능 변화**를 기술한다.

**❌ 나쁜 예**:
```
- Phase 0에 settings.json 로딩 단계 추가
- Phase 4에 백업 메커니즘 추가
```

**✅ 좋은 예**:
```
- 커맨드 실행 시 `.claude/settings.json` 설정 자동 로딩
- improve/sync 모드에서 기존 CLAUDE.md 자동 백업
```

## 판단 기준

"이 프로젝트의 코드를 한 번도 본 적 없는 사용자가 이 문장만 읽고 변경 내용을 이해할 수 있는가?"
