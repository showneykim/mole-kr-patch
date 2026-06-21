# 이 패치는 어떻게 만들어졌나 — Made with Claude Code

> **이 프로젝트의 거의 모든 과정 — 게임 역공학, 파일 포맷 분석, 폰트 문제 해결, 1,300개 문자열 번역, 전수 검증, 빌드 도구·문서·저장소 구성까지 — 은 [Claude Code](https://claude.com/claude-code)(Anthropic의 에이전트형 코딩 CLI)를 통해 수행되었습니다.** 이 문서는 그 과정을 투명하게 기록하기 위한 것이며, 궁금해하는 사람과 다른 AI 에이전트 모두를 독자로 상정합니다.

이 문서를 따로 둔 이유는 두 가지입니다. (1) **투명성** — AI가 무엇을 했고 사람이 무엇을 결정했는지 분명히 밝히기 위해. (2) **재현성과 학습** — 같은 방법론으로 다른 게임/문제에 접근하려는 사람이나 에이전트가 참고할 수 있도록.

---

## 1. 한눈에

| | |
|---|---|
| 도구 | Claude Code (Anthropic agentic CLI) |
| 모델 | Claude Opus 4.8 (1M context) |
| 작업 환경 | WSL2(Ubuntu) — Windows Steam 설치본을 `/mnt/c`로 접근 |
| 사람의 역할 | 목표 제시 · 게임 실행/스크린샷 제공 · 인게임 검수 · 의사결정 승인 · 톤·용어 지침 |
| AI의 역할 | 역공학 · 포맷 분석 · 도구 사용 · 번역 · 검증 · 코드·문서·저장소 작성 |
| 결과물 | 단일 `_P.pak` 패치 + 결정적 빌드 파이프라인 + 전 과정 문서 |

이 프로젝트는 "AI에게 통째로 맡긴 것"이 아니라 **사람-AI 협업**입니다. 사람은 화면을 보고(에이전트는 게임 화면을 볼 수 없습니다) 방향과 검수를 맡았고, AI는 분석·구현·문서화의 본체를 수행했습니다.

---

## 2. 사람이 한 것 vs AI가 한 것

에이전트는 **게임 화면을 직접 볼 수 없고**, Windows에서 실행 중인 게임 프로세스에도 접근할 수 없습니다. 그래서 역할이 자연스럽게 나뉘었습니다.

**사람이 한 것**
- "이 게임 한글 패치가 가능한가?"라는 목표와 게임 설치 경로 제시
- 게임을 실제로 실행하고 **각 단계의 스크린샷 제공**(폰트가 깨지는지, 한글이 나오는지 등) — 에이전트의 유일한 "눈"
- 공식 스팀 한국어 페이지의 용어·톤을 지침으로 제공(두더지/굴착기/항해사/승조원…)
- 놓친 부분 지적(예: `左 Shift`가 한자로 남음, `\r`이 글자로 보임)
- 의사결정 승인(배포 방식, 라이선스, 공개 여부)

**Claude Code가 한 것**
- 게임이 UE5 IoStore 구조임을 식별하고, 텍스트·폰트가 레거시 pak에 있음을 발견
- `repak`/`retoc` 도구를 직접 내려받아 사용
- UE LocRes v3 바이너리 포맷을 **바이트 단위로 역분석**하고 무손실 파서를 작성
- 폰트 문제를 가설-검증 루프로 좁혀 해결(6종 전부 교체, Galmuri11)
- 1,300개 문자열을 멀티에이전트로 번역하고 교차검증
- IoStore를 풀어 **하드코딩 누락이 없음을 전수 검증**
- 결정적 빌드 파이프라인, 저장소 구조, 모든 문서를 작성

---

## 3. 방법론 하이라이트 — 에이전트가 실제로 일한 방식

이 프로젝트가 흥미로운 이유는 결과물보다 **방법** 때문일 수 있습니다.

### (a) 에이전트형 역공학 — 가설·도구·검증의 루프
에이전트는 "한글 패치는 무조건 된다"고 단정하지 않았습니다. 대신 게임 파일을 직접 열어 엔진을 식별하고, 암호화 여부를 확인하고, 텍스트가 어느 컨테이너에 있는지 좁혀 갔습니다. LocRes 포맷은 표준 파서가 깨졌기 때문에, **헤더+엔트리를 불투명 바이트로 보존하고 문자열 테이블만 다시 쓰는** 우회 전략을 세워 *원본을 바이트 단위로 무손실 복원*함을 먼저 증명한 뒤 편집에 들어갔습니다. (→ [02-reverse-engineering](docs/02-reverse-engineering.md))

### (b) 사람을 "센서"로 쓴 폰트 디버깅
에이전트는 화면을 못 보므로, **한 글자만 바꾼 테스트 패치**를 만들어 사람에게 "이게 □로 보이나요, 한글로 보이나요?"를 물으며 범위를 좁혔습니다. 이 루프로 "UE는 `.ufont`을 크기와 무관하게 통째로 읽는다", "UI마다 다른 폰트를 쓴다", "한자 없는 폰트는 미번역 일본어를 깨뜨린다" 같은 사실을 하나씩 확정했습니다. (→ [03-fonts](docs/03-fonts.md))

### (c) 멀티에이전트 번역 워크플로
1,300개 문자열을 문체(register)별 33개 배치로 나눈 뒤, 각 배치를 **[번역 → 3개 독립 검수자의 병렬 교차검증(정확성/용어·문체/포맷) → 교정]** 파이프라인으로 처리했습니다. 약 **165개의 서브에이전트**가 동작했고 **105건의 검수 지적**이 반영되었습니다. 이어서 사람이 아닌 *프로그램*이 태그·줄바꿈·고유명사 일관성을 다시 검증했습니다(불일치 0). (→ [04-translation](docs/04-translation.md))

### (d) 병렬 컨텍스트 포크로 문서 작성
이 저장소의 기술 문서들은 **6개의 병렬 에이전트**가 동시에 작성했습니다. 각 에이전트는 전체 작업 맥락을 그대로 물려받아(컨텍스트 포크), 자신이 1차 경험한 내용을 문서로 풀었습니다.

### (e) 프로그램적 전수 검증
"빠진 텍스트가 없나?"라는 질문에 감으로 답하지 않고, IoStore(857MB)를 **압축 해제(3.1GB)** 한 뒤 모든 에셋을 바이트 스캔했습니다. 핵심 추론은 *"게임 소스가 영어라, 제대로 현지화된 텍스트는 에셋에 영어로 박히고 일본어는 locres에만 있다 → 에셋에서 일본어 단어가 나오면 하드코딩 누락"* 이었고, 실제 일본어 게임 단어는 **0건**이었습니다. (→ [06-verification](docs/06-verification.md))

---

## 4. 정직한 한계 (꼭 읽어주세요)

AI가 주도했다는 사실은 강점인 동시에 **한계**이기도 합니다.

- **번역은 사람 검수가 필요합니다.** 기계 번역은 문맥·말투(특히 대사의 반말/존댓말)·서사적 뉘앙스에서 틀릴 수 있습니다. 이 패치는 교차검증과 용어 고정으로 품질을 높였지만, **플레이 검수로 다듬어야 할 여지가 있습니다.** 오류 제보·수정 PR을 환영합니다(→ [CONTRIBUTING](CONTRIBUTING.md)).
- **에이전트는 화면을 못 봅니다.** 시각적 확인은 전적으로 사람의 스크린샷에 의존했습니다.
- **원작 버그를 그대로 옮길 수 있습니다.** 실제로 원작의 리터럴 `\r` 버그를 충실히 따라갔다가, 사람이 지적한 뒤 교정했습니다(→ [05](docs/05-engine-keys-and-bugs.md)).
- **이것은 비공식 팬 패치입니다.** 법적·윤리적 고지는 [DISCLAIMER](DISCLAIMER.md)를 따릅니다.

검증 가능성으로 이 한계를 보완합니다: 번역 데이터는 사람이 읽을 수 있는 형태로 공개(`data/translations.tsv`)되고, 빌드는 **결정적**이며, 모든 추론은 `docs/`에 기록되어 **누구나(사람이든 AI든) 검토·재현**할 수 있습니다.

---

## 5. AI 에이전트를 위한 메모 (For AI agents)

다른 에이전트가 이 저장소를 이해하거나 유사 작업을 재현하려 한다면, 아래가 출발점입니다.

```yaml
project: mole-kr-patch
type: unofficial fan localization (Japanese-slot hijack)
target: M.O.L.E (Steam app 4064510), Unreal Engine 5, build 1.1.5
strategy: overwrite the unused 'ja' locale; user selects 日本語 in-game
key_invariants:
  - game text & fonts live in the LEGACY pak (Mole-Windows.pak), not IoStore
  - override via a higher-priority '_P' pak (repak; V11, mount ../../../, seed 0x498B9334)
  - LocRes v3: keep header+entry-table opaque, rewrite only the string table (lossless)
  - translations keyed by JAPANESE SOURCE STRING (robust to index shifts; 1300 unique, 0 conflicts)
  - replace ALL 6 custom .ufont (raw TTF) with a Hangul+Latin+kana+Hanja font (Galmuri11)
  - in-game key prompts come from Engine.locres InputKeys (long + 'Short' display names)
  - source culture is English -> no hardcoded Japanese in IoStore (verified by byte scan)
reproduce:
  - bash scripts/setup_tools.sh
  - python tools/build.py --game <M.O.L.E path> --install   # deterministic (RAYON_NUM_THREADS=1)
verify:
  - python tools/locres.py check <locres>   # round-trip lossless
  - data/translations.tsv (index, key_guid, en, ja, ko) is the human-reviewable source of truth
entry_points: [tools/locres.py, tools/build.py, data/translations.json, docs/]
```

핵심 교훈을 하나만 남긴다면: **단정하지 말고, 가장 싼 검증부터 하라.** 한 글자 테스트 패치, 라운드트립 무손실 확인, 바이트 스캔 같은 작은 검증들이 큰 잘못된 가정을 막았습니다.

---

## 6. 크레딧

- **Claude Code** · Claude Opus 4.8 (1M context) — Anthropic
- 사람 협업자 — 방향·검수·의사결정
- 도구: [repak](https://github.com/trumank/repak) · [retoc](https://github.com/trumank/retoc) (trumank)
- 폰트: [Galmuri](https://galmuri.quiple.dev) (quiple, SIL OFL 1.1)

이 페이지를 포함해, 이 저장소의 코드·문서·번역은 Claude Code와의 협업으로 작성되었습니다. 더 궁금한 점이나 개선 제안은 이슈로 남겨주세요.
