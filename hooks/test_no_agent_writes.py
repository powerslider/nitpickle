"""Tests for the write-command guardrail. Stdlib only, run with:

    python3 -m unittest discover -s hooks -p "test_*.py"

The harness fires the hook per family (the hooks.json `if` condition). These
tests invoke the script directly with the family arg and a crafted command, so
they exercise the real allow/deny decision, including flag-order variants. The
only untested layer is the harness firing, which is the platform's `if` matcher.
"""
import json
import os
import subprocess
import sys
import unittest

HOOK = os.path.join(os.path.dirname(__file__), "no-agent-writes.py")


def run(family, command, env=None):
    full_env = dict(os.environ)
    full_env.pop("NITPICKLE_ALLOW_WRITES", None)
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, HOOK, family],
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True,
        text=True,
        env=full_env,
    )


def run_auto(command, env=None):
    """Self-dispatch path: no family argument, the Codex wiring. The hook gets
    the whole Bash command and finds the write itself."""
    full_env = dict(os.environ)
    full_env.pop("NITPICKLE_ALLOW_WRITES", None)
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
        capture_output=True,
        text=True,
        env=full_env,
    )


def denied(result):
    if not result.stdout.strip():
        return False
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


class TestUnconditional(unittest.TestCase):
    def test_git_commit_denied(self):
        self.assertTrue(denied(run("git-commit", "git commit -m fix")))

    def test_git_push_denied(self):
        self.assertTrue(denied(run("git-push", "git push origin main")))

    def test_git_push_force_denied(self):
        self.assertTrue(denied(run("git-push", "git push --force-with-lease")))

    def test_git_push_in_a_chain_denied(self):
        # The harness fires on the matched subcommand and passes the full command.
        self.assertTrue(denied(run("git-push", "make test && git push")))


class TestTokenDiscriminated(unittest.TestCase):
    def test_git_reset_hard_denied(self):
        self.assertTrue(denied(run("git-reset", "git reset --hard HEAD~1")))

    def test_git_reset_soft_allowed(self):
        self.assertFalse(denied(run("git-reset", "git reset --soft HEAD~1")))

    def test_git_reset_unstage_allowed(self):
        self.assertFalse(denied(run("git-reset", "git reset path.py")))

    def test_merge_continue_denied(self):
        self.assertTrue(denied(run("git-merge", "git merge --continue")))

    def test_merge_initiate_denied(self):
        self.assertTrue(denied(run("git-merge", "git merge feature")))

    def test_merge_abort_allowed(self):
        self.assertFalse(denied(run("git-merge", "git merge --abort")))

    def test_rebase_continue_denied(self):
        self.assertTrue(denied(run("git-rebase", "git rebase --continue")))

    def test_rebase_abort_allowed(self):
        self.assertFalse(denied(run("git-rebase", "git rebase --abort")))

    def test_cherry_pick_continue_denied(self):
        self.assertTrue(denied(run("git-cherry-pick", "git cherry-pick --continue")))

    def test_merge_with_global_dir_flag_denied(self):
        self.assertTrue(denied(run("git-merge", "git -C repo merge feature")))


class TestReadOnlySiblings(unittest.TestCase):
    """The harness `if` matcher fires on a string prefix, so read-only siblings
    that share it (git merge-base, git commit-graph) reach the script. They must
    pass: the skills compute diff bases with merge-base constantly."""

    def test_merge_base_allowed(self):
        self.assertFalse(denied(run("git-merge", "git merge-base main HEAD")))

    def test_merge_tree_allowed(self):
        self.assertFalse(denied(run("git-merge", "git merge-tree a b")))

    def test_merge_base_with_branch_named_merge_allowed(self):
        self.assertFalse(denied(run("git-merge", "git merge-base merge main")))

    def test_commit_graph_allowed(self):
        self.assertFalse(denied(run("git-commit", "git commit-graph write")))

    def test_commit_tree_allowed(self):
        self.assertFalse(denied(run("git-commit", "git commit-tree abc123")))


class TestGhPr(unittest.TestCase):
    def test_pr_merge_denied(self):
        self.assertTrue(denied(run("gh-pr", "gh pr merge 42 --squash")))

    def test_pr_create_denied(self):
        self.assertTrue(denied(run("gh-pr", "gh pr create --fill")))

    def test_pr_comment_denied(self):
        self.assertTrue(denied(run("gh-pr", "gh pr comment 42 --body hi")))

    def test_pr_review_approve_denied(self):
        self.assertTrue(denied(run("gh-pr", "gh pr review 42 --approve")))

    def test_pr_review_approve_reordered_denied(self):
        # Flag-order robust: PR number before the flag still denies.
        self.assertTrue(denied(run("gh-pr", "gh pr review --approve 42")))

    def test_pr_review_comment_allowed(self):
        # review-pr's sanctioned posting path must pass.
        self.assertFalse(denied(run("gh-pr", "gh pr review 42 --comment --body x")))

    def test_pr_review_request_changes_allowed(self):
        self.assertFalse(denied(run("gh-pr", "gh pr review 42 --request-changes -b x")))

    def test_pr_view_allowed(self):
        self.assertFalse(denied(run("gh-pr", "gh pr view 42 --json title")))

    def test_pr_diff_allowed(self):
        self.assertFalse(denied(run("gh-pr", "gh pr diff 42")))


class TestGhResources(unittest.TestCase):
    def test_repo_create_denied(self):
        self.assertTrue(denied(run("gh-repo", "gh repo create x --public")))

    def test_repo_view_allowed(self):
        self.assertFalse(denied(run("gh-repo", "gh repo view")))

    def test_release_create_denied(self):
        self.assertTrue(denied(run("gh-release", "gh release create v1")))

    def test_issue_create_denied(self):
        self.assertTrue(denied(run("gh-issue", "gh issue create --title x")))

    def test_issue_view_allowed(self):
        self.assertFalse(denied(run("gh-issue", "gh issue view 7")))


class TestCodexSelfDispatch(unittest.TestCase):
    """No-family path for harnesses (Codex) that fire on the whole Bash call.
    The script splits on shell operators and anchors family detection to each
    segment's leading token. These cover the two failures the design must fix."""

    def test_plain_commit_denied(self):
        self.assertTrue(denied(run_auto("git commit -m fix")))

    def test_chained_add_then_commit_denied(self):
        # The false negative: an index-anywhere scan would resolve to `add`.
        self.assertTrue(denied(run_auto("git add -A && git commit -m fix")))

    def test_chained_push_denied(self):
        self.assertTrue(denied(run_auto("make test && git push origin main")))

    def test_semicolon_chain_denied(self):
        self.assertTrue(denied(run_auto("git add . ; git commit -m x")))

    def test_string_mention_of_git_push_allowed(self):
        # The false positive: a command that merely mentions a write must pass.
        self.assertFalse(denied(run_auto('grep -r "git push" .')))

    def test_echo_mention_allowed(self):
        self.assertFalse(denied(run_auto('echo "run git commit first"')))

    def test_read_only_git_allowed(self):
        self.assertFalse(denied(run_auto("git status && git diff")))

    def test_merge_base_in_chain_allowed(self):
        self.assertFalse(denied(run_auto("git merge-base main HEAD && echo ok")))

    def test_sudo_wrapped_commit_denied(self):
        self.assertTrue(denied(run_auto("sudo git commit -m x")))

    def test_env_assignment_prefix_commit_denied(self):
        self.assertTrue(denied(run_auto("GIT_AUTHOR_NAME=x git commit -m y")))

    def test_gh_pr_create_in_chain_denied(self):
        self.assertTrue(denied(run_auto("git add . && gh pr create --fill")))

    def test_gh_pr_view_allowed(self):
        self.assertFalse(denied(run_auto("gh pr view 42 --json title")))

    def test_reset_hard_denied(self):
        self.assertTrue(denied(run_auto("git reset --hard HEAD~1")))

    def test_reset_soft_allowed(self):
        self.assertFalse(denied(run_auto("git reset --soft HEAD~1")))

    def test_env_override_allows_self_dispatch(self):
        r = run_auto("git commit -m x", env={"NITPICKLE_ALLOW_WRITES": "1"})
        self.assertFalse(denied(r))


class TestEscapeHatchAndFailOpen(unittest.TestCase):
    def test_env_override_allows(self):
        r = run("git-push", "git push origin main", env={"NITPICKLE_ALLOW_WRITES": "1"})
        self.assertEqual(r.returncode, 0)
        self.assertFalse(denied(r))

    def test_unknown_family_allows_with_diagnostic(self):
        r = run("git-bogus", "git bogus")
        self.assertEqual(r.returncode, 0)
        self.assertFalse(denied(r))
        self.assertIn("unknown family", r.stderr)

    def test_malformed_input_allows(self):
        r = subprocess.run(
            [sys.executable, HOOK, "git-push"],
            input="not json", capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0)
        self.assertFalse(denied(r))


if __name__ == "__main__":
    unittest.main()
