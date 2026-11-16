"""Real end-to-end run through the same workflow the UI uses: Jira -> Claude -> GitHub -> browser tests
-> report -> Jira. Approves every drafted test case except the last, which it rejects, to exercise
the review gate.

REAL WRITES: commits the .feature file and the report to GitHub and attaches the report + comment
to the Jira ticket. Refuses to run without --confirm-writes.

    python -m scripts.e2e_real <jira-ticket-link> --confirm-writes
"""
import sys
import time

from agent_app import workflow
from agent_app.config import ServiceError
from agent_app.deps import Services


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or "--confirm-writes" not in sys.argv:
        print(__doc__)
        return 2
    svc = Services()
    t0 = time.time()
    try:
        run = workflow.new_run(svc, args[0])
        workflow.advance_to_review(svc, run, on_step=lambda m: print(f"[{time.time() - t0:5.1f}s] {m}"))
        print(f"  {len(run['criteria'])} criteria, {len(run['scenarios'])} test cases, "
              f"uncovered={run['uncovered']}, warnings={run['warnings']}")
        for s in run["scenarios"][:-1]:
            workflow.set_decision(svc, run, s["tc_id"], "approved")
        workflow.set_decision(svc, run, run["scenarios"][-1]["tc_id"], "rejected")
        workflow.push_approved(svc, run)
        print(f"[{time.time() - t0:5.1f}s] pushed: {run['commit_url']}")
        ids = [s["tc_id"] for s in workflow.approved(run)]
        workflow.execute(svc, run, ids, on_step=lambda m: print(f"[{time.time() - t0:5.1f}s] {m}"))
        for r in run["results"]:
            print(f"  {r['tc_id']} {r['status']:6} {r['title']}" + (f"  <- {r['reason'][:100]}" if r["reason"] else ""))
        print(f"  {run['report_title']}: {run['summary']['status']} {run['summary']['pass_pct']}%")
        workflow.attach_to_jira(svc, run)
        print(f"[{time.time() - t0:5.1f}s] report committed: {run['report_commit_url']}")
        print(f"  final status: {svc.store.get_run(run['id'])['status']}; total {time.time() - t0:.0f}s")
    except (ServiceError, ValueError) as exc:
        print(f"FAILED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
