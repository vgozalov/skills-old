# shellcheck shell=bash
# Pins that parallel-build is self-contained: its own workspace, final review, worktree
# setup and finishing procedure, and no hand-off to a skill shipped elsewhere.

SKILL_DIR="$REPO_ROOT/skills/parallel-build"

test_no_hand_off_to_an_outside_plugin() {
  local hits
  # The plugin name is split so this file does not mention it either.
  hits=$(git -C "$REPO_ROOT" grep -niE "super""powers" -- . || true)
  [ -z "$hits" ] || fail "outside plugin still named:
$hits"
}

test_build_workspaces_live_under_parallel_build() {
  local out
  git init -q -b main repo && mkdir -p repo/docs/plans && : > repo/docs/plans/feature.md
  out=$(cd repo && bash "$SKILL_DIR/scripts/plan-workspace" docs/plans/feature.md)
  assert_contains "$out" "/.parallel-build/feature" "default workspace"
}

test_review_worktree_and_finishing_procedures_ship_with_the_skill() {
  local body file
  body=$(cat "$SKILL_DIR/SKILL.md")
  for file in final-reviewer-prompt.md worktree.md finishing.md; do
    [ -f "$SKILL_DIR/$file" ] || fail "$file missing"
    assert_contains "$body" "./$file" "linked from SKILL.md"
  done
}

test_finishing_never_offers_discard_unasked() {
  local body
  body=$(cat "$SKILL_DIR/finishing.md")
  assert_contains "$body" "Type \`discard\`" "typed confirmation"
  assert_contains "$body" "Run the suites on the merged result" "merged result is tested"
}

test_worktree_setup_checks_before_creating() {
  local body
  body=$(cat "$SKILL_DIR/worktree.md")
  assert_contains "$body" "git rev-parse --git-common-dir" "detects an existing worktree"
  assert_contains "$body" "git check-ignore" "verifies the folder is ignored"
  assert_contains "$body" "EnterWorktree" "prefers the harness tool"
}

test_final_reviewer_names_what_it_set_aside() {
  local body
  body=$(cat "$SKILL_DIR/final-reviewer-prompt.md")
  assert_contains "$body" "Set aside" "declined-to-judge list"
  assert_contains "$body" "Ready to merge" "clear verdict"
  assert_contains "$body" "Do not spawn" "no sub-reviewers"
}
