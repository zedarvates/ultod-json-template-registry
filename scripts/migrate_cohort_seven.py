from __future__ import annotations
import argparse,hashlib,json,sys
from collections import Counter
from pathlib import Path
if __package__ in (None,""):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.cohort_seven_contracts import FAMILIES,STRICT,KINDS,candidate,convert,schema
from scripts.pilot_contracts import MigrationResult
from scripts.template_contract import decode_json_bytes
def render(v):return (json.dumps(v,indent=2,ensure_ascii=False)+"\n").encode()
def readme(f):return (f"# {f.title()} templates\n\n## Purpose\n\nMinimal declarative {f} identity and classification.\n\n## Required fields\n\n`display_name`; optional profession, station, or category tags.\n\n## Authoritative exclusions\n\nExcluded: ingredients, quantities, skill thresholds, timings, probabilities, costs, rewards, loot tables, experience, and runtime rules.\n\n## Intended consumers\n\nLLM pipeline only. Zig support requires separate typed-adapter evidence.\n\n## Compatibility evidence\n\nNone verified.\n\n## Versioning\n\nTemplates and family schemas follow independent SemVer.\n").encode()
def build(root:Path):
    cat=decode_json_bytes((root/"templates/catalog.json").read_bytes()); ss=set(STRICT); entries=[e for e in cat["entries"] if not(e.get("validation_profile")=="strict-v1" and e.get("family") in ss) and not(e.get("validation_profile")=="strict-schema-v1" and e.get("name") in ss)]; by={e["file"]:e for e in entries}; results=[]; files={}
    for family in FAMILIES:
        paths=sorted(p.relative_to(root).as_posix() for p in (root/"templates"/family).rglob("template.json") if p.parent.name!="v1.0.0"); decoded={}; cand=[]
        for source in paths:
            try:d=decode_json_bytes((root/source).read_bytes());decoded[source]=d;cand.append(candidate(source,d))
            except Exception:pass
        collisions={s for s,c in Counter(cand).items() if c>1}
        for source in paths:
            try:r=convert(family,source,decoded[source],collisions)
            except Exception as error:r=MigrationResult(source,family,"","invalid-source",(type(error).__name__,),None,None)
            results.append(r);legacy=by[source]
            for k in ("id","slug","family","superseded_by"):legacy.pop(k,None)
            if r.disposition!="migrated":continue
            content=render(r.document);files[r.target_file]=content;legacy.update({"id":f"{family}:{r.slug}","slug":r.slug,"family":family,"superseded_by":f"{family}:{r.slug}@1.0.0"});entries.append({"id":f"{family}:{r.slug}","slug":r.slug,"family":family,"name":r.slug,"kind":KINDS[family],"version":"1.0.0","contract_version":"1.0.0","validation_profile":"strict-v1","status":"experimental","schema_file":f"templates/schemas/{family}/v1.0.0/schema.json","file":r.target_file,"sha256":hashlib.sha256(content).hexdigest(),"spec_checksum":r.document["spec_checksum"],"intended_consumers":r.document["intended_consumers"],"compatibility":[],"supersedes":[f"{family}:{r.slug}@0.1.0"]})
        if family not in ss:continue
        sp=f"templates/schemas/{family}/v1.0.0/schema.json";sc=render(schema(family));files[sp]=sc;entries.append({"name":family,"kind":"json-schema","version":"1.0.0","status":"experimental","file":sp,"sha256":hashlib.sha256(sc).hexdigest(),"compatibility":[],"validation_profile":"strict-schema-v1","contract_version":"1.0.0"});files[f"templates/{family}/README.md"]=readme(family)
    results.sort(key=lambda r:r.source_file);counts=dict(sorted(Counter(r.disposition for r in results).items()));report={"report_version":"1.0.0","cohort":"7","families":list(FAMILIES),"summary":{"total":len(results),"dispositions":counts},"results":[{"source_file":r.source_file,"family":r.family,"slug":r.slug,"disposition":r.disposition,"reason_codes":list(r.reason_codes),"target_file":r.target_file} for r in results]};cat["entries"]=entries;files["MIGRATION-V1-COHORT-7.json"]=render(report);files["templates/catalog.json"]=render(cat);return {"results":results,"counts":counts,"files":files}
def write(root,plan):
    for rel,c in sorted(plan["files"].items()):
        p=root/rel;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists() and "v1.0.0/template.json" in rel and p.read_bytes()!=c:raise FileExistsError(rel)
        p.write_bytes(c)
def check(root,plan):return [r for r,c in plan["files"].items() if not(root/r).is_file() or (root/r).read_bytes()!=c]
def main():
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path("."));m=p.add_mutually_exclusive_group(required=True);m.add_argument("--write",action="store_true");m.add_argument("--check",action="store_true");a=p.parse_args();plan=build(a.root)
    if a.write:write(a.root,plan)
    elif check(a.root,plan):raise SystemExit(1)
    print(json.dumps({"counts":plan["counts"],"total":len(plan["results"])},sort_keys=True))
if __name__=="__main__":main()
