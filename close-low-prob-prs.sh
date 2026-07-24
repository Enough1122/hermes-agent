#!/usr/bin/env bash
# Close low-probability PRs in NousResearch/hermes-agent
# Requires: gh CLI authenticated as Enough1122 with 'repo' scope
set -euo pipefail

REPO=NousResearch/hermes-agent

declare -a PR_COMMENTS=(
  "69362|Closing as superseded by #49568 — that PR includes this exact endpoint change together with auxiliary-vision resolver and routing work."
  "68784|Closing as superseded by upstream redesign of _is_user_authorized_from_message in current main. The pure-config gap this PR addressed is structurally impossible under the new mutually-exclusive allowlist design (group_allow_from for groups vs allow_from for DMs). Thanks to @agent-narya for the two rigorous verification passes."
  "66849|Closing — clean resubmission of closed-unmerged #56124. If reviewers want this landed, please revive #56124 directly to keep one source of truth."
  "69382|Closing — competing design choice with #69348 (always-fresh-page vs bounded-handshake fallback). Deferring to maintainer selection."
  "69347|Closing — competing design choice with #69346 (cumulative per-conversation tally vs consecutive-only counter). Deferring to maintainer selection."
  "67569|Closing — competing design choice with #67550 / #67573 (which non-recording paths disarm continuous mode). Deferring to maintainer selection."
  "67408|Closing — competing design choice with #64344. Deferring to maintainer selection."
  "67398|Closing — competing design choice with #67229 / #57852. Deferring to maintainer selection."
  "70765|Closing — competing design choice with #46584 (stable request ID + dashboard path). Deferring to maintainer selection."
  "66902|Closing — overlapping with the #56642 / #64849 / #29761 cluster. Deferring to maintainer selection of which slice to land."
  "66898|Closing — needs-decision review pending. Deferring to maintainer selection."
)

for entry in "${PR_COMMENTS[@]}"; do
  pr="${entry%%|*}"
  msg="${entry#*|}"
  echo "=== Closing #$pr ==="
  gh pr close "$pr" --repo "$REPO" --comment "$msg"
  echo ""
done

echo "Done. Closed ${#PR_COMMENTS[@]} PRs."
