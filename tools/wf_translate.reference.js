export const meta = {
  name: 'mole-kr-translate',
  description: 'Translate M.O.L.E ja->ko locres in batches with 3-lens parallel cross-verification and fix gate',
  phases: [
    { title: 'Translate', detail: 'one agent per ~45-string batch (ja primary, en reference)' },
    { title: 'Verify', detail: '3 independent lenses per batch: accuracy / glossary+register / format+fluency' },
    { title: 'Finalize', detail: 'apply findings, re-check preservation rules, write batch_<id>.json' },
  ],
}

const GLO = '/home/shawnkim/mole-kr/glossary.md'
const SRC = id => `/home/shawnkim/mole-kr/tr/src/batch_${id}.json`
const OUT = id => `/home/shawnkim/mole-kr/tr/out/batch_${id}.json`

const TR = {
  type: 'object',
  properties: {
    translations: {
      type: 'array',
      items: {
        type: 'object',
        properties: { index: { type: 'integer' }, ko: { type: 'string' } },
        required: ['index', 'ko'],
      },
    },
  },
  required: ['translations'],
}

const FIND = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          index: { type: 'integer' },
          severity: { type: 'string' },
          issue: { type: 'string' },
          suggestion: { type: 'string' },
        },
        required: ['index', 'severity', 'issue', 'suggestion'],
      },
    },
  },
  required: ['findings'],
}

const LENSES = [
  { key: 'accuracy', focus: '의미 정확성. 오역/누락/추가/의미왜곡 점검. 일본어(ja)가 우리가 채우는 슬롯이므로 ja 의미 우선, 영어(en)는 보조. ja와 en이 충돌하면 ja 의미를 기준으로 판정.' },
  { key: 'glossary', focus: '글로서리 고유명사·용어 일관성, 카테고리 register_hint에 맞는 문체/레지스터, 호칭·말투 일관성.' },
  { key: 'format', focus: '보존 무결성: {/n} 개수·위치, 실제 줄바꿈(\\n) 위치, [ENTER]/[코드]/버전/주파수/좌표/단위/에러코드 보존. 그리고 한국어 맞춤법/오타/어색함.' },
]

let TASK = [{"batch_id":1,"cat":"UI","n":45},{"batch_id":2,"cat":"UI","n":45},{"batch_id":3,"cat":"UI","n":45},{"batch_id":4,"cat":"UI","n":45},{"batch_id":5,"cat":"UI","n":45},{"batch_id":6,"cat":"UI","n":45},{"batch_id":7,"cat":"UI","n":45},{"batch_id":8,"cat":"UI","n":45},{"batch_id":9,"cat":"UI","n":45},{"batch_id":10,"cat":"UI","n":45},{"batch_id":11,"cat":"UI","n":45},{"batch_id":12,"cat":"UI","n":45},{"batch_id":13,"cat":"UI","n":45},{"batch_id":14,"cat":"UI","n":44},{"batch_id":15,"cat":"NUMERIC","n":11},{"batch_id":16,"cat":"SYSTEM","n":33},{"batch_id":17,"cat":"ITEM","n":45},{"batch_id":18,"cat":"ITEM","n":5},{"batch_id":19,"cat":"DIALOGUE","n":45},{"batch_id":20,"cat":"DIALOGUE","n":45},{"batch_id":21,"cat":"DIALOGUE","n":21},{"batch_id":22,"cat":"DIARY","n":17},{"batch_id":23,"cat":"DOC","n":43},{"batch_id":24,"cat":"MISC","n":45},{"batch_id":25,"cat":"MISC","n":45},{"batch_id":26,"cat":"MISC","n":45},{"batch_id":27,"cat":"MISC","n":45},{"batch_id":28,"cat":"MISC","n":45},{"batch_id":29,"cat":"MISC","n":45},{"batch_id":30,"cat":"MISC","n":45},{"batch_id":31,"cat":"MISC","n":45},{"batch_id":32,"cat":"MISC","n":45},{"batch_id":33,"cat":"MISC","n":1}]
if (Array.isArray(args)) TASK = args
else if (typeof args === 'string') { try { TASK = JSON.parse(args) } catch (e) {} }
log(`번역 시작: ${TASK.length}개 배치`)

const results = await pipeline(
  TASK,

  // --- Stage 1: translate ---
  (b) => agent(
    `당신은 심리호러 게임 M.O.L.E의 한글화 전문 번역가다.\n` +
    `먼저 글로서리를 정독하라: Read ${GLO}\n` +
    `그리고 번역할 배치를 읽어라: Read ${SRC(b.batch_id)}  (필드: cat, register_hint, items=[{i,ja,en}])\n\n` +
    `규칙:\n` +
    `- 각 item을 한국어로 번역한다. ja(일본어)가 실제로 게임에 들어갈 원문이므로 ja 의미를 우선하고, en(영어)은 보조 참고.\n` +
    `- register_hint의 문체를 따르고, 글로서리의 고유명사·용어·슬로건을 반드시 그대로 사용한다.\n` +
    `- 보존 규칙(절대 변형 금지): {/n} 토큰 그대로, 실제 줄바꿈 위치 유지, [ENTER]/[001-032]/버전/주파수/좌표/단위(m,°C,Hz)/16진 에러코드(0x...) 보존.\n` +
    `- 가타카나 변형 표기(スル, イル 등 작위적 표기)도 표준 한국어로 자연스럽게.\n` +
    `- 항목을 하나도 빠뜨리지 말 것. item의 i 값을 index로 그대로 사용.\n\n` +
    `결과를 {index, ko} 배열(translations)로 반환하라.`,
    { schema: TR, label: `tr:b${b.batch_id}:${b.cat}`, phase: 'Translate', effort: 'high' }
  ).then(r => ({ b, translations: r.translations })),

  // --- Stage 2: 3-lens parallel cross-verification ---
  (t) => parallel(LENSES.map(L => () =>
    agent(
      `M.O.L.E 한글화 검수자. 담당 렌즈: [${L.key}]\n중점: ${L.focus}\n\n` +
      `원문(소스): Read ${SRC(t.b.batch_id)}\n글로서리: Read ${GLO}\n\n` +
      `아래는 번역 결과 JSON이다. 네 렌즈 기준으로 문제가 있는 항목만 findings에 담아라. 문제 없으면 빈 배열.\n` +
      `각 finding: index, severity(high/med/low), issue(무엇이 문제인지), suggestion(구체적 수정안).\n` +
      `자신 없거나 사소한 취향 차이는 제외하고, 실제 오류/불일치/보존위반에 집중.\n\n` +
      `번역 결과:\n${JSON.stringify(t.translations)}`,
      { schema: FIND, label: `vf:${L.key}:b${t.b.batch_id}`, phase: 'Verify', effort: 'medium' }
    ).then(r => r.findings || [])
  )).then(all => ({ ...t, findings: all.filter(Boolean).flat() })),

  // --- Stage 3: finalize (apply fixes, re-check, persist to disk) ---
  (t) => agent(
    `M.O.L.E 한글화 최종 교정·기록자.\n` +
    `원문: Read ${SRC(t.b.batch_id)}\n글로서리: Read ${GLO}\n\n` +
    `아래 "현재 번역"에 "검수 지적(findings)"을 반영해 최종본을 확정하라.\n` +
    `- 지적된 index만 수정하고, 지적 없는 항목은 좋은 번역이면 유지.\n` +
    `- 보존 규칙({/n}, 줄바꿈 위치, [ENTER]/코드/숫자/단위/에러코드)을 최종 점검.\n` +
    `- 배치의 모든 항목을 빠짐없이 포함.\n\n` +
    `그런 다음 반드시 Write 툴로 다음 파일을 생성하라:\n` +
    `  경로: ${OUT(t.b.batch_id)}\n` +
    `  내용: 최종본을 JSON 배열로. 예) [{"index":12,"ko":"..."},{"index":13,"ko":"..."}]\n` +
    `  (UTF-8, 유효한 JSON, 배치의 전체 항목 포함)\n\n` +
    `마지막으로 같은 최종본을 StructuredOutput(translations 배열)으로도 반환하라.\n\n` +
    `현재 번역:\n${JSON.stringify(t.translations)}\n\n검수 지적:\n${JSON.stringify(t.findings)}`,
    { schema: TR, label: `final:b${t.b.batch_id}`, phase: 'Finalize', effort: 'medium' }
  ).then(r => ({ batch_id: t.b.batch_id, count: r.translations.length, findings: t.findings.length }))
)

const ok = results.filter(Boolean)
const totalStrings = ok.reduce((s, r) => s + (r.count || 0), 0)
const totalFindings = ok.reduce((s, r) => s + (r.findings || 0), 0)
log(`완료: ${ok.length}/${TASK.length} 배치, 번역 ${totalStrings}개, 검수 지적 ${totalFindings}건 반영`)
return { batches: ok.length, strings: totalStrings, findings: totalFindings }
