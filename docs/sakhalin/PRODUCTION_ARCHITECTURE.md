# Sakhalin Kids Studio — Production Architecture

Production concerns: media, provenance, approvals, budget, security, runtime, determinism, observability.

Дополнение к `ARCHITECTURE.md` (core system/domain architecture).

## 10. Медиа-библиотека

Предлагаемая структура:

```text
library/
  characters/
  locations/
    sakhalin/
      aniva/
      quiet-bay/
      yuzhno-sakhalinsk/
      nevelsk/
      okhotsk-sea/
      forests/
      rivers/
      ports/
      lighthouses/
      winter/
  props/
  effects/
  music/
  ambient/
  voices/
```

Каждый reusable asset должен иметь provenance metadata.

## 11. Provenance

Минимальная модель:

```yaml
id: okhotsk-sea-drone-001
type: video

source:
  kind: original_footage
  owner: internal

location:
  region: sakhalin

rights:
  status: owned

technical:
  duration_seconds: 12.4
  width: 3840
  height: 2160
```

Для generated assets дополнительно:

- provider;
- model;
- prompt reference;
- generation date;
- cost;
- episode ID.

Секреты в provenance запрещены.

## 12. Approval gates

Human approval обязателен минимум после:

1. proposal;
2. script;
3. storyboard;
4. paid/generated asset plan;
5. publish package.

Character redesign всегда требует отдельного approval.

## 13. Budget boundary

AI-провайдеры являются финансовой trust boundary.

До платного вызова:

```text
estimate
 -> validate
 -> budget policy
 -> reserve
 -> provider call
 -> reconcile
```

Никаких бесконечных retry loops.

Default:

- image retries: 3;
- video retries: 2;
- voice retries: 2.

## 14. Security invariants

1. Secrets не хранятся в Git.
2. Model output не авторизует tool calls.
3. Model output не передаётся напрямую в shell/eval.
4. Filesystem paths нормализуются и ограничиваются workspace.
5. Arbitrary URL fetch запрещён в Sakhalin-specific tools.
6. External research считается untrusted content.
7. Provider calls имеют cost limits.
8. Generated HTML/SVG не должен получать произвольный executable JS из model output.
9. Character asset writes ограничены каталогом проекта/библиотеки.
10. Все high-impact substitutions требуют explicit approval.

## 15. Runtime choice

Для character acting целевые runtimes:

### HyperFrames

Предпочтителен для:

- SVG;
- GSAP;
- timeline-driven acting;
- bespoke scene composition.

### Remotion

Предпочтителен для:

- React composition;
- reusable graphics;
- captions;
- educational cards;
- mixed video/graphics.

### Hypit

Approved candidate для optional semantic composition и derivative production после отдельного pilot gate.

Hypit может собирать утверждённые scene outputs, captions/B-roll и ограниченный набор platform derivatives, но не должен владеть episode/job/approval state, перегенерировать core-character identity, обходить scene routing/budget/provenance или получать arbitrary shell/filesystem/network authority.

При использовании exact Hypit release/commit должен фиксироваться в run metadata.

FFmpeg используется как post-processing/assembly layer, но не как полноценный acting runtime.

## 16. Детерминизм

Повторный render с одинаковыми:

- character assets;
- scene plan;
- dialogue audio;
- timelines;
- runtime version

должен сохранять внешний вид персонажей.

Randomness допускается только в явно объявленных effects и должна быть seedable.

## 17. Наблюдаемость

Каждый episode project должен иметь:

- decision log;
- cost log;
- asset manifest;
- provenance;
- QA reports;
- render report.

Backlot используется как production board, но его отсутствие не должно блокировать render pipeline.

## 18. Не-цели первого этапа

Не делать в Milestone 01:

- полноценный 5-минутный выпуск;
- все пять rig profiles;
- автоматическую публикацию в YouTube;
- сложный neural lip-sync;
- fine-tuning video models;
- самостоятельный web SaaS;
- arbitrary multi-agent orchestration;
- Hypit production integration или массовое клонирование/вариативное производство видео.
