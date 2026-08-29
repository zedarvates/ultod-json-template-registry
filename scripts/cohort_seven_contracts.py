from __future__ import annotations
from dataclasses import replace
from pathlib import PurePosixPath
from typing import Any
from scripts.pilot_contracts import MigrationResult, normalize_slug
from scripts.template_contract import compute_spec_checksum

FAMILIES=("recipes","recipe","bulk-orders","bods","loot","gathering-node")
STRICT=("recipes","recipe","bulk-orders")
KINDS={"recipes":"recipe-template","recipe":"recipe-template","bulk-orders":"bulk-order-template"}

def _path(path): return normalize_slug(PurePosixPath(path.replace("\\","/")).parts[-3])
def candidate(source,doc): return normalize_slug(doc["id"]) if isinstance(doc,dict) and isinstance(doc.get("id"),str) else _path(source)
def _text(value,maximum=100,tag=False):
    if not isinstance(value,str) or not (value:=value.strip()) or len(value)>maximum:return None
    return normalize_slug(value) if tag else value

def convert(family,source,doc,collisions):
    slug=candidate(source,doc)
    if family in ("bods","loot","gathering-node"):
        return MigrationResult(source,family,slug,"legacy-only-authoritative",("runtime-quantities-timings-probabilities-or-rewards",),None,None)
    if not isinstance(doc,dict): return MigrationResult(source,family,slug,"invalid-source",("root-not-object",),None,None)
    if family=="bulk-orders" and "global_settings" in doc:
        return MigrationResult(source,family,slug,"legacy-only-authoritative",("runtime-bulk-order-system",),None,None)
    if slug in collisions:return MigrationResult(source,family,slug,"manual-review",("normalized-slug-collision",),None,None)
    name=_text(doc.get("name"))
    if name is None:return MigrationResult(source,family,slug,"manual-review",("missing-display-name",),None,None)
    spec={"display_name":name}
    for key,target in (("profession","profession_tag"),("station_type","station_kind"),("category","category_tag")):
        value=_text(doc.get(key),64,True)
        if value is not None:spec[target]=value
    target=f"templates/{family}/{slug}/v1.0.0/template.json"; result=MigrationResult(source,family,slug,"migrated",(),target,None)
    strict={"$schema":f"../../../schemas/{family}/v1.0.0/schema.json","contract_version":"1.0.0","id":f"{family}:{slug}","slug":slug,"family":family,"version":"1.0.0","authority":"declarative","intended_consumers":["llm-pipeline"],"compatibility":[],"dependencies":[],"spec_checksum":compute_spec_checksum(spec),"spec":spec}
    return replace(result,document=strict)

def schema(family):
    tag={"type":"string","pattern":"^[a-z0-9]+(?:-[a-z0-9]+)*$","maxLength":64}; props={"display_name":{"type":"string","minLength":1,"maxLength":100}}
    fields=("profession_tag","station_kind") if family in ("recipe","recipes") else ("profession_tag","category_tag")
    props.update({f:tag for f in fields})
    return {"$schema":"https://json-schema.org/draft/2020-12/schema","$id":f"https://ultimateodycer.com/schemas/{family}/1.0.0","title":f"Ultimate Odycer {family} Template v1","allOf":[{"$ref":"https://ultimateodycer.com/schemas/template-contract/1.0.0"},{"properties":{"spec":{"type":"object","required":["display_name"],"properties":props,"additionalProperties":False}}}]}
