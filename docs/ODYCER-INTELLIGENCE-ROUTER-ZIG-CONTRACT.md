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


## Predictive intent and shared presentation

The private Zig runtime SHOULD distribute compact semantic intents ahead of their expected execution time when the action is sufficiently stable. Prediction is advisory until authoritative commit.

A predictive record SHOULD identify:

- actor and optional target;
- stable sequence/event identifier;
- server timeline anchor;
- semantic action category;
- bounded parameters required for gameplay reconstruction;
- deterministic presentation seed;
- prediction stability/confidence;
- interruptibility/cancellation semantics;
- presentation-profile protocol version.

Clients MUST distinguish predicted/prepared state from authoritative committed gameplay state.

### Action stability and network horizon

Prediction horizon SHOULD adapt to measured action stability. Stable locomotion, schedules, or long casts MAY be announced farther ahead. Chaotic close combat SHOULD use a short horizon or conventional snapshots.

A learned estimator MAY assist stability estimation only behind a bounded, validated adapter. Deterministic rules remain a valid baseline and fallback.

Repeated correction cost MUST be measured. The system SHOULD automatically shorten prediction horizons when correction/divergence exceeds policy.

## Shared server timeline

Multiplayer clients MUST reconstruct shared visible events against a common server-time/tick anchor rather than packet-arrival time.

A client receiving an event early SHOULD schedule it for the declared server time. A late client SHOULD seek to the appropriate presentation phase when the profile supports deterministic reconstruction.

Prediction therefore serves both bandwidth reduction and cross-player synchronization.

## Synchronization classes

Presentation consequences SHOULD be classified by the minimum synchronization needed:

- S0 local: purely perceptual micro-detail with no shared semantic meaning;
- S1 deterministic-shared: clients derive the same visible variant from event id, server time, seed, and profile version;
- S2 synchronized-semantic: server distributes the shared social/semantic event and timing, while clients derive audiovisual detail;
- S3 authoritative-gameplay: server owns action validity and world-state consequences.

Examples are intentionally non-normative. A cosmetic blink may be S0; a deterministic hit reaction may be S1; a socially meaningful salute may be S2; damage, stun, cast validity, or death is S3.

## Presentation consequence engine

The server SHOULD transmit causes and authoritative consequences rather than audiovisual implementation details whenever the latter can be derived safely.

For example, an authoritative impact event may describe semantic contact class, position, direction, and force class. The client presentation layer may derive animation, sound, particles, decals, haptics, camera response, and IK from its local versioned presentation profile.

The server SHOULD NOT name individual sound files, particle assets, animation clips, or client rendering commands unless a future protocol requirement proves that semantic derivation is insufficient.

Animation-local events such as foot contact MAY drive local surface-dependent footsteps and related cosmetic effects without server traffic when they have no gameplay authority.

## Dialogue and barks

Decorative barks MAY be selected client-side from an approved versioned profile using deterministic event seed when cross-player consistency is desired.

Dialogue that carries gameplay state, quest information, negotiation outcome, generated factual content, or other authoritative meaning MUST originate from a validated server-side semantic event/content path.

Text/voice preparation MAY occur ahead of display time, but clients MUST NOT expose prepared content before its shared presentation time when synchronization matters.

## Semantic state versus visual detail

The protocol MUST preserve shared semantic truth while allowing presentation detail to scale locally.

Example: the server may state that NPC A is attending to player B. A close client may represent this with eye, head, neck, shoulder, and facial motion; a distant client may use only coarse facing or no visible micro-detail. Both clients retain the same semantic attention target.

This principle applies to gaze, posture, held objects, social state, interaction state, and other observable semantics.

## Presentation LOD

Presentation LOD is independent from graphical, simulation, cognitive, and network/prediction LOD.

Recommended semantic levels:

- P0: not perceptible; no micro-presentation work;
- P1: crowd/distant; locomotion and principal action;
- P2: medium importance; major posture and reactions;
- P3: near/important; gaze, emotes, local SFX/VFX, bounded IK;
- P4: very near/direct interaction/VR salience; facial, lips, hands/fingers where supported, breathing and micro-emotes.

Distance MUST NOT be the sole selector. A client SHOULD score perceptual importance using bounded inputs such as visibility, screen coverage, direct interaction, current combat target, speaking state, gaze/aim focus, and narrative/gameplay salience.

Presentation LOD is normally client-specific. The same authoritative NPC may be P1 for one player and P4 for another.

Clients SHOULD enforce local P3/P4 budgets and degrade the least perceptually important actors first under load.

## Crowd/group prediction

For large cohorts, the server MAY transmit one group semantic intent plus deterministic seed and member identifiers/roles. Clients MAY derive bounded per-member timing and presentation variation from a stable hash of group event id, actor id, seed, and presentation-profile version.

Individual authoritative overrides MUST supersede the group prediction.

This permits a shared charge, retreat, formation transition, or other cohort action to remain visually consistent across observers without transmitting every cosmetic detail per member.

## Join-in-progress and correction

A client entering relevance mid-event SHOULD receive enough presentation anchor data to reconstruct the current semantic phase rather than replaying the event from its beginning.

Prediction cancellation/correction MUST identify the affected sequence and effective server time. Clients SHOULD transition gracefully to the corrected authoritative state.

The protocol SHOULD measure correction rate, late-event rate, and cross-client presentation divergence.

## Deterministic presentation boundary

Determinism is required only where shared perception benefits from it. S0 details MAY intentionally differ between clients.

For shared reconstruction, the effective key SHOULD include at least:

event/sequence id + actor id + server timeline anchor + deterministic seed + presentation-profile protocol version.

Presentation-profile content remains a client asset concern. The server carries only the semantic/version contract needed to avoid incompatible reconstruction.

## Additional benchmark requirements

The 1,000-NPC benchmark SHOULD include multiple simulated clients with different latency/jitter and camera relevance.

Measure additionally:

- bytes per NPC-second and per visible cohort;
- predictive horizon distribution;
- prediction cancellation/correction rate;
- late-arrival rate;
- join-in-progress reconstruction error;
- cross-client semantic divergence;
- cross-client synchronized-presentation timing error;
- P0-P4 population per client;
- P3/P4 budget pressure and degradation rate.

The target is not identical pixels on every client. The target is identical authoritative/semantic reality, bounded synchronization error for shared events, and locally scalable perceptual detail.
