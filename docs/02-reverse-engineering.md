# 02. 역공학 / 포맷 분석

> 요약: M.O.L.E은 **언리얼 엔진 5(UE5)** 게임이며, 게임 텍스트와 폰트가 **암호화 없이** IoStore가 아닌 **레거시 `.pak`에 loose 파일로** 들어있다는 점이 패치를 가능하게 한 핵심이다. 텍스트는 UE의 **LocRes v3(Optimized_CityHash64_UTF16)** 포맷이며, 이 문서는 그 바이트 구조와 우리가 만든 파서(`tools/locres.py`)의 동작 원리를 기록한다.

관련 문서: 전체 전략은 [01-approach.md](01-approach.md), 폰트는 [03-fonts.md](03-fonts.md), 번역 파이프라인은 [04-translation.md](04-translation.md), 엔진 키/버그는 [05-engine-keys-and-bugs.md](05-engine-keys-and-bugs.md), 누락 검증은 [06-verification.md](06-verification.md), 결정 근거는 [DECISIONS.md](DECISIONS.md).

---

## 1. 게임 식별

설치 경로: `…/steamapps/common/M.O.L.E/Windows/`

```
Windows/
├── MOLE.exe
├── Manifest_UFSFiles_Win64.txt      # UFS(쿡된) 파일 매니페스트
├── Manifest_NonUFSFiles_Win64.txt
├── Engine/                          # ← UE 엔진 컨텐츠 (엔진임을 확정)
└── Mole/                            # 프로젝트명 = "Mole"
    └── Content/Paks/
```

`Engine/` 폴더 + `Manifest_UFSFiles_Win64.txt` + `Paks/` 구성은 전형적인 **UE 패키징**이다. 프로젝트명은 `Mole`.

### Paks 구성

| 파일 | 크기 | 종류 |
|---|---|---|
| `Mole-Windows.pak` | 42,272,645 B (≈42MB) | **레거시 pak** (loose 쿡 파일) |
| `Mole-Windows.ucas` | 857,611,872 B (≈857MB) | **IoStore** 컨테이너 (uasset/벌크) |
| `Mole-Windows.utoc` | 1,825,091 B | IoStore 디렉터리 인덱스 |
| `global.ucas` / `global.utoc` | 2.4MB / 638 B | IoStore 글로벌 |

UE5의 IoStore(`.ucas`/`.utoc`)는 uasset을 청크 ID로 저장해 직접 편집이 까다롭지만, **`.locres`/`.ufont`/`.ini` 같은 일부 쿡 파일은 IoStore가 아니라 레거시 `.pak`에 그대로 남는다.** 이 게임도 그랬고, 그것이 패치의 출발점이다.

### 지원 언어 (공식)

매니페스트의 `Mole/Content/Localization/Game/` 하위:

```
en, fr, ja, zh-Hans, de, es, pl, pt, ru, uk   ← 한국어(ko) 없음
```

→ 비어 있는 **일본어(ja) 슬롯을 한국어로 덮어쓰는 전략**을 택했다(근거는 [01-approach.md](01-approach.md)).

---

## 2. 암호화 없음 확인

`strings`로 `.ucas`를 훑어 평문 게임 텍스트(`DORM 04, DECK FLOOR` 등)와 UE 머티리얼 함수 설명이 그대로 노출되는 것을 확인했다. **AES 인덱스 암호화가 걸려 있지 않다** → repak/retoc에 AES 키가 필요 없다.

---

## 3. 도구: repak / retoc

둘 다 [trumank](https://github.com/trumank)의 Rust 도구이며 리눅스 x86_64 정적 바이너리를 제공한다.

| 도구 | 용도 | 비고 |
|---|---|---|
| `repak` (v0.2.3) | **레거시 `.pak`** 추출/패킹 | 본 패치 빌드에 사용 |
| `retoc` (v0.1.5) | **IoStore**(`.ucas`/`.utoc`) 언팩/변환 | 누락 검증([06](06-verification.md))에만 사용 |

설치는 [`scripts/setup_tools.sh`](../scripts/setup_tools.sh) 참고.

```bash
# 레거시 pak 정보 — version/mount/seed 확인
repak info Mole-Windows.pak
#   mount point: ../../../
#   version: V11  (major: Fnv64BugFix)
#   path hash seed: Some(498B9334)
#   compression: Oodle

# 추출 (4461개 파일)
repak unpack Mole-Windows.pak -o ./extract
```

추출 결과 텍스트/폰트가 레거시 pak에 있음을 확인:

```
Mole/Content/Localization/Game/ja/Game.locres        ← 본문 텍스트 (169,994 B)
Engine/Content/Localization/Engine/ja/Engine.locres  ← 엔진 키 이름 등
Mole/Content/Drift/Art/Fonts/*.ufont                 ← 폰트 (→ 03-fonts.md)
```

패치는 동일 경로를 담은 **`Mole-Windows_P.pak`**(우선순위 `_P`)를 같은 Paks 폴더에 추가해 오버라이드한다. 패킹은 원본과 동일한 `--version V11 --mount-point ../../../ --path-hash-seed 0x498B9334`(10진 1233883956)로 한다.

---

## 4. UE LocRes v3 포맷 해부

`Game.locres`(ja)의 선두 바이트:

```
00000000: 0e14 7475 674a 03fc 4a15 909d c337 7f1b   ← 16바이트 매직(LocResMagic GUID)
00000010: 03                                          ← 버전 = 3
          a1 5f 01 00 00 00 00 00                     ← int64 문자열테이블 오프셋 = 0x15fa1
```

- **매직**: `0e 14 74 75 67 4a 03 fc 4a 15 90 9d c3 37 7f 1b` (= `FTextLocalizationResource` 의 LocRes 매직 GUID)
- **버전 바이트 `03`** = `ELocResVersion::Optimized_CityHash64_UTF16`
- 이어서 **int64 문자열 테이블 오프셋**(파일 뒤쪽의 문자열 배열 위치)

### 4.1 전체 레이아웃

```
┌ 0x00  매직 (16 B)
├ 0x10  버전 (1 B = 0x03)
├ 0x11  int64 문자열테이블 오프셋  ──────────────┐
├ 0x19  엔트리 영역 (네임스페이스/키 테이블)      │ 비표준 중첩
│         …                                     │
└ str_off  문자열 테이블  ◀──────────────────────┘
            uint32 count
            [ FString text ; int32 refcount ] × count
```

### 4.2 문자열 테이블 (실제 표시 텍스트)

게임에 보이는 **모든 번역 텍스트는 여기**에 있다. `Game.locres`(ja) 기준:

```
str_off (0x15fa1):
  uint32 count = 1300
  for each:
    FString text          # 예: 첫 항목 len=-3 → UTF-16 "戻る"
    int32  refcount        # 예: 15  (이 문자열을 참조하는 키 수)
```

문자열은 **중복 제거(dedup)** 되어 있어, 여러 키가 한 문자열 인덱스를 공유한다(그래서 refcount가 1보다 큰 것이 있다). ja는 고유 문자열 1300개.

### 4.3 FString 인코딩

```
int32 length
  length == 0  → 빈 문자열
  length  > 0  → ANSI(1바이트/문자), length 바이트(널 종단 포함)
  length  < 0  → UTF-16LE, |length| 코드유닛(널 종단 포함) = 2·|length| 바이트
```

영어/숫자 키는 ANSI(양수), 일본어/한국어 텍스트는 UTF-16(음수)로 저장된다. 한글을 쓰려면 해당 문자열을 UTF-16로 인코딩하면 된다.

### 4.4 엔트리 영역과 "불투명 보존" 전략

오프셋 직후(0x19)부터 문자열 테이블 전까지는 **네임스페이스 → 키 → (소스해시, 문자열인덱스)** 매핑 테이블이다. 그런데 이 게임의 엔트리 영역은 표준 중첩 레이아웃(`nsCount → {nsHash, nsStr, keyCount, keys…}`)으로 파싱하면 **첫 키에서 어긋나며 깨졌다**(전처리부 21바이트의 해석이 표준과 불일치).

이 영역을 완벽히 파싱할 필요는 없었다. **번역 표시 텍스트는 전부 문자열 테이블에만** 있고, 엔트리는 인덱스로 참조할 뿐이며, 저장된 해시는 **소스(영어) 문자열의 해시**라 번역을 바꿔도 무관하기 때문이다. 그래서:

> **헤더(25바이트) + 엔트리 영역을 통째로 불투명(opaque) 바이트로 보존**하고, **문자열 테이블만 다시 써서** 오프셋을 갱신한다.

이 방식으로 원본을 그대로 재생성했을 때 **바이트 단위 완전 일치(round-trip lossless)** 를 달성했다:

```
$ python tools/locres.py check .../ja/Game.locres
ver=3 strings=1300 orig=169994 rebuilt=169994 identical=True
```

`Engine.locres`(ja, 34,552 문자열)에서도 동일하게 무손실 확인.

### 4.5 키 블록 구조와 en↔ja 정렬

품질을 위해 일본어뿐 아니라 **영어 원문**도 대조하려면 두 언어 파일을 같은 항목끼리 묶어야 한다. 각 언어 `.locres`는 독립적인 문자열 테이블/인덱스를 갖지만(ja 1300개, en 1795개로 개수도 다름), **키(key)는 언어 간 동일**하다.

이 게임의 키는 **32자 16진수 GUID**다. 키 블록은 다음 49바이트 고정 구조:

```
keyHash   uint32   (4)
key       FString  (4 + 33)   ← int32 길이(=33) + GUID 32자 ASCII + 널
srcHash   uint32   (4)        ← 소스(영어) 문자열 해시
index     int32    (4)        ← 문자열 테이블 인덱스
= 49 바이트
```

실제 첫 키(ja):

```
0x2e  keyHash
0x32  len = 33
0x36  "49DF297A425CB670A783A7BEC1D493A8"
0x57  srcHash
0x5b  index = 0     → 문자열[0] = "戻る"
```

GUID는 16진수 32자라 검증이 쉬워, 엔트리 영역을 **brute-scan**(각 위치에서 위 49바이트 패턴 + index 범위 검증)해 `(GUID → index)`를 추출한다. 결과:

| 파일 | 고유 문자열 | 추출 키 |
|---|---|---|
| ja `Game.locres` | 1300 | 1835 |
| en `Game.locres` | 1795 | 2454 |
| **공통 GUID** | — | **1835** |

GUID로 조인하면 `GUID → (en_text, ja_text)`가 만들어진다. 예: `49DF297A…` → ja `"戻る"` / en `"Backward"`(→ 메뉴 "뒤로"가 아니라 이동 "후진"이 맞다는 판단 근거가 됨). 이 정렬로 번역 시 일본어+영어를 동시에 보며 작업했다(→ [04-translation.md](04-translation.md)).

> 참고: 배포용 번역 데이터는 인덱스가 아니라 **일본어 원문 문자열 → 한국어**로 키잉한다(`data/translations.json`). 게임 업데이트로 인덱스가 밀려도 견고하며, ja 1300개가 전부 고유해 충돌이 없음을 확인했다.

---

## 5. `tools/locres.py` 구현 요약

위 분석을 그대로 코드화한 v3 전용 리더/라이터. 핵심은 **엔트리 영역 불투명 보존 + 문자열 테이블만 재작성**이다.

```python
# load(): 헤더(매직+버전) / 엔트리 블롭 / 문자열 테이블로 분해
header  = d[:25]               # 매직(16) + 버전(1) + 오프셋(8)
entries = d[25:str_off]        # 네임스페이스/키 테이블 — 손대지 않음
strings = [(text, enc, refcount), ...]   # 문자열 테이블만 파싱/편집

# dump(): 헤더 + 오프셋 자리표시자 + 엔트리 블롭 + (재인코딩된)문자열 테이블
#         마지막에 실제 문자열 테이블 오프셋을 헤더에 채워넣음
```

제공 명령:

```bash
python tools/locres.py check  <file>          # 라운드트립 무손실 검증
python tools/locres.py export <file> out.json # [index, text] 목록 추출
```

빌드 시 `data/translations.json`(일본어→한국어)과 `data/engine_keys.json`을 이 모듈로 적용한다(→ [`tools/build.py`](../tools/build.py)).
