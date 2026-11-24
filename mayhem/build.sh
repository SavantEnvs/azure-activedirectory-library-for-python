#!/usr/bin/env bash
#
# mayhem/build.sh — build the adal (azure-activedirectory-library-for-python) Atheris targets.
#
# Runs in the commit image (mayhem/Dockerfile) as `mayhem` in /mayhem. adal is pure Python, so the
# fuzzed code is instrumented by Atheris at import time (atheris.instrument_imports), not by clang;
# SANITIZER_FLAGS has no compiled project to apply to. Mayhem needs an ELF target, so each harness
# gets a tiny clang-built launcher (mayhem/launcher.c) that execs python3 on it, forwarding the
# libFuzzer arguments; the same ELF replays a single input file, so it is also the reproducer.
#
# Air-gapped (SPEC §6.5): the first (online) run fills mayhem/wheelhouse with the adal wheel built
# from this tree, its runtime deps, atheris and the test-only deps (httpretty, six); every run,
# including the offline PATCH re-run, installs from it with --no-index. The adal wheel is rebuilt
# from the (possibly patched) tree on every run with --no-build-isolation, so a patch takes effect.
set -euo pipefail

[ -n "${SOURCE_DATE_EPOCH:-}" ] || unset SOURCE_DATE_EPOCH

: "${SANITIZER_FLAGS=-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer}"
: "${DEBUG_FLAGS:=-g -gdwarf-3}"
: "${CC:=clang}"
: "${SRC:=/mayhem}"
: "${MAYHEM_JOBS:=$(nproc)}"
: "${PYTHONUSERBASE:=/opt/toolchains/python}"
export SANITIZER_FLAGS DEBUG_FLAGS CC SRC MAYHEM_JOBS PYTHONUSERBASE

cd "$SRC"
H="$SRC/mayhem"
WHEELHOUSE="$H/wheelhouse"
PIP="python3 -m pip"
DEPS="atheris==3.1.0 PyJWT==2.10.1 requests==2.32.3 python-dateutil==2.9.0.post0 cryptography==44.0.2 httpretty==1.1.4 six==1.17.0 setuptools wheel"

# 1) Wheelhouse (online, once). The marker is not a dotfile and the directory is not gitignored, so
#    `git clean -ffdX` leaves it in place for the offline graded rebuild.
mkdir -p "$WHEELHOUSE"
if [ ! -f "$WHEELHOUSE/POPULATED" ]; then
  # shellcheck disable=SC2086
  $PIP wheel --wheel-dir "$WHEELHOUSE" $DEPS
  touch "$WHEELHOUSE/POPULATED"
fi
# shellcheck disable=SC2086
$PIP install --no-index --find-links "$WHEELHOUSE" --user --break-system-packages $DEPS

# 2) adal itself from this tree (offline; reinstalled every run so an edited tree is what runs).
rm -rf "$SRC/build" "$SRC/adal.egg-info"
$PIP install --no-index --find-links "$WHEELHOUSE" --no-build-isolation --no-deps \
  --force-reinstall --user --break-system-packages "$SRC"
rm -rf "$SRC/build" "$SRC/adal.egg-info"

# 3) ELF launchers: one per harness (fuzz target + reproducer), plus the oracle launcher. They are
#    exec shims, built with DEBUG_FLAGS (DWARF 3) but without SANITIZER_FLAGS (an ASan runtime in
#    the shim would only be inherited by the python child).
for h in fuzz_util fuzz_xmlutil fuzz_wstrust_response fuzz_mex fuzz_token_response \
         fuzz_user_realm fuzz_auth_challenge fuzz_token_cache; do
  $CC $DEBUG_FLAGS -O1 -DSCRIPT_PATH="\"$H/$h.py\"" "$H/launcher.c" -o "$SRC/$h"
  cp -f "$SRC/$h" "$SRC/$h-standalone"
done
$CC $DEBUG_FLAGS -O1 -DORACLE_PATH="\"$H/oracle.py\"" "$H/oracle_launch.c" -o "$SRC/adal_oracle"

# 4) Fail early if the harnessed API drifted.
python3 -c "import atheris, httpretty, adal; from adal.mex import Mex; from adal.wstrust_response import WSTrustResponse; from adal.user_realm import UserRealm; from adal.oauth2_client import OAuth2Client; from adal.token_cache import TokenCache"

echo ">> build.sh done"
