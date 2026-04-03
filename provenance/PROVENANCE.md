# Provenance — Bitcoin Blockchain Timestamps

This directory contains OpenTimestamps proof files (`.ots`) that anchor
the content of this repository to the Bitcoin blockchain.

## What This Proves

Each `.ots` file is a cryptographic proof that the corresponding document
existed at or before the Bitcoin block timestamp. This proof is:

- **Irrefutable** — anchored to Bitcoin's proof-of-work chain
- **Independently verifiable** — anyone can check without trusting us
- **Permanent** — survives regardless of GitHub, servers, or companies

## Timestamped Documents

| Proof File | Proves |
|---|---|
| `commit_23689f3.ots` | Entire repo state at commit `23689f3` (2026-04-03) |
| `from_agent_teams_to_agent_civilisations.md.ots` | Paper 1 — Mark E. Mala |
| `civilisation_as_innovation_engine.md.ots` | Paper 2 — Mark E. Mala |
| `maslow_machines.md.ots` | Paper 3 — Mark E. Mala |

Paper 4 ("Collective Machine Intelligence") is timestamped in the
[AgentCiv Engine](https://github.com/wonderben-code/agentciv-engine) repo.

## How to Verify

```bash
# Install the client
pip install opentimestamps-client

# Verify a paper (checks against Bitcoin blockchain)
ots verify provenance/maslow_machines.md.ots -f paper/maslow_machines.md

# Verify the full repo state at the tagged commit
echo -n "23689f37d0a97617bf13acbb4fbb1176b4d723e0" > /tmp/hash.txt
ots verify provenance/commit_23689f3.ots -f /tmp/hash.txt
```

## Why This Matters

These proofs establish that the concepts, terms, and research in this
repository — including Collective Machine Intelligence (CMI) and
Computational Organisational Theory (COT) — were authored by Mark E. Mala
and existed at the timestamps proven by the Bitcoin blockchain.
