"""proof-gate-runner -- live demo (Streamlit Community Cloud).

Wraps the no-arg `demo` verb (scripts/lib/gates.py run_demo) as an
interactive page. It runs the same v0 gates (voice_lint, spec_check)
against the committed examples/demo-repo fixture and renders the same
ranked result the terminal prints -- pass/fail per gate, findings ranked
by rule, the top offender -- plus a per-finding table and a paste-box so
you can voice_lint your own text. No network, no secrets: it reads the
committed fixture and runs the committed gate code directly.

Deploy: Streamlit Community Cloud -> New app -> repo
AthenaTheOwl/proof-gate-runner, branch main, main file streamlit_app.py.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import streamlit as st

REPO = Path(__file__).resolve().parent
LIB = REPO / "scripts" / "lib"
# the gate modules do `from gates import Finding`, so scripts/lib must be
# on sys.path before we import any of them.
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

try:
    import gates  # noqa: E402  (path mutated above on purpose)
    from voice_lint import run as voice_lint_run  # noqa: E402
except Exception as exc:  # pragma: no cover - import-time guard for cloud
    st.set_page_config(page_title="proof-gate-runner", layout="wide")
    st.title("proof-gate-runner")
    st.warning(f"could not import the gate code under scripts/lib: {exc}")
    st.stop()


def short_rule(rule_id: str) -> str:
    return gates._short_rule(rule_id)


st.set_page_config(page_title="proof-gate-runner -- typed proof gates", layout="wide")
st.title("proof-gate-runner")
st.caption(
    "typed proof gates for AI-generated PRs. this runs the same `demo` verb "
    "the CLI prints -- every v0 gate against the committed examples/demo-repo "
    "fixture -- and shows which bug classes the tree trips, ranked."
)

fixture = gates._demo_fixture_dir()
if not fixture.exists():
    st.warning(f"demo fixture not found at {fixture}")
    st.stop()

# mirror run_demo: run every gate in the registry against the fixture.
results = [gates._run_one(name, fixture) for name in gates.REGISTRY]
all_findings = [f for r in results for f in r.findings]

total = len(all_findings)
failing = [r for r in results if not r.passed]

c1, c2, c3 = st.columns(3)
c1.metric("gates run", len(results))
c2.metric("findings", total)
c3.metric("gates failing", len(failing), help="a gate fails on any fail-severity finding")

st.subheader("gates")
st.dataframe(
    [
        {
            "gate": r.gate,
            "result": "pass" if r.passed else "FAIL",
            "findings": len(r.findings),
            "rules that fired": ", ".join(
                sorted({short_rule(f.rule_id) for f in r.findings}) or ["-"]
            ),
            "duration ms": r.duration_ms,
        }
        for r in results
    ],
    use_container_width=True,
    hide_index=True,
)

# headline: the top rule by fire count, same as the terminal summary.
counts = Counter(short_rule(f.rule_id) for f in all_findings)
if counts:
    worst_rule, worst_n = counts.most_common(1)[0]
    example = next(f for f in all_findings if short_rule(f.rule_id) == worst_rule)
    loc = example.path or "(no path)"
    if example.line is not None:
        loc += f":{example.line}"
    st.info(
        f"**top rule:** `{worst_rule}` fired {worst_n}x "
        f"(first at {loc}). that is where a reviewer drowning in AI PRs "
        f"should look first."
    )
else:
    st.success("no findings -- the scanned tree is clean.")

st.subheader("findings ranked by rule")
st.dataframe(
    [{"rule": rule, "fired": n} for rule, n in counts.most_common()],
    use_container_width=True,
    hide_index=True,
)

# one interactive control: filter the per-finding table by gate.
st.subheader("every finding")
gate_names = ["(all)"] + [r.gate for r in results]
pick = st.selectbox("filter by gate", gate_names, index=0)
shown = all_findings if pick == "(all)" else [
    f for r in results if r.gate == pick for f in r.findings
]
st.dataframe(
    [
        {
            "severity": f.severity,
            "rule": f.rule_id,
            "path": f.path or "(no path)",
            "line": f.line,
            "message": f.message,
        }
        for f in shown
    ],
    use_container_width=True,
    hide_index=True,
)

with st.expander("the committed demo fixture (why it trips these gates)"):
    st.markdown(
        f"the fixture lives at `examples/demo-repo/` and is planted on "
        f"purpose with banlist words, antithetical-reversal shapes, and an "
        f"unreferenced `R-*` requirement id. scanned path: `{fixture}`."
    )
    for fp in sorted(fixture.rglob("*")):
        if fp.is_file():
            st.markdown(f"- `{fp.relative_to(fixture).as_posix()}`")

st.divider()
st.subheader("run the gates on your own input")
st.caption(
    "this is the same engine the committed view runs above -- `gates._run_one`, "
    "the v0 dispatcher -- pointed at text you write instead of the planted "
    "fixture. write a doc, pick which gates fire, and get the real per-gate "
    "verdict live: pass/FAIL, every finding, the top rule. nothing is "
    "hardcoded; this calls the committed gate code in-process."
)

own_gates = st.multiselect(
    "gates to run",
    options=list(gates.REGISTRY),
    default=list(gates.REGISTRY),
    help=(
        "voice_lint scans your prose for banlist words + reversal shapes. "
        "spec_check needs a specs/*/requirements.md layout, so it only fires "
        "if you upload a tree; on pasted prose it has nothing to scan."
    ),
)

sample = st.text_area(
    "your text (treated as a .md file the gates scan)",
    value="This robust framework demonstrates synergy. It's not slow; it's fast.",
    height=140,
)

if not own_gates:
    st.info("pick at least one gate to run.")
elif sample.strip():
    import tempfile

    # write the pasted text into a scratch tree and run the REAL dispatcher
    # against it -- exactly the call the committed view makes, just on a
    # different --path. _run_one loads the gate module from the registry,
    # invokes its run(path), and times it, so the verdict here is produced
    # by the same code path a CI run uses.
    with tempfile.TemporaryDirectory() as td:
        scratch_root = Path(td)
        (scratch_root / "pasted.md").write_text(sample, encoding="utf-8")
        own_results = [gates._run_one(name, scratch_root) for name in own_gates]

    own_findings = [f for r in own_results for f in r.findings]
    own_failing = [r for r in own_results if not r.passed]

    m1, m2, m3 = st.columns(3)
    m1.metric("gates run", len(own_results))
    m2.metric("findings", len(own_findings))
    m3.metric(
        "gates failing",
        len(own_failing),
        help="a gate fails on any fail-severity finding",
    )

    st.dataframe(
        [
            {
                "gate": r.gate,
                "result": "pass" if r.passed else "FAIL",
                "findings": len(r.findings),
                "rules that fired": ", ".join(
                    sorted({short_rule(f.rule_id) for f in r.findings}) or ["-"]
                ),
                "duration ms": r.duration_ms,
            }
            for r in own_results
        ],
        use_container_width=True,
        hide_index=True,
    )

    own_counts = Counter(short_rule(f.rule_id) for f in own_findings)
    if own_counts:
        worst_rule, worst_n = own_counts.most_common(1)[0]
        st.warning(
            f"**FAIL** -- {len(own_findings)} finding(s). top rule: "
            f"`{worst_rule}` fired {worst_n}x. this PR would not pass the gate."
        )
        st.dataframe(
            [
                {
                    "severity": f.severity,
                    "rule": f.rule_id,
                    "line": f.line,
                    "message": f.message,
                }
                for f in own_findings
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "edit the text above to drive the verdict to pass -- drop the "
            "banlist words and the `not X; it's Y` shape and the gate clears."
        )
    else:
        st.success(
            "**pass** -- no fail-severity findings. your text clears the "
            "selected gate(s)."
        )
else:
    st.info("write some text above to run the gates against it.")

st.caption(
    "v0 ships voice_lint + spec_check. the gates + dispatcher live in "
    "`scripts/lib/`; this page runs them against the committed "
    "`examples/demo-repo`. repo: github.com/AthenaTheOwl/proof-gate-runner"
)
