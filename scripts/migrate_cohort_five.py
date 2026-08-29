from __future__ import annotations

import argparse, hashlib, json, sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.cohort_five_contracts import COHORT_FIVE_FAMILIES, KIND_BY_FAMILY, STRICT_FAMILIES, candidate_slug, convert_legacy, family_schema
from scripts.pilot_contracts import MigrationResult
from scripts.template_contract import decode_json_bytes


def _render(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _readme(family):
    return (f"# {family.title()} templates\n\n## Purpose\n\nMinimal declarative {family} identity and classification.\n\n## Required fields\n\n`display_name`. Optional classification tags are defined by the exact schema.\n\n## Authoritative exclusions\n\nExcluded: stats, phases, loot, anatomy, assets, objectives, rewards, schedules, waves, coordinates, palettes, probabilities, requirements, lore, and runtime mechanics.\n\n## Intended consumers\n\nLLM pipeline only. Zig support requires separate typed-adapter evidence.\n\n## Compatibility evidence\n\nNone verified.\n\n## Versioning\n\nTemplates and family schemas follow independent SemVer.\n").encode("utf-8")


def build_migration(root: Path, families=COHORT_FIVE_FAMILIES):
    if tuple(families) != COHORT_FIVE_FAMILIES:
        raise ValueError("cohort five families are fixed for reproducible review")
    catalog = decode_json_bytes((root / "templates/catalog.json").read_bytes())
    strict_set = set(STRICT_FAMILIES)
    entries = [e for e in catalog["entries"] if not (e.get("validation_profile") == "strict-v1" and e.get("family") in strict_set) and not (e.get("validation_profile") == "strict-schema-v1" and e.get("name") in strict_set)]
    by_file = {e["file"]: e for e in entries}; results=[]; files={}
    for family in families:
        paths=sorted(p.relative_to(root).as_posix() for p in (root/"templates"/family).rglob("template.json") if p.parent.name!="v1.0.0")
        decoded={}; candidates=[]
        for source in paths:
            try:
                document=decode_json_bytes((root/source).read_bytes()); decoded[source]=document; candidates.append(candidate_slug(family,source,document))
            except Exception: pass
        collisions={slug for slug,count in Counter(candidates).items() if count>1}
        for source in paths:
            try: result=convert_legacy(family,source,decoded[source],collisions)
            except Exception as error: result=MigrationResult(source,family,"","invalid-source",(type(error).__name__,),None,None)
            results.append(result); legacy=by_file[source]
            for key in ("id","slug","family","superseded_by"): legacy.pop(key,None)
            if result.disposition!="migrated": continue
            content=_render(result.document); files[result.target_file]=content
            legacy.update({"id":f"{family}:{result.slug}","slug":result.slug,"family":family,"superseded_by":f"{family}:{result.slug}@1.0.0"})
            entries.append({"id":f"{family}:{result.slug}","slug":result.slug,"family":family,"name":result.slug,"kind":KIND_BY_FAMILY[family],"version":"1.0.0","contract_version":"1.0.0","validation_profile":"strict-v1","status":"experimental","schema_file":f"templates/schemas/{family}/v1.0.0/schema.json","file":result.target_file,"sha256":hashlib.sha256(content).hexdigest(),"spec_checksum":result.document["spec_checksum"],"intended_consumers":result.document["intended_consumers"],"compatibility":[],"supersedes":[f"{family}:{result.slug}@0.1.0"]})
        if family not in strict_set: continue
        schema_path=f"templates/schemas/{family}/v1.0.0/schema.json"; schema_content=_render(family_schema(family)); files[schema_path]=schema_content
        entries.append({"name":family,"kind":"json-schema","version":"1.0.0","status":"experimental","file":schema_path,"sha256":hashlib.sha256(schema_content).hexdigest(),"compatibility":[],"validation_profile":"strict-schema-v1","contract_version":"1.0.0"}); files[f"templates/{family}/README.md"]=_readme(family)
    results.sort(key=lambda r:r.source_file); counts=dict(sorted(Counter(r.disposition for r in results).items()))
    report={"report_version":"1.0.0","cohort":"5","families":list(families),"summary":{"total":len(results),"dispositions":counts},"results":[{"source_file":r.source_file,"family":r.family,"slug":r.slug,"disposition":r.disposition,"reason_codes":list(r.reason_codes),"target_file":r.target_file} for r in results]}
    catalog["entries"]=entries; files["MIGRATION-V1-COHORT-5.json"]=_render(report); files["templates/catalog.json"]=_render(catalog)
    return {"results":results,"counts":counts,"files":files}


def write_migration(root,plan):
    for relative,content in sorted(plan["files"].items()):
        path=root/relative; path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and "v1.0.0/template.json" in relative and path.read_bytes()!=content: raise FileExistsError(relative)
        path.write_bytes(content)


def check_migration(root,plan): return [r for r,c in sorted(plan["files"].items()) if not (root/r).is_file() or (root/r).read_bytes()!=c]


def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,default=Path(".")); m=p.add_mutually_exclusive_group(required=True); m.add_argument("--write",action="store_true"); m.add_argument("--check",action="store_true"); a=p.parse_args(); plan=build_migration(a.root)
    if a.write: write_migration(a.root,plan)
    else:
        bad=check_migration(a.root,plan)
        if bad: print("\n".join(bad[:50])); raise SystemExit(1)
    print(json.dumps({"counts":plan["counts"],"total":len(plan["results"])},sort_keys=True))


if __name__=="__main__": main()
