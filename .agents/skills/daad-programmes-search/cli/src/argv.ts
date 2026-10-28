/**
 * A tiny argv parser with one rule the portal CLIs cannot do without: an
 * unrecognised flag is an error, never a silent discard.
 *
 * That rule is the whole reason this file exists instead of a framework. A
 * discarded filter does not fail - it returns a *different, larger* result
 * set that looks exactly like a successful search, so `--lvl masters` on a
 * CLI whose flag is `--level` would quietly return every programme in
 * Germany, and the only symptom would be a shortlist that made no sense a
 * week later.
 *
 * The same reasoning covers the second rule: a declared option that is
 * present with no value (`--level --limit 5`) is an error rather than a
 * fall-through to the default, because the default is not what was asked for.
 */

export interface OptionSpec {
  readonly type: "string" | "number" | "boolean"
  readonly short?: string
  readonly description: string
  readonly choices?: readonly string[]
  readonly repeatable?: boolean
  readonly default?: string | number | boolean
}

export type OptionMap = Record<string, OptionSpec>
export type Flags = Record<string, string | number | boolean | string[] | undefined>

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

export function fail(error: string, code: string): never {
  writeError(error, code)
  process.exit(1)
}

/** Render `--name <type>` help lines, so --help never drifts from the spec. */
export function renderHelp(command: string, options: OptionMap): string {
  const lines = [`Usage: ${command} [flags]`, ""]
  for (const [name, spec] of Object.entries(options)) {
    const short = spec.short ? `-${spec.short}, ` : "    "
    const value = spec.type === "boolean" ? "" : ` <${spec.type}>`
    const choices = spec.choices ? ` (${spec.choices.join("|")})` : ""
    const dflt = spec.default !== undefined ? ` [default: ${String(spec.default)}]` : ""
    lines.push(`  ${short}--${name}${value}`.padEnd(34) + spec.description + choices + dflt)
  }
  return lines.join("\n")
}

export function parse(argv: readonly string[], options: OptionMap): Flags {
  const byShort = new Map<string, string>()
  for (const [name, spec] of Object.entries(options)) {
    if (spec.short) byShort.set(spec.short, name)
  }

  const flags: Flags = {}
  for (const [name, spec] of Object.entries(options)) {
    if (spec.default !== undefined) flags[name] = spec.default
  }

  const resolve = (token: string): { name: string; rendered: string } => {
    const rendered = token.split("=")[0] ?? token
    const bare = rendered.replace(/^--?/, "")
    const name = token.startsWith("--") ? bare : byShort.get(bare)
    if (!name || !(name in options)) {
      fail(
        `unknown flag ${rendered} - flags are never silently ignored, because a discarded ` +
          `filter changes what the search returns; see --help for the supported flags`,
        "UNKNOWN_FLAG",
      )
    }
    return { name, rendered }
  }

  for (let i = 0; i < argv.length; i++) {
    const token = argv[i]
    if (token === undefined || token === "--") break
    if (!token.startsWith("-") || token === "-") {
      fail(`unexpected positional argument "${token}"`, "BAD_ARG")
    }
    const { name, rendered } = resolve(token)
    const spec = options[name]!

    if (spec.type === "boolean") {
      if (token.includes("=")) {
        const value = token.slice(token.indexOf("=") + 1).toLowerCase()
        if (value !== "true" && value !== "false") {
          fail(`${rendered} takes true or false, got ${value}`, "BAD_ARG")
        }
        flags[name] = value === "true"
      } else {
        flags[name] = true
      }
      continue
    }

    let raw: string
    if (token.includes("=")) {
      raw = token.slice(token.indexOf("=") + 1)
    } else {
      const next = argv[i + 1]
      // A value that must begin with "-" uses --flag=value. Consuming a
      // dash-led token here would swallow the next flag and silently drop
      // this one's value, which is the failure the whole module is about.
      if (next === undefined || (next.startsWith("-") && next !== "-")) {
        fail(`option ${rendered} requires a value`, "BAD_ARG")
      }
      raw = next
      i++
    }

    if (spec.choices && !spec.choices.includes(raw)) {
      fail(`${rendered}: expected one of ${spec.choices.join(", ")}, got ${raw}`, "BAD_ARG")
    }
    if (spec.type === "number") {
      const parsed = Number(raw)
      if (!Number.isFinite(parsed)) fail(`${rendered}: expected a number, got ${raw}`, "BAD_ARG")
      flags[name] = parsed
      continue
    }
    if (spec.repeatable) {
      const previous = flags[name]
      flags[name] = Array.isArray(previous) ? [...previous, raw] : [raw]
      continue
    }
    flags[name] = raw
  }
  return flags
}
