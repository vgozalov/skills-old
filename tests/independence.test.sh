# shellcheck shell=bash
# Pins that nothing shipped here needs the superpowers plugin, and that our skills
# never share a description with one of its skills (identical descriptions made agents
# pick the plugin's skill instead of ours).

test_no_skill_or_agent_hands_off_to_superpowers() {
  local hits
  hits=$(grep -rn 'superpowers:' "$REPO_ROOT/skills" "$REPO_ROOT/agents" || true)
  [ -z "$hits" ] || fail "superpowers hand-offs remain:
$hits"
}

test_descriptions_are_our_own() {
  local file desc
  for file in "$REPO_ROOT"/skills/*/SKILL.md; do
    desc=$(grep -m1 '^description:' "$file")
    assert_not_contains "$desc" "Use when executing implementation plans with independent tasks in the current session" "$file"
    assert_not_contains "$desc" "Use when you have a spec or requirements for a multi-step task, before touching code" "$file"
  done
}

test_build_workspaces_live_under_parallel_build() {
  local out
  git init -q -b main repo && mkdir -p repo/docs/plans && : > repo/docs/plans/feature.md
  out=$(cd repo && bash "$REPO_ROOT/skills/parallel-build/scripts/sdd-workspace" docs/plans/feature.md)
  assert_contains "$out" "/.parallel-build/feature" "default workspace"
}

test_an_in_flight_legacy_workspace_is_kept() {
  local out
  git init -q -b main repo && mkdir -p repo/docs/plans repo/.superpowers/sdd/feature && : > repo/docs/plans/feature.md
  printf 'docs/plans/feature.md\n' > repo/.superpowers/sdd/feature/plan-path
  out=$(cd repo && bash "$REPO_ROOT/skills/parallel-build/scripts/sdd-workspace" docs/plans/feature.md)
  assert_contains "$out" "/.superpowers/sdd/feature" "legacy workspace resumes"
}

test_the_final_reviewer_prompt_ships_with_the_build_skill() {
  [ -f "$REPO_ROOT/skills/parallel-build/final-reviewer-prompt.md" ] || fail "final-reviewer-prompt.md missing"
  assert_contains "$(cat "$REPO_ROOT/skills/parallel-build/SKILL.md")" "./final-reviewer-prompt.md" "linked from the skill"
}
