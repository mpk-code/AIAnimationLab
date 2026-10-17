# Glossary Entry Structure

Reference for the `grill` skill: the shape of a **proposed** glossary entry in a session file's
technical handoff. The live glossary is `docs/glossary.md` (created in M0; until then, the Glossary
table in `docs/project-definition.md`). Read the live glossary first and match its form — if it is
a `Term | Meaning` table, propose table rows and carry the extra fields below as notes beneath them.
Grill never edits the live glossary; a glossary change needs an ADR.

## Fields per proposed entry

```markdown
#### <Canonical Term>  — new | changed | renamed from "<old term>"

- **Meaning:** <One or two plain sentences, in the register of the existing glossary ("One
  continuous camera take, the unit of staging and rendering"). No paths, field names or ADR
  numbers.>
- **Avoid aliases:** <Near-synonyms that have come up; for each, whether it funnels to this term or
  the distinction matters. Omit the field when there are none.>
- **Where it appears:** <Plain area names — "the story stages", "the style bible", "the render
  loop", "the experiments".>
- **Authorized by:** <The draft ADR in this session that makes the change, by proposed file name.>
- **References:** <Internal back-links for the downstream agent: project-definition sections,
  ADRs, schemas, stage skills. Never read aloud in the interview.>
```

Append **(provisional)** to the heading when the meaning is still ambiguous and should be firmed up
the next time the term comes up.

## What does not belong in an entry

- Implementation detail (module names, `bpy` calls, schema field names) beyond References.
- Long history — cite the ADR instead.
- Run-level ephemera — status reports, fix docs, production IDs.

## Voice

- Plain prose, short sentences, no hedging. Either the entry defines the term or it is provisional —
  say which.
- Capitalization follows the existing glossary (sentence-case terms: "Style bible", "Anti-default").
- Use the term exactly as the glossary does everywhere else in the entry.
