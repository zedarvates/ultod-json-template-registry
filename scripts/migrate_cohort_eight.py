from __future__ import annotations
import argparse,hashlib,json,sys
from collections import Counter
from pathlib import Path,PurePosixPath
if __package__ in (None,""):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.pilot_contracts import MigrationResult,normalize_slug
from scripts.template_contract import decode_json_bytes,compute_spec_checksum
def render(v):return (json.dumps(v,indent=2,ensure_ascii=False)+"\n").encode()
def slug(source,doc):return normalize_slug(doc["id"]) if isinstance(doc,dict) and isinstance(doc.get("id"),str) else normalize_slug(PurePosixPath(source).parts[-3])
def convert(source,doc,collisions):
    s=slug(source,doc)
    if not isinstance(doc,dict):return MigrationResult(source,"energy",s,"invalid-source",("root-not-object",),None,None)
    if any(k in doc for k in ("energy_events","energy_nodes","advanced_synergies")) or "position" in doc or "template" in s:
        return MigrationResult(source,"energy",s,"legacy-only-authoritative",("runtime-energy-instance-catalog-or-formula",),None,None)
    if s in collisions:return MigrationResult(source,"energy",s,"manual-review",("normalized-slug-collision",),None,None)
    name=doc.get("name")
    if not isinstance(name,str) or not name.strip():return MigrationResult(source,"energy",s,"manual-review",("missing-display-name",),None,None)
    spec={"display_name":name.strip()}; target=f"templates/energy/{s}/v1.0.0/template.json"; result=MigrationResult(source,"energy",s,"migrated",(),target,None)
    strict={"$schema":"../../../schemas/energy/v1.0.0/schema.json","contract_version":"1.0.0","id":f"energy:{s}","slug":s,"family":"energy","version":"1.0.0","authority":"declarative","intended_consumers":["llm-pipeline"],"compatibility":[],"dependencies":[],"spec_checksum":compute_spec_checksum(spec),"spec":spec};return result.__class__(**{**result.__dict__,"document":strict})
def schema():return {"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"https://ultimateodycer.com/schemas/energy/1.0.0","title":"Ultimate Odycer energy Template v1","allOf":[{"$ref":"https://ultimateodycer.com/schemas/template-contract/1.0.0"},{"properties":{"spec":{"type":"object","required":["display_name"],"properties":{"display_name":{"type":"string","minLength":1,"maxLength":100}},"additionalProperties":False}}}]}
def build(root:Path):
    cat=decode_json_bytes((root/"templates/catalog.json").read_bytes());entries=[e for e in cat["entries"] if not(e.get("validation_profile")=="strict-v1" and e.get("family")=="energy") and not(e.get("validation_profile")=="strict-schema-v1" and e.get("name")=="energy")];by={e["file"]:e for e in entries};paths=sorted(p.relative_to(root).as_posix() for p in (root/"templates/energy").rglob("template.json") if p.parent.name!="v1.0.0");decoded={};cand=[]
    for source in paths:
        try:d=decode_json_bytes((root/source).read_bytes());decoded[source]=d;cand.append(slug(source,d))
        except Exception:pass
    collisions={s for s,c in Counter(cand).items() if c>1};results=[];files={}
    for source in paths:
        try:r=convert(source,decoded[source],collisions)
        except Exception as error:r=MigrationResult(source,"energy","","invalid-source",(type(error).__name__,),None,None)
        results.append(r);legacy=by[source]
        for k in ("id","slug","family","superseded_by"):legacy.pop(k,None)
        if r.disposition!="migrated":continue
        content=render(r.document);files[r.target_file]=content;legacy.update({"id":f"energy:{r.slug}","slug":r.slug,"family":"energy","superseded_by":f"energy:{r.slug}@1.0.0"});entries.append({"id":f"energy:{r.slug}","slug":r.slug,"family":"energy","name":r.slug,"kind":"energy-template","version":"1.0.0","contract_version":"1.0.0","validation_profile":"strict-v1","status":"experimental","schema_file":"templates/schemas/energy/v1.0.0/schema.json","file":r.target_file,"sha256":hashlib.sha256(content).hexdigest(),"spec_checksum":r.document["spec_checksum"],"intended_consumers":["llm-pipeline"],"compatibility":[],"supersedes":[f"energy:{r.slug}@0.1.0"]})
    sc=render(schema());sp="templates/schemas/energy/v1.0.0/schema.json";files[sp]=sc;entries.append({"name":"energy","kind":"json-schema","version":"1.0.0","status":"experimental","file":sp,"sha256":hashlib.sha256(sc).hexdigest(),"compatibility":[],"validation_profile":"strict-schema-v1","contract_version":"1.0.0"});files["templates/energy/README.md"]=b"# Energy templates\n\nMinimal declarative energy identities. Runtime capacities, regeneration, conversion, nodes, events, colors, coordinates, and formulas are excluded. Intended consumer: LLM pipeline only. Zig support requires separate evidence.\n";results.sort(key=lambda r:r.source_file);counts=dict(sorted(Counter(r.disposition for r in results).items()));report={"report_version":"1.0.0","cohort":"8","families":["energy"],"summary":{"total":len(results),"dispositions":counts},"results":[{"source_file":r.source_file,"family":r.family,"slug":r.slug,"disposition":r.disposition,"reason_codes":list(r.reason_codes),"target_file":r.target_file} for r in results]};cat["entries"]=entries;files["MIGRATION-V1-COHORT-8.json"]=render(report);files["templates/catalog.json"]=render(cat);return {"results":results,"counts":counts,"files":files}
def write(root,plan):
    for rel,c in plan["files"].items():p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(c)
def check(root,plan):return [r for r,c in plan["files"].items() if not(root/r).is_file() or(root/r).read_bytes()!=c]
def main():
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path("."));m=p.add_mutually_exclusive_group(required=True);m.add_argument("--write",action="store_true");m.add_argument("--check",action="store_true");a=p.parse_args();plan=build(a.root);write(a.root,plan) if a.write else (_ for _ in ()).throw(SystemExit(1)) if check(a.root,plan) else None;print(json.dumps({"counts":plan["counts"],"total":len(plan["results"])},sort_keys=True))
if __name__=="__main__":main()
