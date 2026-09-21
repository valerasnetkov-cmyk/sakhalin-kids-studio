# Sakhalin Kids — Narrative Character Profiles

This directory contains the canonical narrative/behavior profiles for the persistent cast.

These documents define character voice, temperament, strengths, weaknesses, thinking patterns, team relationships, recurring phrases, and story function.

## Profiles

- [Макар](makar.md) — исследователь и главный любитель вопросов.
- [Лёва](leva.md) — рассудительный исследователь и голос здравого смысла.
- [Тихон](tikhon.md) — лесной исследователь и хранитель безопасности.
- [Анна](anna.md) — исследовательница моря и подводного мира.
- [Антошка](antoshka.md) — путешественник и рассказчик.

## Source-of-truth boundary

- `docs/sakhalin/TEAM_CANON.md` and `config/sakhalin/team_canon.json` own stable identity fields such as character ID, species/type, and implemented rig mapping.
- The files in this directory own narrative characterization: personality, behavior, thinking pattern, relationships, signature phrases, and story role.
- Runtime schemas and rig files own technical animation contracts.

If a contradiction is found between identity/type data and a narrative profile, do not silently reinterpret the character. Treat it as a canon conflict that requires an explicit project decision.

Sima is not part of the current persistent cast.
