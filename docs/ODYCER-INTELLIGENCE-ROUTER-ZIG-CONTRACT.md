# Odycer Intelligence Router — Zig integration contract

Status: experimental design contract  
Runtime authority: private Zig server only  
Public registry authority: none

## Goal

Define the boundary for an Ultimate Odycer NPC intelligence stack that minimizes compute while preserving deterministic server authority. This document does not publish runtime weights, behavior trees, prompts, model endpoints, balance values, or server configuration.

## Core rule

The server MUST attempt the cheapest sufficient decision path and MUST remain authoritative over state mutation.

A NPC capability tier is a ceiling, not a mandatory execution tier. A high-capability NPC MAY execute ordinary actions through the CLASSIC path.

## Cognitive LOD

The private Zig adapter SHOULD support these semantic levels:

- I0 dormant: persisted/statistical state only.
- I1 simulated: coarse scheduled world transitions.
- I2 classic: deterministic FSM/rules/timers/RNG.
- I3 reactive: CLASSIC plus a bounded fast-decision adapter (for example JEV-like logic).
- I4 planning: bounded hierarchical planning.
- I5 cognitive: bounded learned/model-assisted reasoning.

Promotion MUST be explicit, budgeted, observable, and reversible. Demotion SHOULD occur as soon as the higher tier is no longer required.

## Intelligence Router

Conceptual route:

1. exact deterministic rule / CLASSIC;
2. cached or reusable decision;
3. bounded fast-decision adapter;
4. planner;
5. approximate/small-model specialist;
6. expensive cognitive worker.

The adapter MUST fail closed when a result is invalid, stale, unauthorized, over budget, or below its configured confidence policy.

No model result may directly mutate authoritative world state.

## CLASSIC brain

CLASSIC is the default for low-complexity NPCs and the fallback execution layer for more capable NPCs.

Representative primitive states include idle, wander, patrol, guard, follow, chase, attack, flee, work, eat, sleep, return-home, and protect-target.

These names are illustrative integration vocabulary only; this registry does not define their runtime transitions or weights.

## Batch AI

The scheduler SHOULD batch work at four independent layers:

- simulation cohorts;
- group/squad decisions;
- shared-situation decisions;
- model inference.

Batching MUST NOT erase per-NPC identity. Shared results are intents or parameterized orders; individual execution remains filtered by authoritative NPC state.

## Shared perception

The Zig runtime SHOULD compute spatial/perception queries once per relevant world event or spatial cohort when safe, then distribute bounded observations to affected NPCs.

Perception results are observations, not permissions to mutate world state.

## Shared navigation

For cohorts with a common destination, the runtime MAY use shared corridors, flow fields, or equivalent group navigation, with local steering and individual fallback near dynamic obstacles.

## Scheduler and budgets

AI work MUST NOT block the authoritative network/world tick on an external or expensive inference.

Priority classes SHOULD distinguish at least:

- reflex/combat;
- local movement;
- tactical planning;
- social decisions;
- economy;
- background world simulation.

Non-urgent work MAY be deferred, coalesced, cached, or demoted when the current tick budget is exhausted.

## Asynchronous cognitive workers

Expensive model calls MUST execute asynchronously behind bounded queues and circuit breakers.

While a cognitive request is pending, the NPC MUST continue through an approved lower-tier behavior.

Returned results MUST pass validation and authority checks before becoming an intention.

## Decision reuse / Parcimonia boundary

A routing layer MAY compute a bounded situation signature from non-secret runtime features and attempt:

exact cache -> approximate reuse -> existing cohort -> new batch -> higher-cost route.

Approximate reuse MUST expose confidence/abstention and MUST NOT silently substitute a merely similar identifier or world object.

## Personality preservation

Batch decisions SHOULD produce a shared intent. Individual authoritative state MAY then specialize execution using bounded traits, relationships, health, equipment, memory references, and deterministic seed/state.

## Observability

Every routed decision SHOULD record enough structured telemetry to benchmark:

- selected cognitive LOD;
- selected route;
- batch/cohort identifier when applicable;
- cache/reuse outcome;
- latency;
- budget consumed;
- confidence/abstention where applicable;
- promotion/demotion reason;
- final validated action category;
- consequence/success signal when available.

Telemetry MUST NOT expose secrets, prompts, private model endpoints, or raw private provenance.

## Benchmark gate

Before enabling a new route by default, compare it against the cheaper baseline on representative workloads.

The first target benchmark SHOULD include approximately 1,000 simulated NPCs with a majority on CLASSIC/Reactive tiers and a small minority eligible for planning or cognitive promotion.

Measure at minimum:

- NPC decisions per second;
- CPU time;
- memory;
- P50/P95/P99 decision latency;
- batch/cohort hit rate;
- cache/reuse hit rate;
- promotions by tier;
- expensive inference calls avoided;
- invalid/abstained decisions;
- deterministic replay divergence.

No performance claim is valid without reproducible evidence.

## Adapter boundary

The public registry may expose symbolic references such as `behavior_profile_id`. The private Zig adapter resolves those references to runtime policy.

Required stages remain:

verify -> resolve -> project -> bind -> route -> validate action -> authoritative mutation

The public registry MUST NOT contain runtime decision weights, behavior trees, model configuration, prompts, server addresses, or execution commands.

## Proposed private Zig modules

Names are recommendations, not claims about the current private repository:

- `ai/classic_brain.zig`
- `ai/cognitive_lod.zig`
- `ai/intelligence_router.zig`
- `ai/batch_scheduler.zig`
- `ai/perception_batch.zig`
- `ai/navigation_batch.zig`
- `ai/action_contract.zig`
- `ai/decision_telemetry.zig`

The server implementation should begin with CLASSIC + Cognitive LOD + scheduler telemetry, then add batching, and only then add higher-cost routes behind disabled-by-default feature gates.
