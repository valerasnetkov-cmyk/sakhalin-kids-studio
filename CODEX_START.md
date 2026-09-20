# Sakhalin Kids Studio — стартовый бриф для Codex

## Цель

Расширить OpenMontage отдельным производственным контуром для детского YouTube-канала о Сахалине.

Финальная команда персонажей:

- Макар — лисёнок, главный исследователь.
- Лёва — сивуч, спокойный напарник и голос здравого смысла.
- Тихон — медвежонок, лес и безопасность.
- Анна — нерпа, море и подводный мир.
- Антошка — чайка-путешественник и собиратель историй.

Состав закрыт: новые постоянные герои не создаются без отдельного изменения конфигурации проекта.

## Базовый принцип

Не переписывать OpenMontage.

Нужно добавить тонкий продуктовый слой:

- `pipeline_defs/sakhalin-kids.yaml`;
- `skills/pipelines/sakhalin-kids/*`;
- `styles/sakhalin-kids.yaml`;
- `tools/character/sakhalin/*`;
- `library/characters/*`;
- `schemas/sakhalin/*`;
- `tests/sakhalin/*`.

Использовать существующие OpenMontage contracts, registry, checkpoints, cost tracker, Backlot и render runtimes.

## Главная производственная стратегия

Не строить сериал как цепочку независимых text-to-video вызовов.

Основные герои должны быть повторно используемыми детерминированными ассетами:

`character spec -> rig -> pose library -> action timeline -> viseme timeline -> render`.

Генеративное видео используется как дополнительный слой:

- establishing shots;
- природа;
- море;
- исторические реконструкции;
- фантазийные сцены;
- сложные кинематографические вставки.

Диалоги и повторяющееся актёрское взаимодействие героев должны рендериться локальным character runtime.

## Первый milestone

Сделать только Макара и Лёву.

Тестовая сцена 10–15 секунд:

> Макар: «Лёва, а почему море солёное?»
> Лёва: «Хороший вопрос. Давайте разберёмся.»

Нужно доказать:

1. два разных персонажа одновременно;
2. фиксированные character assets;
3. blink;
4. gaze;
5. минимум один gesture на персонажа;
6. два разных голоса;
7. русский viseme timeline;
8. lip-sync;
9. HyperFrames или Remotion render;
10. итоговый MP4;
11. повторный render не меняет внешний вид героев.

## Ограничения

- Не добавлять платный AI-video в Milestone 01.
- Не создавать отдельный renderer на каждого героя.
- Отличия героев должны быть данными и rig profiles.
- Не хранить API keys, voice IDs с секретами или credentials в Git.
- Не исполнять model output напрямую как shell, URL, filesystem path или provider call.
- Все платные provider calls должны проходить budget policy.
- Все authored source files держать до 400 строк.
- Не менять существующие OpenMontage public interfaces без доказанной необходимости.

## Обязательные проверки

Перед завершением каждого milestone:

- lint;
- type/static checks, если они есть в проекте;
- targeted tests;
- relevant contract tests;
- render smoke test;
- ffprobe результата;
- frame sampling;
- проверка отсутствия секретов в diff;
- line-count gate для изменённых authored files.

## Документация

Сначала прочитать:

- `docs/sakhalin/ARCHITECTURE.md`
- `docs/sakhalin/IMPLEMENTATION_PLAN.md`
- `docs/sakhalin/CHARACTER_FORMAT.md`
- `docs/sakhalin/LIPSYNC.md`
- `pipeline_defs/sakhalin-kids.yaml`

Не начинать с реализации полного выпуска. Первый deliverable — Character Runtime proof.
