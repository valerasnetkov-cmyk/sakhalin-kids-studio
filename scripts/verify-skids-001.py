#!/usr/bin/env python3
"""SKIDS-001 verification. Check repo policy, manifest, cast, line gate, secrets."""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys
from pathlib import Path

PINNED_COMMIT = "08e2151fa02de28a5d6a312b3d575692bf147ad7"
CAST_PATH = Path("config/sakhalin/allowed_cast.json")
MANIFEST = Path("pipeline_defs/sakhalin-kids.yaml")
AUTHORED_EXT = {".py", ".yaml", ".yml", ".json", ".md"}
EXCLUDE = {".git", ".venv", "venv", "node_modules", "dist", "build",
           "coverage", "cache", "vendor", "__pycache__", ".pytest_cache"}
LIMIT = 400
CAST = {"makar", "leva", "tikhon", "anna", "antoshka"}
EXTS = {"pipelines/sakhalin-kids/executive-producer",
        "pipelines/sakhalin-kids/research-director",
        "pipelines/sakhalin-kids/proposal-director",
        "pipelines/sakhalin-kids/script-director",
        "pipelines/sakhalin-kids/storyboard-director",
        "pipelines/sakhalin-kids/voice-director",
        "pipelines/sakhalin-kids/lipsync-director",
        "pipelines/sakhalin-kids/asset-director",
        "pipelines/sakhalin-kids/animation-director",
        "pipelines/sakhalin-kids/compose-director",
        "pipelines/sakhalin-kids/qa-director",
        "pipelines/sakhalin-kids/publish-director",
        "sakhalin_lipsync", "sakhalin_character_loader",
        "sakhalin_media_library", "sakhalin_action_timeline",
        "sakhalin_character_renderer", "sakhalin_character_reviewer",
        "dialogue_manifest", "viseme_timelines", "child_content_qa",
        "factual_qa", "production_qa", "sakhalin-kids"}
SECRET_RE = re.compile(
    r"(?:api[_-]?key|secret[_-]?key|password|access[_-]?token"
    r"|auth[_-]?token|private[_-]?key|client[_-]?secret)"
    r"\s*[=:]\s*(['\"])\\S+\\1", re.IGNORECASE)
META = ["meta/reviewer", "meta/checkpoint-protocol",
        "meta/animation-runtime-selector", "meta/voice-performance-director"]
ARTIFACTS = ["research_brief", "proposal_packet", "decision_log", "script",
             "scene_plan", "asset_manifest", "edit_decisions", "render_report",
             "final_review", "publish_log", "character_design", "rig_plan",
             "pose_library", "action_timeline", "character_qa_report"]


class R:
    def __init__(self, n):
        self.name, self.ok, self.m = n, True, []
    def f(self, x): self.ok = False; self.m.append(f"FAIL: {x}")
    def w(self, x): self.m.append(f"WARN: {x}")
    def i(self, x): self.m.append(f"  {x}")


def yload(p):
    try:
        import yaml
        return yaml.safe_load(p.read_text("utf-8"))
    except ImportError:
        return _byaml(p)

def _byaml(p):
    r, cl = {}, None
    for ln in p.read_text("utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("- ") and cl is not None:
            cl.append(s[2:].strip())
            continue
        m = re.match(r"^([A-Za-z_][\w_-]*)\s*:\s*(.*)", s)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if v in ("", "|"):
                cl = []; r[k] = cl
            elif v.startswith("[") and v.endswith("]"):
                r[k] = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
                cl = None
            else:
                if v == "true": r[k] = True
                elif v == "false": r[k] = False
                else: r[k] = v.strip("\"'")
                cl = None
    return r

def afiles(root):
    return sorted(p for p in root.rglob("*") if p.is_file()
                  and p.suffix in AUTHORED_EXT
                  and not any(x in EXCLUDE or x.startswith(".")
                              for x in p.relative_to(root).parts))

def git(a, cwd=None):
    try:
        return subprocess.run(["git"]+a, capture_output=True, text=True,
                              check=True, cwd=cwd).stdout.strip()
    except Exception:
        return None


def chk_repo():
    r = R("Repository Policy")
    h, o = git(["rev-parse", "HEAD"]), git(["rev-parse", "origin/main"])
    if h and o:
        if h == o: r.i(f"HEAD == origin/main ({h[:12]})")
        else: r.f(f"HEAD ({h[:12]}) != origin/main ({o[:12]})")
    else: r.w("Could not determine HEAD/origin/main")
    s = git(["status", "--porcelain"])
    if s is not None:
        if not s: r.i("Working tree clean")
        else: r.f(f"Working tree dirty")
    if Path("sakhalin-kids-studio.bundle").exists():
        r.w("Bundle file exists")
    else: r.i("No bundle file")
    return r

def chk_cast():
    r = R("Core Cast Policy")
    if not CAST_PATH.exists(): r.f(f"Not found: {CAST_PATH}"); return r
    try: d = json.loads(CAST_PATH.read_text("utf-8"))
    except Exception as e: r.f(f"Parse error: {e}"); return r
    c = set(d.get("core_cast", []))
    if c == CAST: r.i(f"Core cast: {sorted(c)}")
    else:
        if CAST-c: r.f(f"Missing: {sorted(CAST-c)}")
        if c-CAST: r.f(f"Unexpected: {sorted(c-CAST)}")
    if d.get("policy", {}).get("core_cast_closed"): r.i("Core cast closed")
    else: r.w("core_cast_closed not true")
    return r

def chk_manifest():
    r = R("Manifest Schema")
    if not MANIFEST.exists(): r.f(f"Not found: {MANIFEST}"); return r
    m = yload(MANIFEST)
    if not m: r.f("Could not load YAML"); return r
    for f, e, l in [("name", "sakhalin-kids", "Name"),
                     ("version", "0.1", "Version"),
                     ("stability", "beta", "Stability")]:
        if m.get(f) == e: r.i(f"{l}: {e}")
        else: r.f(f"{l}: {m.get(f)} (expected {e})")
    ext = m.get("extensions", {})
    if ext.get("custom_tools"): r.i("extensions.custom_tools: true")
    else: r.f("extensions.custom_tools not true")
    stg = m.get("stages", [])
    r.i(f"Stages: {len(stg) if isinstance(stg, list) else 0}")
    return r

def chk_upstream():
    r = R("Upstream References")
    if not MANIFEST.exists(): r.f("No manifest"); return r
    m = yload(MANIFEST)
    skills = m.get("required_skills", [])
    for s in META:
        if s in skills: r.i(f"Skill: {s}")
        else: r.f(f"Missing skill: {s}")
    pa = set()
    for st in m.get("stages", []):
        pa.update(st.get("produces", []))
    for a in ARTIFACTS:
        if a in pa: r.i(f"Artifact: {a}")
    return r

def chk_extensions():
    r = R("Sakhalin Expected Extensions")
    if not MANIFEST.exists(): r.f("No manifest"); return r
    m = yload(MANIFEST)
    items = set(m.get("required_skills", []))
    for st in m.get("stages", []):
        items.update(st.get("produces", []))
        items.update(st.get("tools_available", []))
    pb = m.get("compatible_playbooks", {})
    items.update(pb.get("recommended", []))
    items.update(pb.get("also_works", []))
    found = EXTS & items
    r.i(f"Referenced: {len(found)}/{len(EXTS)}")
    for e in sorted(found):
        r.i(f"  SAKHALIN_EXTENSION_REQUIRED: {e}")
    if "sakhalin-kids" in pb:
        r.i("Custom playbook 'sakhalin-kids' (SAKHALIN_EXTENSION_REQUIRED)")
    return r

def chk_upstream_files(root, label, subdir, files):
    r = R(label)
    if not root: r.w("NOT_VERIFIED: no OpenMontage checkout"); return r
    d = root / subdir
    if not d.exists(): r.f(f"Not found: {d}"); return r
    for f in files:
        if (d / f).exists(): r.i(f"Exists: {f}")
        else: r.f(f"Missing: {f}")
    return r

def chk_upstream_schema(root):
    r = R("Manifest Schema (upstream)")
    if not root: r.w("NOT_VERIFIED: no OpenMontage checkout"); return r
    if not (root / "AGENT_GUIDE.md").exists():
        r.f(f"Not an OpenMontage checkout: {root}"); return r
    c = git(["rev-parse", "HEAD"], str(root))
    if c:
        if c == PINNED_COMMIT: r.i(f"Commit matches pinned: {c[:12]}")
        else: r.w(f"Commit {c[:12]} != pinned {PINNED_COMMIT[:12]}")
    sp = root / "schemas" / "pipelines" / "pipeline_manifest.schema.json"
    if not sp.exists(): r.f("Pipeline schema not found"); return r
    try:
        import yaml, jsonschema
        schema = json.loads(sp.read_text("utf-8"))
        jsonschema.validate(instance=yload(MANIFEST), schema=schema)
        r.i("Manifest validates against upstream schema")
    except ImportError:
        r.w("NOT_VERIFIED: jsonschema/yaml not installed")
    except Exception as e:
        r.f(f"Validation failed: {e}")
    return r

def chk_line_gate():
    r = R("Line Gate")
    over = []
    for f in afiles(Path(".")):
        try:
            n = len(f.read_text("utf-8", "ignore").splitlines())
            if n > LIMIT: over.append((str(f), n))
        except Exception: pass
    if over:
        for p, n in over: r.f(f"OVER LIMIT: {p} ({n} lines)")
    else: r.i(f"All authored files <= {LIMIT} lines")
    return r

def chk_secrets():
    r = R("Secret Scan")
    found = []
    for f in afiles(Path(".")):
        try: txt = f.read_text("utf-8", "ignore")
        except: continue
        for i, ln in enumerate(txt.splitlines(), 1):
            if SECRET_RE.search(ln):
                found.append((str(f), i))
    if found:
        for p, n in found: r.f(f"POSSIBLE_SECRET: {p}:{n}")
    else: r.i("No obvious secrets")
    return r


def main():
    ap = argparse.ArgumentParser(description="SKIDS-001 verification")
    ap.add_argument("--openmontage-root", type=str,
                    default=os.environ.get("OPENMONTAGE_ROOT"))
    args = ap.parse_args()
    om = Path(args.openmontage_root) if args.openmontage_root else None

    print("=" * 70)
    print("SKIDS-001 Verification")
    print("=" * 70)
    print()

    checks = [chk_repo(), chk_cast(), chk_manifest(), chk_upstream(),
              chk_extensions()]
    if om:
        ag = om / "AGENT_GUIDE.md"
        is_om = ag.exists() and (om / "pipeline_defs").exists()
        if is_om:
            checks.append(chk_upstream_schema(om))
            checks.extend([
                chk_upstream_files(om, "Upstream Skills", "skills/meta",
                                   ["reviewer.md", "checkpoint-protocol.md",
                                    "animation-runtime-selector.md",
                                    "voice-performance-director.md"]),
                chk_upstream_files(om, "Upstream Artifact Schemas",
                                   "schemas/artifacts",
                                   [f"{a}.schema.json" for a in ARTIFACTS]),
                chk_upstream_files(om, "Upstream Character Tools",
                                   "tools/character",
                                   ["character_animation.py", "__init__.py"]),
            ])
        else:
            for lbl in ["Manifest Schema (upstream)", "Upstream Skills",
                        "Upstream Artifact Schemas", "Upstream Character Tools"]:
                checks.append(R(lbl))  # empty = NOT_VERIFIED via warn
                checks[-1].w(f"NOT_VERIFIED: {om} is not a valid OpenMontage checkout")
    else:
        for lbl in ["Manifest Schema (upstream)", "Upstream Skills",
                    "Upstream Artifact Schemas", "Upstream Character Tools"]:
            rc = R(lbl)
            rc.w("NOT_VERIFIED: no --openmontage-root provided")
            checks.append(rc)
    checks.extend([chk_line_gate(), chk_secrets()])

    ok = True; gaps = False; nv = False
    for c in checks:
        s = "PASS" if c.ok else "FAIL"
        print(f"[{s}] {c.name}")
        for msg in c.m:
            print(f"  {msg}")
            if msg.startswith("FAIL:"): ok = False
            if "NOT_VERIFIED" in msg: nv = True
            if "SAKHALIN_EXTENSION_REQUIRED" in msg: gaps = True
            if msg.startswith("WARN:"): gaps = True
        print()

    print("=" * 70)
    if ok and not gaps and not nv:
        print("RESULT: PASS"); return 0
    elif ok:
        print("RESULT: PASS WITH EXPECTED EXTENSION GAPS"); return 0
    else:
        print("RESULT: FAIL"); return 1


if __name__ == "__main__":
    sys.exit(main())
