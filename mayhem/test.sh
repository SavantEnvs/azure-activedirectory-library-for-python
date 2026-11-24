#!/usr/bin/env bash
#
# mayhem/test.sh — RUN adal's functional suite that mayhem/build.sh installed (never builds).
#
# Runs upstream's unittest suite (tests/, HTTP mocked by httpretty) plus known-answer checks of the
# fuzzed parsers through /mayhem/adal_oracle, an ELF launcher under /mayhem (so the sabotage check
# can neuter it), and reports the counts as CTRF. A no-op program prints no ORACLE_RESULT and fails.
set -uo pipefail
[ -n "${SOURCE_DATE_EPOCH:-}" ] || unset SOURCE_DATE_EPOCH
: "${SRC:=/mayhem}"
cd "$SRC"
ORACLE="$SRC/adal_oracle"

emit_ctrf() {
  local tool="$1" passed="$2" failed="$3" skipped="${4:-0}" pending="${5:-0}" other="${6:-0}"
  local tests=$(( passed + failed + skipped + pending + other ))
  cat > "${CTRF_REPORT:-$SRC/ctrf-report.json}" <<JSON
{
  "results": {
    "tool": { "name": "$tool" },
    "summary": {
      "tests": $tests,
      "passed": $passed,
      "failed": $failed,
      "pending": $pending,
      "skipped": $skipped,
      "other": $other
    }
  }
}
JSON
  printf 'CTRF {"results":{"tool":{"name":"%s"},"summary":{"tests":%d,"passed":%d,"failed":%d,"pending":%d,"skipped":%d,"other":%d}}}\n' \
    "$tool" "$tests" "$passed" "$failed" "$pending" "$skipped" "$other"
  [ "$failed" -eq 0 ]
}
if [ ! -x "$ORACLE" ]; then
  echo "FAIL: $ORACLE missing — mayhem/build.sh did not build it" >&2
  emit_ctrf unittest 0 1
  exit 1
fi

out="$("$ORACLE" 2>&1)"; rc=$?
echo "$out"
line="$(printf '%s\n' "$out" | grep -E '^ORACLE_RESULT passed=[0-9]+ failed=[0-9]+ skipped=[0-9]+$' | tail -1)"
if [ "$rc" -ne 0 ] || [ -z "$line" ]; then
  echo "FAIL: adal oracle produced no result (rc=$rc)" >&2
  emit_ctrf unittest 0 1
  exit 1
fi
passed="$(sed -E 's/.*passed=([0-9]+).*/\1/' <<<"$line")"
failed="$(sed -E 's/.*failed=([0-9]+).*/\1/' <<<"$line")"
skipped="$(sed -E 's/.*skipped=([0-9]+).*/\1/' <<<"$line")"
if [ "$passed" -eq 0 ]; then failed=$((failed + 1)); fi
emit_ctrf unittest "$passed" "$failed" "$skipped"
