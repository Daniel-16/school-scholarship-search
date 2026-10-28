#!/usr/bin/env bun
/**
 * scholarship-feeds-search: master's and doctoral funding calls, aggregated
 * from the scholarship announcement feeds applicants from Africa actually
 * read.
 *
 * The important property of this CLI is what it refuses to claim. Every row
 * it emits carries `requires_verification: true`, because every row is a
 * third party's republication of somebody else's call - frequently stale,
 * occasionally wrong about eligibility, and sometimes a scam reprint. The
 * rows are leads for /discover's gate to examine, never shortlist entries.
 *
 * Undergraduate announcements are detected in order to be dropped; they are
 * the bulk of these feeds and none of this workspace's business.
 *
 * Dependency-free: see the DAAD CLI's header for the reasoning.
 */
import { fail } from "./argv.js"
import * as search from "./commands/search.js"
import * as sources from "./commands/sources.js"

const COMMANDS: Record<string, { run: (argv: readonly string[]) => Promise<number> }> = { search, sources }

const USAGE = `scholarship-feeds-search

  search    master's and doctoral funding calls across the aggregator feeds
  sources   list the feeds and what each is good for

Run a command with --help for its flags.
Every result is UNVERIFIED: confirm on the funder's own site before applying.`

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
