# clawbot_mcp

Stdio MCP server exposing the mechanism model.

```
pip install -r clawbot_mcp/requirements.txt
python -m clawbot_mcp.server
```

## Tools

| Tool | Answers |
|---|---|
| `list_robots` | what records exist, and which joints have no limits — those make every derivation answer incomplete |
| `list_actuators` | what drives them, and `capacity_derivable`: whether a continuous torque rating exists at all |
| `describe_robot` | the record verbatim; nothing is resolved |
| `forward_kinematics` | where every link and the tool sit at a pose |
| `reach` | sampled reachability, with sample count and seed |
| `hold` | static gravity load per joint, labelled an upper bound |
| `can_it` | the affordance verdict — four answers, none of them an unqualified yes |
| `bill_of_parts` | the parts list in OpenBuildCore's vocabulary |
| `export_urdf` | URDF, or the joints that make it inexpressible |
| `validate` | every rule, read-only |

## Two things about this surface

**Everything executes; nothing proposes.** OpenDesignCore ADR-0009 splits MCP tools into reads
and deterministic runs that execute, and effects reaching a fabricator that only propose.
ClawBot's propose side is **empty** — not unused, empty. It has no side effects by construction:
ADR-0010 put every actuating loop behind Oh-Ben-Claw's Track 0, and `data/` is edited by people.
Nothing can be added to the propose side without first reversing an ADR.

**No tool takes a filesystem path.** `urdf.py import` reads a file you name, and exposed here
that would be an arbitrary file read wearing a domain-specific name. It stays on the CLI. A
tool taking URDF *text* is a different thing and may be added if the need is real.

## The caveats are the answer

Every tool returns its whole verdict object. A tool returning a bare boolean or a bare distance
would strip the assumptions that ADR-0003, ADR-0004, ADR-0013 and ADR-0015 each require to
travel *inside* the value — the tool offset, the base frame, the sample count and seed, the
"joint-limit result, not a collision result" warning, the "static upper bound" label.

That matters more over MCP than on a CLI, because a tool result is usually summarised by a model
before a human reads it, and a stripped caveat is exactly what a summary drops. If you are
building on this surface, carry the caveats through.

## Sample counts are clamped, and the clamp is reported

`reach` and `can_it` cap `samples` at 200,000. A large enough N is a denial of service against
the process, and silently honouring it is as bad as silently refusing it — so a clamped request
comes back with a `clamped` field saying what was asked for and what was actually run.
