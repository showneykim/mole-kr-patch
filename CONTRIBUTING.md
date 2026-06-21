# 기여 가이드

번역 개선·버그 제보·코드 기여를 환영합니다. 이 패치의 목표는 **자연스럽고 정확한 한국어**입니다.

## 번역 수정 제안

번역 텍스트는 **원문(일본어) → 한국어** 매핑으로 관리됩니다.

- 사람이 검토하기 좋은 표: [`data/translations.tsv`](data/translations.tsv) — `index, key_guid, english, japanese, korean` 열.
- 빌드에 실제로 쓰이는 파일: [`data/translations.json`](data/translations.json) — `{"일본어 원문": "한국어"}`.
- 엔진 키 이름: [`data/engine_keys.json`](data/engine_keys.json) / [`.tsv`](data/engine_keys.tsv).

### 수정 절차
1. `data/translations.tsv`에서 고치고 싶은 줄을 찾습니다(인덱스/영어/일본어로 검색).
2. `data/translations.json`에서 해당 **일본어 키**의 값을 새 한국어로 바꿉니다.
   - ⚠️ JSON 키(일본어 원문)는 **절대 수정 금지** — 키가 바뀌면 게임에서 매칭되지 않습니다.
   - 보존 규칙: `{/n}`(줄바꿈), `[ENTER]`/`[001-032]`/버전·주파수·좌표·단위·16진 에러코드는 그대로 두세요.
   - 용어는 [`tools/glossary.md`](tools/glossary.md)를 따르세요(두더지, 굴착기, 항해사, 승조원 등).
3. (선택) `data/translations.tsv`의 `korean` 열도 같이 갱신하면 리뷰가 쉬워집니다.
4. 다시 빌드해 실제로 확인합니다(아래).
5. PR을 올립니다. 어떤 화면의 어떤 문장인지, 가능하면 스크린샷을 첨부해 주세요.

## 빌드해서 확인하기

```bash
bash scripts/setup_tools.sh                 # repak 설치 (최초 1회)
python tools/build.py --game "<게임 설치 경로>" --install
```

게임을 완전히 종료 후 재실행하고 언어를 **日本語**로 설정해 확인합니다.
원리·도구 설명은 [`docs/`](docs/)를 참고하세요.

## 코드 기여

- `tools/locres.py`(LocRes v3 입출력), `tools/build.py`(빌드)는 표준 라이브러리만 사용합니다.
- 변경 시 `python tools/locres.py check <locres>`로 라운드트립 무손실을 확인하세요.

## 행동 규범

원작자(Z Labs)와 게임을 존중합니다. 이 프로젝트는 비상업 팬 패치이며, 게임을 정식 소유한 사용자만을 대상으로 합니다. 자세한 내용은 [DISCLAIMER.md](DISCLAIMER.md).
