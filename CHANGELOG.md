# 변경 이력 (Changelog)

이 프로젝트는 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

## [1.0.0] - 2026-06-21

최초 공개 릴리스. M.O.L.E (Steam app 4064510, build 1.1.5) 전체 한국어화.

### 추가
- **본문 번역 1300개** — Game.locres 전체 문자열 한국어화 (UI·시스템·아이템·대사·일기·문서).
- **엔진 키 표시명 115개** — Engine.locres의 키보드/마우스/스페이스/수정자/화살표/게임패드 키 이름 한국어화 (예: `左 Shift → 왼쪽 Shift`, `SpaceBarShort スペース → 스페이스`).
- **한글 폰트** — 게임 커스텀 폰트 6종을 Galmuri11(한글+영문+가나+한자)로 교체.
- **결정적 빌드** — `tools/build.py`로 사용자 게임 설치본에서 패치 pak 생성. repak을 단일 스레드로 호출해 같은 입력이면 **바이트 단위로 동일한** pak을 재현(프리빌트 SHA256과 일치).
- 검토용 데이터 공개 — `data/translations.tsv`(index·guid·en·ja·ko), `data/engine_keys.tsv`.
- 문서화 — 접근 전략, 역공학, 폰트, 번역 파이프라인, 엔진 키/버그, 전수 검증, 의사결정 로그.

### 수정
- 원작 일본어 로컬라이즈 버그(리터럴 `\r`)를 교정. 통신(메일) 위젯은 `{/n}` 토큰을 해석하지 않고 자동 줄바꿈하므로, 버그 문자열의 줄바꿈을 **공백으로 교체**(일기/문서 위젯의 정상 `{/n}`은 보존). → [docs/05](docs/05-engine-keys-and-bugs.md)

### 문서
- 제작 과정 전반을 정리한 [MADE-WITH-CLAUDE-CODE.md](MADE-WITH-CLAUDE-CODE.md) 추가.

### 검증
- IoStore 전수 스캔으로 하드코딩 일본어 0건 확인(모든 텍스트가 Game.locres 경유).
- 태그/코드/줄바꿈 보존, 고유명사 일관성 프로그램 검증 — 이슈 0.

[1.0.0]: https://github.com/showneykim/mole-kr-patch/releases/tag/v1.0.0
