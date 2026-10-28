#!/usr/bin/env bun
/**
 * daad-programmes-search: master's and doctoral programmes in Germany from
 * the DAAD "International Programmes in Germany" database.
 *
 * Dependency-free on purpose. A portal CLI that every fork executes is the
 * riskiest code in this workspace (see tools/security_guards.py), and the
 * three things a framework was providing here - argument parsing, schema
 * validation and HTML walking - are each a few dozen lines against one
 * known API. Nothing to install also means nothing to install *offline*.
 */
import { fail } from "./argv.js"
import * as search from "./commands/search.js"
import * as detail from "./commands/detail.js"

const COMMANDS: Record<string, { run: (argv: readonly string[]) => Promise<number> }> = {
  search,
  detail,
}

const USAGE = `daad-programmes-search

  search   find master's or doctoral programmes in Germany
  detail   full record for one programme

Run a command with --help for its flags.
Master's and doctoral study only: this CLI has no undergraduate level.`

const [command, ...rest] = process.argv.slice(2)

if (!command || command === "--help" || command === "-h" || command === "help") {
  process.stdout.write(USAGE + "\n")
  process.exit(0)
}
if (command === "--version" || command === "-v") {
  process.stdout.write("1.0.0\n")
  process.exit(0)
}

const selected = COMMANDS[command]
if (!selected) {
  fail(`unknown command "${command}" - expected one of ${Object.keys(COMMANDS).join(", ")}`, "UNKNOWN_COMMAND")
}

process.exit(await selected.run(rest))
