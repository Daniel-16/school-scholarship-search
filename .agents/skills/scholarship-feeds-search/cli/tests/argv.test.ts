import { describe, expect, test, spyOn } from "bun:test"
import { parse, type OptionMap } from "../src/argv.js"

const OPTIONS: OptionMap = {
  level: { type: "string", short: "l", description: "", choices: ["masters", "phd"], default: "masters" },
  query: { type: "string", short: "q", description: "" },
  subject: { type: "string", description: "", repeatable: true },
  "tuition-free": { type: "boolean", description: "" },
  limit: { type: "number", description: "", default: 25 },
}

/** parse() exits the process on a bad flag, so the exit has to be trapped. */
function expectExit(argv: string[]): { code: string; error: string } {
  const errors: string[] = []
  const stderr = spyOn(process.stderr, "write").mockImplementation(((chunk: string) => {
    errors.push(String(chunk))
    return true
  }) as never)
  const exit = spyOn(process, "exit").mockImplementation((() => {
    throw new Error("__exit__")
  }) as never)
  try {
    parse(argv, OPTIONS)
    throw new Error("expected parse() to exit")
  } catch (error) {
    if ((error as Error).message !== "__exit__") throw error
  } finally {
    stderr.mockRestore()
    exit.mockRestore()
  }
  return JSON.parse(errors.join(""))
}

describe("parse", () => {
  test("applies declared defaults", () => {
    expect(parse([], OPTIONS)).toMatchObject({ level: "masters", limit: 25 })
  })

  test("reads long flags, short flags and = form", () => {
    expect(parse(["--query", "robotics"], OPTIONS).query).toBe("robotics")
    expect(parse(["-q", "robotics"], OPTIONS).query).toBe("robotics")
    expect(parse(["--query=robotics"], OPTIONS).query).toBe("robotics")
  })

  test("collects a repeatable flag", () => {
    expect(parse(["--subject", "4", "--subject", "12"], OPTIONS).subject).toEqual(["4", "12"])
  })

  test("coerces a number", () => {
    expect(parse(["--limit", "5"], OPTIONS).limit).toBe(5)
  })

  // The reason this module exists: a discarded filter silently widens the
  // result set instead of failing, so every one of these must be an error.
  test("rejects an unknown long flag", () => {
    expect(expectExit(["--lvl", "masters"]).code).toBe("UNKNOWN_FLAG")
  })

  test("rejects an unknown short flag", () => {
    expect(expectExit(["-x", "1"]).code).toBe("UNKNOWN_FLAG")
  })

  test("rejects a known option with no value", () => {
    expect(expectExit(["--query"]).code).toBe("BAD_ARG")
  })

  test("rejects a known option followed by another flag", () => {
    expect(expectExit(["--query", "--limit", "5"]).code).toBe("BAD_ARG")
  })

  test("rejects a value outside the declared choices", () => {
    const result = expectExit(["--level", "bachelors"])
    expect(result.code).toBe("BAD_ARG")
    expect(result.error).toContain("masters, phd")
  })

  test("rejects a non-numeric number", () => {
    expect(expectExit(["--limit", "many"]).code).toBe("BAD_ARG")
  })

  test("rejects a positional argument", () => {
    expect(expectExit(["robotics"]).code).toBe("BAD_ARG")
  })

  test("a boolean flag needs no value", () => {
    expect(parse(["--tuition-free", "--limit", "3"], OPTIONS)).toMatchObject({
      "tuition-free": true,
      limit: 3,
    })
  })
})
