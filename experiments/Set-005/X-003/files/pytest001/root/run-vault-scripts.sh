#!/bin/sh

export VAULT_TOKEN="$1"
export VAULT_ADDR="http://127.0.0.1:8200/"

run-parts --new-session --exit-on-error /etc/vault/deploy-secrets
