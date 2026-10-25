#!/usr/bin/env python3
"""synthesis-01: write round-0003/round.yaml from observed files (hashes computed here)."""
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

RD = Path(__file__).resolve().parents[3]          # round-0003
REPO = RD.parents[3]
LAB = REPO.parent / "forest-cover-lab"
SENT_SHA = "5b2e30e11d2ea9a990878f4bee643c11864daae3"
LAB_SHA = "c322e89fb96def2434c62776ac595f6cd995ef92"
GRAPH = "f70789df04b79ca8ec65e0094c571e0b3f6844afa2b88af2f8c9bcf1776a20f7"
ENDED = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).isoformat()
APPROVED = "2026-10-24T16:36:36+00:00"  # earliest recorded artifact of the session; operator message preceded it

def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(source, path, root, rev, status="captured"):
    return dict(source=source, path_or_identifier=path, revision=rev, sha256=h(root / path), capture_status=status)
S = lambda p: ref("sentinel-monthly-forest-cover", p, REPO, SENT_SHA)
L = lambda p: ref("forest-cover-lab", p, LAB, LAB_SHA)
R = lambda p: ref("round", p, RD, None)
def outputs(rel_paths):
    return {p: h(RD / p) for p in rel_paths}
def approval(basis): return dict(status="approved", approver="human operator (user in this conversation)", decided_utc=APPROVED, basis=basis)

BASIS = ("Operator message (artifacts/synthesis-01/operator_request.txt) asked to add a synthesis sub-agent, retask existing "
         "sub-agents if needed and allowed online extraction. decided_utc is a proxy: the earliest recorded session artifact; the "
         "message timestamp is not exposed. This graph was written by synthesis-01 after execution from that instruction; no graph "
         "image was presented for approval beforehand. Human confirmation of this record is pending (human_review).")
PRIVATE = dict(source="external-private", path_or_identifier="claude-code-session-system-and-runtime-instructions", revision=None, sha256=None, capture_status="not_captured")
WS_CLAUDE = dict(source="local-workspace", path_or_identifier="/Users/server/projects/CLAUDE.md", revision=None, sha256=h(REPO.parent / "CLAUDE.md"), capture_status="captured")
COMMON_LIMITS = ["Private host system/runtime instructions are not captured.",
                 "Claude Code client version is not exposed to the agent."]
RUNTIME = lambda ctx: dict(client_version=None, model_configuration={"model": "claude-opus-5-5 (reported by runtime)"},
                           context_mode=ctx, workspace_mode="shared", permission_summary="Claude Code auto mode; web fetch/search allowed by operator; writes limited by assignment")

def sub_files(base):
    return sorted(str(p.relative_to(RD)) for p in (RD / "artifacts" / base).glob("*") if p.is_file() and p.name != ".gitignore")

geo_out = sub_files("geo-01"); works_out = sub_files("works-01")
syn_report = sorted(str(p.relative_to(RD)) for p in (RD / "artifacts/synthesis-01").rglob("*") if p.is_file())

def sub_instance(iid, role, assign, retasks, attempts_spec, question, contract):
    atts = []
    for aid, start, end, extra_assign, tools in attempts_spec:
        loaded = [S("AGENTS.md"), S("CLAUDE.md"), WS_CLAUDE, L("AGENTS.md"), L("docs/agents.md"), L(role), R(assign), R(retasks[0])] + [R(a) for a in extra_assign] + [PRIVATE]
        atts.append(dict(
            attempt_id=aid, host="claude-code", started_utc=start, ended_utc=end, status="completed",
            model_if_known="claude-opus-5-5 (as reported by the subagent)", loaded_harness=loaded,
            prompt_ref="artifacts/synthesis-01/subagent_prompts.md",
            tool_access=tools, source_refs=["inputs/prior_rois.geojson"],
            output_refs=(geo_out if iid == "geo-01" else works_out),
            output_hashes=outputs(geo_out if iid == "geo-01" else works_out),
            checks=[f"Outputs listed in artifacts/{iid}/README.md and {iid}/execution.json",
                    "Agent declared no Sentinel/EO or audit-01 conclusions were read",
                    "synthesis-01 reviewed claims against images and ledgers"],
            limitations=COMMON_LIMITS + [
                "Lab AGENTS.md and docs/agents.md were read about 2 minutes after the attempt started, on a synthesis-01 harness update.",
                "Sentinel docs/agent_harness.md was not read by this subagent.",
                f"Outputs were written to round-0002/artifacts/{iid}/ and moved unchanged to round-0003 (artifacts/RELOCATION.md); internal absolute paths still name round-0002.",
                "Web searches and dynamic official services cannot be replayed exactly."],
            runtime=RUNTIME("fresh"),
            handoffs=[R(retasks[0])] + [R(a) for a in extra_assign],
            coordination_events=[],
            independence=dict(source_lineage_groups=(["LG-MARU-ORTHO", "LG-MARU-ETAK"] if iid == "geo-01" else ["LG-MARU-ETAK", "LG-KAUR-METSAREGISTER", "LG-TRANSP", "LG-ERR"]),
                              conclusion_exposure="not_received", evidence_inspected=["inputs/prior_rois.geojson"],
                              limitations=["Brief written by synthesis-01, which had seen Sentinel crops; the brief contained geometry and periods only."]),
        ))
    if iid == "works-01":
        atts[1]["coordination_events"] = [dict(kind="retry", detail="synthesis-01 retask 0002 (W4-W6: Halinga-Kangru, km positions) resumed the same subagent; outputs appended.",
                                               artifact=R("assignments/works-01-retask-0002.md"))]
        atts[1]["output_refs"] = works_out
        atts[0]["output_refs"] = ["artifacts/works-01/works_claims.csv"]
        atts[0]["output_hashes"] = {"artifacts/works-01/works_claims.csv": h(RD / "artifacts/works-01/works_claims.csv")}
        atts[0]["limitations"].append("First-attempt files were later appended by attempt 0002; only the final state is hashed.")
    return dict(id=iid, role=role, role_scope="standing", host_planned="claude-code", selection_status="completed", assignment=assign,
                delegation=dict(mode="native_subagent", parent_instance_id="synthesis-01", question=question, output_contract=contract,
                                permitted_writes=[f"reviews/road-like-ndvi-2025-2026-monthly/rounds/round-0002/artifacts/{iid}/ (moved to round-0003)"],
                                budget=dict(tool_call_limit=120, elapsed_seconds_limit=3600, cost_usd_limit=None)),
                harness_sources=[dict(L(role), capture_status="selected"), dict(R(assign), capture_status="selected")] + [dict(R(r), capture_status="selected") for r in retasks],
                actual_executions=atts)

geo = sub_instance("geo-01", "agent_harness/roles/national-geospatial-evidence.md", "assignments/geo-01.md", ["assignments/geo-01-retask-0001.md"],
    [("geo-01-attempt-0001", "2026-10-24T16:37:40+00:00", "2026-10-24T16:51:18+00:00", [], ["WebFetch", "WebSearch", "Bash (curl, python)", "Read"])],
    "Presence and width of road/track/rail along ROI-01/02 in dated Maa- ja Ruumiamet orthophotos, maps and ETAK; resolve flight dates.",
    "geo_sources.csv, geo_claims.csv, geo_primary_evidence.json, images/, README.md, execution.json")
works = sub_instance("works-01", "agent_harness/roles/official-infrastructure-records.md", "assignments/works-01.md", ["assignments/works-01-retask-0001.md"],
    [("works-01-attempt-0001", "2026-10-24T16:37:40+00:00", "2026-10-24T16:51:21+00:00", [], ["WebFetch", "WebSearch", "Bash (curl, python)", "Read"]),
     ("works-01-attempt-0002", "2026-10-24T16:52:00+00:00", "2026-10-24T17:00:00+00:00", ["assignments/works-01-retask-0002.md"], ["WebFetch", "WebSearch", "Bash (curl, python)", "Read"])],
    "Identity, 2025 existence and 2024-2026 works for ROI-01/02 from official road/rail/plan/cadastre/forest-register records.",
    "works_ledger.csv, works_claims.csv, works_primary_evidence.json, images/, README.md, execution.json")

syn_loaded = [S("AGENTS.md"), S("CLAUDE.md"), S("docs/agent_harness.md"), WS_CLAUDE, L("AGENTS.md"), L("docs/agents.md"),
              L("agent_harness/roles/national-geospatial-evidence.md"), L("agent_harness/schemas/round.schema.json"),
              L("agent_harness/scripts/validate_round.py"), L("agent_harness/scripts/round_graph.py"),
              R("roles/evidence-synthesis.md"), R("assignments/synthesis-01.md"), R("assignments/geo-01.md"), R("assignments/works-01.md"), PRIVATE]
synthesis = dict(id="synthesis-01", role="roles/evidence-synthesis.md", role_scope="round_only", host_planned="claude-code", selection_status="completed",
    assignment="assignments/synthesis-01.md",
    delegation=dict(mode="sequential_role", parent_instance_id=None,
        question="Scan, analyse and summarise sub-agent results; retask as needed; offline HTML report on ROI-01/02 2025 existence and widening.",
        output_contract="synthesis_report/ (index.html, assets, data, evidence, bundle_manifest.json), analysis/, scripts/",
        permitted_writes=["reviews/road-like-ndvi-2025-2026-monthly/rounds/round-0003/"],
        budget=dict(tool_call_limit=None, elapsed_seconds_limit=None, cost_usd_limit=None)),
    harness_sources=[dict(R("roles/evidence-synthesis.md"), capture_status="selected"), dict(R("assignments/synthesis-01.md"), capture_status="selected")],
    actual_executions=[dict(attempt_id="synthesis-01-attempt-0001", host="claude-code", started_utc=APPROVED, ended_utc=ENDED, status="completed",
        model_if_known="claude-fable-5-1 at session start, claude-opus-5-5 from mid-session (runtime switch reported by host)",
        loaded_harness=syn_loaded, prompt_ref="artifacts/synthesis-01/operator_request.txt",
        tool_access=["Bash", "Read", "Write", "Agent (2 background subagents)", "SendMessage"],
        source_refs=["inputs/prior_rois.geojson", "round-0002/artifacts/audit-01/audit_report.md",
                     "runs/aoi-s2-jja-2025-2026-calibrated/source_windows", "artifacts/geo-01", "artifacts/works-01"],
        output_refs=syn_report, output_hashes=outputs(syn_report),
        checks=["All 61 local links/images in synthesis_report/index.html resolve; no script or external stylesheet",
                "Headless Chromium render at 1100 px and 390 px widths inspected",
                "bundle_manifest.json lists SHA-256 for every bundle file",
                "Report numbers cross-checked against analysis/transects.csv and agent claims"],
        limitations=COMMON_LIMITS + [
            "Read-only inspection began a few minutes before started_utc; started_utc is the first recorded write.",
            "Lab AGENTS.md and docs/agents.md were read at 2026-10-24T17:01Z, after most work.",
            "Sentinel analysis uses two single scenes on a 20 m EPSG:6933 grid; diagnostic contrast setting is report configuration, not a Lab threshold.",
            "Round-graph approval is a retrospective record of the operator instruction; human confirmation pending."],
        runtime=RUNTIME("inherited"),
        handoffs=[R("assignments/geo-01-retask-0001.md"), R("assignments/works-01-retask-0001.md"), R("assignments/works-01-retask-0002.md")],
        independence=dict(source_lineage_groups=["LG-S2", "LG-MARU-ORTHO", "LG-MARU-ETAK", "LG-KAUR-METSAREGISTER", "LG-TRANSP", "LG-ERR"],
                          conclusion_exposure="received", evidence_inspected=["artifacts/geo-01", "artifacts/works-01", "round-0002/artifacts/audit-01/audit_report.md"],
                          limitations=["Synthesis reads all branch outputs by design; it is not an independent challenge.",
                                       "Maa- ja Ruumiamet orthophotos, maps, cadastre and plans share one agency lineage."]),
        coordination_events=[dict(kind="retry", detail="works-01 resumed with retask 0002 to resolve ROI-02 north identity (Halinga-Kangru).", artifact=R("assignments/works-01-retask-0002.md")),
                             dict(kind="reconciliation", detail="Branch claims and own Sentinel-2 analysis joined into synthesis_claims.csv; conflicts listed in report section 8.",
                                  artifact=R("artifacts/synthesis-01/synthesis_report/data/synthesis_claims.csv"))])])

round_ = dict(schema_version="1.1", round_id="road-like-ndvi-2025-2026-monthly-round-0003", kind="comparison", status="active",
    created_utc=APPROVED,
    question="For ROI-01 and ROI-02: did the outlined roads exist in 2025, and are there signs of artificial widening (pre vs post July 2025)? Use Maa- ja Ruumiamet / Transpordiamet records.",
    frame=dict(aoi_ref="inputs/aoi.geojson and inputs/prior_rois.geojson, byte-identical copies of round-0002 inputs",
        period="Before July 2025 (<2025-07-01) vs after July 2025 (>=2025-07-01, to 2026-10-24)",
        measurement="Dated orthophoto/map presence and width; official records; Sentinel-2 NDVI cross-profiles 2025-06-15 vs 2026-06-20 (20 m)",
        competing_hypotheses=["Pre-existing road widened 2025-2026", "New alignment or corridor clearing", "Railway corridor misidentified as road",
                              "Seasonal/agricultural or sensor artifact", "Outline offset from the real feature"]),
    repos=dict(forest_cover_lab=LAB_SHA, sentinel_monthly_forest_cover=SENT_SHA, lab_graph_revision=GRAPH),
    instances=[synthesis, geo, works],
    graph=dict(mode="stepwise",
        approval=dict(proposed_by="synthesis-01 (Claude Code), recorded after execution; successor of round-0002",
                      planning_record_id="road-like-ndvi-2025-2026-monthly-round-0003/graph", **approval(BASIS)),
        nodes=[
          dict(id="inputs", kind="input", label="ROIs, AOI, windows, audit-01 report, operator request",
               outputs=["aoi.geojson", "prior_rois.geojson", "window_spec.yaml", "audit_report.md", "operator_request.txt"]),
          dict(id="operator-gate", kind="gate", label="Human: authorize synthesis, retasking and online public sources", approver="human", approval=approval(BASIS)),
          dict(id="geo-01", kind="agent", instance="geo-01", loop=dict(max_iterations=2, until="Claims cite dated sources or blockers are recorded"),
               outputs=["geo_sources.csv", "geo_claims.csv", "geo_primary_evidence.json"],
               step_plan=dict(plan_ref="assignments/geo-01-retask-0001.md", plan_sha256=h(RD / "assignments/geo-01-retask-0001.md"), approval=approval(BASIS))),
          dict(id="works-01", kind="agent", instance="works-01", loop=dict(max_iterations=2, until="Claims trace to geometry and event dates or indeterminate"),
               outputs=["works_ledger.csv", "works_claims.csv", "works_primary_evidence.json"],
               step_plan=dict(plan_ref="assignments/works-01-retask-0001.md", plan_sha256=h(RD / "assignments/works-01-retask-0001.md"), approval=approval(BASIS))),
          dict(id="synthesis-01", kind="agent", instance="synthesis-01", loop=dict(max_iterations=2, until="Report answers each question with cited evidence or indeterminate"),
               outputs=["synthesis_report/index.html", "synthesis_claims.csv", "bundle_manifest.json"],
               step_plan=dict(plan_ref="assignments/synthesis-01.md", plan_sha256=h(RD / "assignments/synthesis-01.md"), approval=approval(BASIS))),
          dict(id="review-gate", kind="gate", label="Human: review synthesis report and agent evidence", approver="human",
               approval=dict(status="pending", approver=None, decided_utc=None, basis=None)),
        ],
        edges=[
          dict(**{"from": "inputs", "to": "operator-gate"}, carries=["prior_rois.geojson", "window_spec.yaml", "audit_report.md", "operator_request.txt"]),
          dict(**{"from": "operator-gate", "to": "geo-01"}, carries=["prior_rois.geojson", "window_spec.yaml"]),
          dict(**{"from": "operator-gate", "to": "works-01"}, carries=["prior_rois.geojson", "window_spec.yaml"]),
          dict(**{"from": "operator-gate", "to": "synthesis-01"}, carries=["prior_rois.geojson", "audit_report.md", "operator_request.txt"]),
          dict(**{"from": "geo-01", "to": "synthesis-01"}, carries=["geo_sources.csv", "geo_claims.csv", "geo_primary_evidence.json"]),
          dict(**{"from": "works-01", "to": "synthesis-01"}, carries=["works_ledger.csv", "works_claims.csv", "works_primary_evidence.json"]),
          dict(**{"from": "synthesis-01", "to": "review-gate"}, carries=["synthesis_report/index.html", "synthesis_claims.csv", "bundle_manifest.json"]),
        ],
        independence_groups=[["geo-01", "works-01"]]),
    human_review=dict(status="pending", reviewer=None, decision=None, basis=None))
(RD / "round.yaml").write_text(yaml.safe_dump(round_, sort_keys=False, allow_unicode=True, width=110))
print("wrote", RD / "round.yaml")
