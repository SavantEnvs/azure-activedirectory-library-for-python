# syntax=docker/dockerfile:1.7
#
# Commit image for azure-activedirectory-library-for-python (adal; pure Python, Atheris), built on
# the org base image (debian + clang + python3 + pip + identities + build-contract ENV).
#
#   DOCKER_BUILDKIT=1 docker build -f mayhem/Dockerfile --build-arg COMMIT=$(git rev-parse HEAD) -t adal-commit:test .

FROM ghcr.io/savantenvs/base:20261023

ARG COMMIT
ARG REPO_URL
ARG SOURCE_DATE_EPOCH
ARG SANITIZER_FLAGS
ARG MAYHEM_JOBS=

# Python packages go to a $HOME-independent, world-readable user base (SPEC §6.2 item 8).
USER root
RUN mkdir -p /opt/toolchains/python && chown 2000:2000 /opt/toolchains/python && chmod 0755 /opt/toolchains/python
ENV PYTHONUSERBASE=/opt/toolchains/python
USER mayhem
WORKDIR /mayhem
COPY --chown=2000:2000 . /mayhem

RUN bash mayhem/build.sh
RUN if [ -f mayhem/test.sh ]; then bash mayhem/test.sh; else echo "no mayhem/test.sh"; fi

LABEL org.opencontainers.image.source="${REPO_URL}" \
      org.opencontainers.image.revision="${COMMIT}" \
      rlenv.tier="commit" \
      rlenv.source_date_epoch="${SOURCE_DATE_EPOCH}" \
      rlenv.user="mayhem"

USER mayhem
WORKDIR /mayhem
