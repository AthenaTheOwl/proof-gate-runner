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
st.subheader("try it on your own text")
st.caption(
    "paste any prose below to run the same voice_lint gate against it -- "
    "banlist words and antithetical-reversal sentence shapes."
)
sample = st.text_area(
    "text to lint",
    value="This robust framework demonstrates synergy. It's not slow; it's fast.",
    height=120,
)
if sample.strip():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        scratch = Path(td) / "pasted.md"
        scratch.write_text(sample, encoding="utf-8")
        own = voice_lint_run(scratch)
    if own:
        st.warning(f"voice_lint found {len(own)} finding(s) in your text:")
        st.dataframe(
            [
                {"rule": f.rule_id, "line": f.line, "message": f.message}
                for f in own
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("voice_lint: clean. no banlist words or reversal shapes.")

st.caption(
    "v0 ships voice_lint + spec_check. the gates + dispatcher live in "
    "`scripts/lib/`; this page runs them against the committed "
    "`examples/demo-repo`. repo: github.com/AthenaTheOwl/proof-gate-runner"
)
