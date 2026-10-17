---
name: defect-filing
description: >
  File a defect: record a bug as a GitHub issue labelled bug on mpk-code/AIAnimationLab, without
  fixing it. Use for "file a defect", "log a bug", "open an issue for this", "this is out of
  scope — record it", "record this bug for later", "raise a ticket", "I found an unrelated bug
  while fixing X; record it", or any defect found during other work (a fix, a code review, a
  planned run, an overseer sweep, a render that misbehaves) that is not being fixed now. Use this
  skill rather than an ad-hoc `gh issue create`, so the issue has the standard sections and is
  recorded where it came from. To fix the defect now instead, use /bug-fix.
---

# Skill: File a Defect

Filing a defect is one action with one result: a GitHub issue in `mpk-code/AIAnimationLab` with the
label `bug`, written in the sections below, and named as `issue #<n>` in the record the defect came
from.

Filing records the defect; it does not diagnose or fix it. The root cause is established later, by
`/bug-fix`, in a fix document under `docs/plans/fixes/`.

## When to use it, and when not

- **Use it** for a defect you are not going to fix in the current piece of work: one found while
  fixing a different defect, one a code review drops as pre-existing, one a planned run meets
  outside its scope, one a worker hands back to an overseer.
- **Do not use it** to fix the defect now. That is `/bug-fix`, which can start from an issue this
  skill filed.
- **A wrong record is a defect too** (a stale docstring, a doc or schema sentence that misstates
  the code). Left unfixed, it is filed here like any other defect. Fixed now, it is `/bug-fix`.
- **Check it is not already filed** before writing anything. Search open and closed issues for two
  or three key words of the behaviour you saw, not the words of your title:
  `gh issue list --repo mpk-code/AIAnimationLab --label bug --state all --search "<two or three words>"`.
  Judge a match by what the issue describes, not by its title. If it is the same defect, add what
  you observed to that issue as a comment and stop.

## Step 1. Write the observation, and keep the hypothesis apart

The issue body has these sections, in this order:

| Section | Required | What goes in it |
|---|---|---|
| Title | yes | The behaviour, in a short line. Not the suspected cause. |
| **What I did** | yes | The exact command (harness invocation, test, script), copied. Steps only. |
| **Expected** | yes | What you expected, stated so someone could check it. |
| **Actual** | yes | What happened, as it appeared in the output or the frames: "frames 12–48 are black in the preview contact sheet", not "lighting is broken". |
| **Logs** | no | The exact error output, verbatim. No summarizing, no reformatting. |
| **Environment** | no | Machine (M5 Max / M1), Blender version, render profile and engine, commit SHA, seed; or the path to the run's `manifest.json`. |
| **Frequency** | yes | Exactly one of `Every time`, `Sometimes`, `Saw it once`. Nondeterministic output is itself worth noting here. |
| **Initial hypothesis** | no | See below. |

The first seven take **observations only**. No guessed cause, no proposed fix and no analysis goes
in them. A common mistake is putting the observation in Expected, or a conclusion ("sorting
doesn't work") where the visible symptom belongs.

**The Initial hypothesis** is the one place a suspected cause belongs: what you suspect, what you
ruled out and how you checked, and the quest or run the defect came from. A partial answer is fine.
It is treated as something to test, not as the diagnosis. It is mainly an agent's place to keep
what it learned while debugging, which is lost when the session ends; write it when you have it. If
you learn more after filing, add an issue comment that begins `Initial hypothesis:`.

Do not paste renders or other large binaries into the issue; point at the manifest or the output
directory instead.

## Step 2. Draft, confirm, then file

Write the body to a scratch file in your session scratchpad (outside the repository). Read it back
against Step 1. Then **show the user the title and body and confirm before creating the issue** —
filing is a write to GitHub.

```bash
gh issue create --repo mpk-code/AIAnimationLab --label bug \
  --title "<title>" --body-file <scratchpad>/defect-body.md
```

The command prints the issue URL. If it fails, nothing was created: read the message, fix the
cause, and run it again. If it times out, run the duplicate search from above before filing again —
the issue may exist.

## Step 3. Set nothing else

Apply no label but `bug`, and no assignee or milestone. Priority and scheduling are the user's call.
If you have a view on priority, suggest it in a comment:

```bash
gh issue comment <n> --repo mpk-code/AIAnimationLab --body "Suggested priority: P2. <one-line reason>"
```

## Step 4. Record where it went

Name the filed defect as `issue #<n>` in whatever record you are working in: a run's status report
(`sidequests/<slug>/status/run<N.M>status.md`, Open Issues), a fix plan (`## Deferred Work`), or a
return block. Never write `fix`, `close` or `resolve`, or any of their forms, before `#<n>`: GitHub
closes the issue when such a phrase reaches `main` in a commit message.

Use a list item that begins `issue #<n>:`, followed by a short description. An item that is not a
defect begins `not a defect: <reason>` instead. In a fix plan's `### Source review findings
addressed` the status reads `deferred: issue #<n>:` or `deferred: not a defect: <reason>`. A section
with nothing to defer reads `None.`. The forms are lower case and the colon is part of each.

## Under an overseer

A worker window whose dispatch withholds GitHub writes does not file. It writes the body file and
puts its path in its return block. The overseer reviews the body and files it. A draft left in a
return block is filed by nobody, so the overseer looks for one in every return.

## Checklist

- [ ] Searched for an existing issue first.
- [ ] Observation sections hold observations only; any suspected cause is in Initial hypothesis.
- [ ] Environment names machine, Blender version and seed (or the manifest path).
- [ ] User confirmed the draft before `gh issue create`.
- [ ] Only the `bug` label set; a priority view, if any, is a comment.
- [ ] The issue is named as `issue #<n>` in the record the defect came from.
