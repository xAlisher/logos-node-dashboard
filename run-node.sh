#!/usr/bin/env bash
set -euo pipefail

cd /home/alisher/logos-blockchain-runbook

export LOGOS_BLOCKCHAIN_CIRCUITS=/home/alisher/logos-blockchain-runbook/artifacts/circuits/logos-blockchain-circuits-v0.4.2-linux-x86_64

exec /home/alisher/logos-blockchain-runbook/artifacts/node/logos-blockchain-node \
  /home/alisher/logos-blockchain-runbook/configs/live/node.yaml
