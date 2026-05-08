# Logos Execution Zone Findings

Last updated: 2026-04-13
Inspected repo: `logos-blockchain/logos-execution-zone`
Inspected commit: `7a29b45`
Local inspection path: `/tmp/logos-execution-zone`

## Purpose

This file is the running log for current and future findings about Logos Execution Zone (LEZ), with an emphasis on:

- what is actually present in the repo
- what looks runnable today
- which docs are likely stale or risky
- what to verify next

## Current Findings

### Repo structure and high-level model

- The repo is not just docs. It contains source code for built-in programs, deployment examples, tutorials, wallet tooling, sequencer/indexer components, and integration tests.
- The root README positions LEZ as a programmable blockchain with both public and private state, with privacy handled at the protocol layer via ZK proofs.
- The README explicitly frames the same program as usable in both public and private execution modes.

### Confirmed example/tutorial coverage

- Program deployment example exists at `/tmp/logos-execution-zone/examples/program_deployment/README.md`.
- Token tutorial exists at `/tmp/logos-execution-zone/docs/LEZ testnet v0.1 tutorials/custom-tokens.md`.
- AMM tutorial exists at `/tmp/logos-execution-zone/docs/LEZ testnet v0.1 tutorials/amm.md`.
- Wallet setup tutorial exists at `/tmp/logos-execution-zone/docs/LEZ testnet v0.1 tutorials/wallet-setup.md`.
- Associated token account tutorial exists at `/tmp/logos-execution-zone/docs/LEZ testnet v0.1 tutorials/associated-token-accounts.md`.

### Confirmed program sources

- Token program source exists under `/tmp/logos-execution-zone/programs/token/`.
- AMM program source exists under `/tmp/logos-execution-zone/programs/amm/`.
- Associated token account program source exists under `/tmp/logos-execution-zone/programs/associated_token_account/`.

### Token program findings

- The token program is built in and shared across all tokens. The tutorial explicitly says you do not deploy a new token program per token.
- The token tutorial demonstrates:
  - creating a token definition plus a supply account
  - using either public or private supply accounts
  - sending tokens across privacy boundaries
- The token core instruction surface includes:
  - `Transfer`
  - `NewFungibleDefinition`
  - `NewDefinitionWithMetadata`
  - `InitializeAccount`
  - `Burn`
  - `Mint`
  - `PrintNft`
- The token core also supports both fungible tokens and NFTs via `TokenDefinition` and `TokenHolding`.

### AMM findings

- The AMM tutorial demonstrates:
  - pool creation
  - swaps
  - remove liquidity
  - add liquidity
- The AMM is implemented as a real program under `/tmp/logos-execution-zone/programs/amm/`, not just a tutorial artifact.
- The AMM core instruction surface includes:
  - `NewDefinition`
  - `AddLiquidity`
  - `RemoveLiquidity`
  - `SwapExactInput`
  - `SwapExactOutput`
- The AMM currently does not charge swap fees. The tutorial says LP tokens only represent proportional pool ownership for now, and fee support is planned for future versions.
- The AMM core computes deterministic PDAs for:
  - the pool
  - token vaults
  - the liquidity token definition

### Associated token account findings

- The ATA tutorial is more than a concept note; it includes a concrete deployment and usage flow.
- Unlike the built-in token program, the ATA program must be deployed before use.
- The tutorial references `artifacts/program_methods/associated_token_account.bin`, and that binary is present in the repo.
- ATA addresses are deterministically derived from owner account ID plus token definition ID.
- The ATA tutorial explicitly supports both public and private owners.

### Wallet and user workflow findings

- The wallet tutorial documents these user-facing commands:
  - `wallet auth-transfer`
  - `wallet chain-info`
  - `wallet account`
  - `wallet pinata`
  - `wallet token`
  - `wallet amm`
  - `wallet check-health`
  - `wallet config`
  - `wallet restore-keys`
  - `wallet deploy-program`
- The program deployment example shows a custom-program workflow, not only built-in programs.
- The example programs include several guest binaries under `examples/program_deployment/methods/guest/src/bin/`, including:
  - `hello_world`
  - `hello_world_with_move_function`
  - `hello_world_with_authorization`
  - `simple_tail_call`
  - `tail_call_with_pda`

## Risks and Suspected Drift

- The root README still tells users to go to `logos-blockchain/lssa` for parts of the stack. That looks historically stale and should be treated carefully.
- The README also references `git checkout master; git pull` for the node repo. The current node repo work we inspected is not centered around a `master` workflow, so this is another drift signal.
- The program deployment README links to `lssa` instructions for running the sequencer. That likely needs translation into the current `logos-blockchain` / `logos-blockchain-node` workflow before treating it as a reliable runbook.
- The wallet setup tutorial lists `wallet amm` and `wallet deploy-program`, but not `wallet ata`, while the ATA tutorial assumes `wallet ata` exists. This may be a minor documentation lag rather than a code problem.

## Practical Interpretation

- Marine's examples are real and present in the repo.
- The token and AMM flows are documented as first-class user workflows, not merely internal tests.
- The repo likely contains enough material to learn the execution model and local developer workflow now.
- The biggest operational risk is documentation drift around how to run the backing node + sequencer stack, not the absence of token/AMM code.

## What To Verify Next

- Whether the current wallet binary in this repo still exposes `wallet ata`.
- Whether the program deployment example still works against the current `logos-blockchain` node setup, or only against an older LEZ/LSSA stack.
- Whether the tutorials assume a local sequencer only, or can be used against a shared devnet/testnet environment.
- Whether the AMM and token tutorials have corresponding end-to-end tests that can be run today.
- Whether there is a current workshop path that uses LEZ directly, or if the workshop expects only the base node to be running beforehand.

## Future Findings Log

### 2026-04-13

- Confirmed presence of token, AMM, ATA, and program deployment materials in the repo.
- Confirmed ATA prebuilt program binary exists at `artifacts/program_methods/associated_token_account.bin`.
- Confirmed the main gap is not missing examples, but likely doc/runtime drift between older LEZ/LSSA instructions and the current Logos node workflow.

### 2026-04-14

- Confirmed the base network target moved to Logos Blockchain `0.1.2`.
- Confirmed the release notes for `0.1.2` publish four explicit bootstrap peer multiaddrs.
- Confirmed the public devnet node-data endpoints still return `401 Unauthorized`, so anonymous retrieval of hosted configs remains blocked.
- Practical consequence: joining the testnet is no longer blocked on discovering peers, but LEZ-related runtime docs may still need translation onto the current `0.1.2` node/testnet workflow.
