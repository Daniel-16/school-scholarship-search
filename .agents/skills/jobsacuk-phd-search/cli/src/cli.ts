#!/usr/bin/env bun
/**
 * jobsacuk-phd-search: funded doctoral studentships from jobs.ac.uk.
 *
 * Only the `/search/phd` board is reachable. jobs.ac.uk also carries
 * lectureships, technician posts and administration jobs, and this workspace
 * has no use for any of them - putting the level in the path rather than in
 * a filter parameter means a dropped parameter cannot widen the search into
 * them.
 *
 * Dependency-free: see the DAAD CLI's header for the reasoning.
 */
import { fail } from "./argv.js"
import * as search from "./commands/search.js"
import * as detail from "./commands/detail.js"

const COMMANDS: Record<string, { run: (argv: readonly string[]) => Promise<number> }> = { search, detail }

const USAGE = `jobsacuk-phd-search

  search   find PhD studentships, optionally funded-only
  detail   full record for one studentship

Run a command with --help for its flags.
Doctoral positions only: this CLI cannot reach the general job board.`

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
