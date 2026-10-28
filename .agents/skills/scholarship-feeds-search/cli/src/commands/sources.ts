import { parse, renderHelp, type OptionMap } from "../argv.js"
import { SOURCES } from "../sources.js"

export const OPTIONS: OptionMap = {
  format: { type: "string", short: "f", description: "Output format", choices: ["json", "table"], default: "table" },
  help: { type: "boolean", short: "h", description: "Show this help" },
}

export async function run(argv: readonly string[]): Promise<number> {
  const flags = parse(argv, OPTIONS)
  if (flags["help"]) {
    process.stdout.write(renderHelp("scholarship-feeds sources", OPTIONS) + "\n")
    return 0
  }
  if (flags["format"] === "json") {
    process.stdout.write(JSON.stringify(SOURCES, null, 2) + "\n")
    return 0
  }
  for (const source of SOURCES) {
    process.stdout.write(`${source.id}\n  ${source.name} - ${source.base}\n  ${source.note}\n\n`)
  }
  process.stdout.write(
    "These are announcement aggregators, not funders. Treat every item as unverified\n" +
    "until the funder's own page confirms the award, the eligibility and the deadline.\n",
  )
  return 0
}
