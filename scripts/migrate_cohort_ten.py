from __future__ import annotations
import argparse,hashlib,json,sys
from collections import Counter
from pathlib import Path,PurePosixPath
if __package__ in (None,""):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.pilot_contracts import MigrationResult,normalize_slug
from scripts.template_contract import decode_json_bytes,compute_spec_checksum

FAMILIES=("blueprints","ai","houses","champions","cosmetic","cosmetic-shop","haptics","marriage","mentorship","paragons","party","pvp","shop","social-events","vendor-shops")
STRICT=("cosmetic","marriage","mentorship","party","social-events")
KINDS={f:f"{f.rstrip('s')}-template" for f in STRICT}
AUTHORITATIVE=set(FAMILIES)-set(STRICT)
def render(v):return (json.dumps(v,indent=2,ensure_ascii=False)+"\n").encode()
def slug(source,doc):return normalize_slug(doc["id"]) if isinstance(doc,dict) and isinstance(doc.get("id"),str) else normalize_slug(PurePosixPath(source).parts[-3])
def text(v,tag=False):
 if not isinstance(v,str) or not(v:=v.strip()) or len(v)>100:return None
 return normalize_slug(v) if tag else v
def convert(family,source,doc,collisions):
 s=slug(source,doc)
 if family in AUTHORITATIVE:return MigrationResult(source,family,s,"legacy-only-authoritative",("runtime-layout-behavior-assets-commerce-or-system-rules",),None,None)
 if not isinstance(doc,dict):return MigrationResult(source,family,s,"invalid-source",("root-not-object",),None,None)
 if s in collisions:return MigrationResult(source,family,s,"manual-review",("normalized-slug-collision",),None,None)
 name=text(doc.get("name"))
 if name is None:return MigrationResult(source,family,s,"manual-review",("missing-display-name",),None,None)
 spec={"display_name":name}; mapping={"cosmetic":(("category","category_tag"),("rarity_tier","rarity_tag")),"marriage":(("marriage_type","marriage_kind"),),"mentorship":(("mentorship_type","mentorship_kind"),),"party":(),"social-events":(("event_type","event_kind"),)}[family]
 for key,target in mapping:
  value=text(doc.get(key),True)
  if value is not None:spec[target]=value
 target=f"templates/{family}/{s}/v1.0.0/template.json";r=MigrationResult(source,family,s,"migrated",(),target,None);strict={"$schema":f"../../../schemas/{family}/v1.0.0/schema.json","contract_version":"1.0.0","id":f"{family}:{s}","slug":s,"family":family,"version":"1.0.0","authority":"declarative","intended_consumers":["llm-pipeline"],"compatibility":[],"dependencies":[],"spec_checksum":compute_spec_checksum(spec),"spec":spec};return MigrationResult(r.source_file,r.family,r.slug,r.disposition,r.reason_codes,r.target_file,strict)
def schema(f):
 tag={"type":"string","pattern":"^[a-z0-9]+(?:-[a-z0-9]+)*$","maxLength":64};props={"display_name":{"type":"string","minLength":1,"maxLength":100}};fields={"cosmetic":("category_tag","rarity_tag"),"marriage":("marriage_kind",),"mentorship":("mentorship_kind",),"party":(),"social-events":("event_kind",)}[f];props.update({x:tag for x in fields});return {"$schema":"https://json-schema.org/draft/2020-12/schema","$id":f"https://ultimateodycer.com/schemas/{f}/1.0.0","title":f"Ultimate Odycer {f} Template v1","allOf":[{"$ref":"https://ultimateodycer.com/schemas/template-contract/1.0.0"},{"properties":{"spec":{"type":"object","required":["display_name"],"properties":props,"additionalProperties":False}}}]}
def build(root:Path):
 cat=decode_json_bytes((root/"templates/catalog.json").read_bytes());ss=set(STRICT);entries=[e for e in cat["entries"] if not(e.get("validation_profile")=="strict-v1" and e.get("family") in ss) and not(e.get("validation_profile")=="strict-schema-v1" and e.get("name") in ss)];by={e["file"]:e for e in entries};results=[];files={}
 for family in FAMILIES:
  paths=sorted(p.relative_to(root).as_posix() for p in (root/"templates"/family).rglob("template.json") if p.parent.name!="v1.0.0");decoded={};cand=[]
  for source in paths:
   try:d=decode_json_bytes((root/source).read_bytes());decoded[source]=d;cand.append(slug(source,d))
   except Exception:pass
  collisions={s for s,c in Counter(cand).items() if c>1}
  for source in paths:
   try:r=convert(family,source,decoded[source],collisions)
   except Exception as error:r=MigrationResult(source,family,"","invalid-source",(type(error).__name__,),None,None)
   results.append(r);legacy=by[source]
   for k in ("id","slug","family","superseded_by"):legacy.pop(k,None)
   if r.disposition!="migrated":continue
   content=render(r.document);files[r.target_file]=content;legacy.update({"id":f"{family}:{r.slug}","slug":r.slug,"family":family,"superseded_by":f"{family}:{r.slug}@1.0.0"});entries.append({"id":f"{family}:{r.slug}","slug":r.slug,"family":family,"name":r.slug,"kind":KINDS[family],"version":"1.0.0","contract_version":"1.0.0","validation_profile":"strict-v1","status":"experimental","schema_file":f"templates/schemas/{family}/v1.0.0/schema.json","file":r.target_file,"sha256":hashlib.sha256(content).hexdigest(),"spec_checksum":r.document["spec_checksum"],"intended_consumers":["llm-pipeline"],"compatibility":[],"supersedes":[f"{family}:{r.slug}@0.1.0"]})
  if family not in ss:continue
  sp=f"templates/schemas/{family}/v1.0.0/schema.json";sc=render(schema(family));files[sp]=sc;entries.append({"name":family,"kind":"json-schema","version":"1.0.0","status":"experimental","file":sp,"sha256":hashlib.sha256(sc).hexdigest(),"compatibility":[],"validation_profile":"strict-schema-v1","contract_version":"1.0.0"});files[f"templates/{family}/README.md"]=(f"# {family.title()} templates\n\nMinimal declarative identities. Runtime layouts, AI, assets, benefits, rewards, commerce, and system rules are excluded. Intended consumer: LLM pipeline only.\n").encode()
 results.sort(key=lambda r:r.source_file);counts=dict(sorted(Counter(r.disposition for r in results).items()));report={"report_version":"1.0.0","cohort":"10","families":list(FAMILIES),"summary":{"total":len(results),"dispositions":counts},"results":[{"source_file":r.source_file,"family":r.family,"slug":r.slug,"disposition":r.disposition,"reason_codes":list(r.reason_codes),"target_file":r.target_file} for r in results]};cat["entries"]=entries;files["MIGRATION-V1-COHORT-10.json"]=render(report);files["templates/catalog.json"]=render(cat);return {"results":results,"counts":counts,"files":files}
def write(root,p):
 for rel,c in p["files"].items():x=root/rel;x.parent.mkdir(parents=True,exist_ok=True);x.write_bytes(c)
def check(root,p):return [r for r,c in p["files"].items() if not(root/r).is_file()or(root/r).read_bytes()!=c]
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path("."));m=p.add_mutually_exclusive_group(required=True);m.add_argument("--write",action="store_true");m.add_argument("--check",action="store_true");a=p.parse_args();plan=build(a.root);write(a.root,plan) if a.write else (_ for _ in ()).throw(SystemExit(1)) if check(a.root,plan) else None;print(json.dumps({"counts":plan["counts"],"total":len(plan["results"])},sort_keys=True))
if __name__=="__main__":main()
