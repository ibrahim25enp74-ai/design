---
name: taste
description: Method for tasteful, non-generic, non-repetitive design in architecture and social media that learns the user's preferences over time. Use for any architecture task (concept, massing, facade, plan, section, CAD/DXF drawings, A3/A1 sheet layout, presentation boards, diagrams, renders) and any social media task (posts, carousels, stories, reel covers, ads, captions, a feed or campaign series), when the user asks for something tasteful, not generic, not repetitive, or for a design critique, and when the user reacts to a design (likes, dislikes, edits) so the preference gets recorded. Arabic triggers - تصميم معماري، واجهة، مخطط، مقطع، شيتات، لوحات، إخراج، رندر، بوست، منشور، سوشيال ميديا، انستغرام، إعلان، كاروسيل، ستوري، بذوق، مو جنريك، بدون تكرار، عجبني، ما عجبني، غيّره.
---

# Taste

A design looks generic when every decision is the default: the first idea, the familiar palette, the template layout, the stock phrase. Here taste means two things. Every visible decision traces back to something true about *this* project, or to something the user has told you they like. And the set of decisions is small and holds together. This file is a method, not a mood board. Follow the steps in order.

The files next to this one:

- `preferences.md`: the user's own taste, learned from their feedback. **Read it first, every time.** It overrides everything else here.
- `projects.md`: the facts for each of the user's projects (site, program, concept threads). Read the project's section in step 1.
- `architecture.md`: concept, facades, plans, CAD drawings, sheet sets, boards, renders.
- `social.md`: posts, carousels, stories, feed series, captions.
- `arabic-type.md`: any Arabic text in either domain (fonts, RTL, shaping, numerals).
- `design-log.md`: the record of past designs. Read it before you start and add to it after (this prevents repetition).

## Where the taste comes from

When two sources conflict, the one higher in this list wins:

1. **The user's preferences** in `preferences.md`, plus anything they say in the current conversation.
2. **A brand guide or house style** for the client, when one exists.
3. **The project's own facts**: site, climate, brief, audience, materials (step 1).
4. **References** the user has given or approved (listed in `preferences.md`).
5. **Craft conventions** in the domain files: drawing standards, typography rules, platform specs.
6. **The anti-generic method**: killing the first idea, the swap test, the log.

Sources 5 and 6 recognise the generic and keep the work competent. The personal part of the taste comes from source 1, which is why step 8 keeps learning it.

## 0. Read the preferences

Read `preferences.md`. Apply the firm preferences that match the task's scope (global, domain or client). Treat tentative ones as a lean, not a rule.

## 1. Find the specific

Before choosing any form, colour or font, read the project's section in `projects.md`, then write down 3–5 facts that belong only to this project. Sources: the site, the climate, the brief or program, the client or brand, the audience, the materials, local history, a hard constraint (budget, plot shape, regulation), the actual product or service.

Every major decision (concept, form, palette, typeface, image, headline) has to point to at least one of these facts. When information is missing, ask once or state the assumption you made. Don't fill the gap with a generic default.

## 2. Kill the first idea

The first idea that comes to mind is the one everyone has. Write three directions, one line each:

- **A**: the obvious one. Write it down so you can name it and avoid it.
- **B** and **C**: two directions that come from different facts on the list.

Develop B or C. Use A only if you can say why the obvious answer really is right here, and then execute it with more precision than anyone else would.

## 3. Set a small system

Set the constraints before you compose:

- **Type**: one family, or two at most (one display, one text).
- **Colour**: one dominant neutral and one secondary colour, plus an accent on at most about 10% of the area. Take the colours from the project's materials, place or brand, never from trend palettes.
- **Grid**: one grid or module per series. Make the margins wider than feels necessary.
- **Signature move**: one recognisable device repeated across the series (a crop, a rule line, a colour band, a corner mark, a drawing style). Use only one.
- **Scale contrast**: each composition gets one dominant element, clearly bigger than everything else.

Restraint does not mean emptiness. All-white minimalism is its own cliché. A bold, colourful or dense design can be tasteful when its system holds together and each decision can be traced to a fact.

## 4. Check the log for repetition

Read the last 10 entries of `design-log.md`.

- **New project or campaign**: differ from every recent entry in concept, and in at least two of palette, type, layout archetype and signature move.
- **Same series** (the next post in a feed, the next sheet in a set): keep the system and change the composition. No two consecutive pieces may share a layout archetype or put the dominant element in the same position.
- **Within one piece**: don't use the same visual idea twice, for example two gradients, two badges, or three icons doing the same job.

## 5. Make it, then subtract

After the first version, remove one element and see whether the piece improves. It usually does. Repeat until removing anything hurts. Decoration that carries neither information nor the concept goes.

## 6. Critique before delivering

Run these tests. Fix whatever fails instead of only reporting it.

- **Swap test**: if the design could go on another project or brand with only the name changed, it is generic. Go back to step 1.
- **Squint test**: with the eyes half closed there should be exactly one element that reads first, then a clear second read.
- **Sentence test**: the idea fits in one sentence without the words in the list below.
- **Tells test**: none of the generic tells listed in the domain files appear.
- **Real-size test**: check at actual output size. A3 sheets plotted at 100%, posts at phone size (about a third of the screen in the feed).
- **Repetition test**: compare against the latest entries in the log.

## 7. Log it

Add one row to `design-log.md` (the format is in that file) for each piece or series you deliver.

## 8. Learn from the reaction

The user's reaction to a design is the most valuable input this skill gets. Whenever it is clear, record it in `preferences.md` using the rules in that file. Clear reactions include:

- A statement: "عجبني", "ما عجبني", "حلو", "غيّره", "too busy", "I like this one".
- A choice: when you showed directions B and C and they picked one.
- An edit: they changed a colour, font, layout or wording in something you delivered. Look at what they changed.
- A reference: they shared an image, account, building or designer they like or dislike, either in the chat or saved in `references/` next to this file. Look at it and pull out 3–5 concrete traits (palette as hex, type style, composition, light, density). Confirm them with the user in one line, then record them under References. Record a trait only after they confirm it, never just the name of the reference.

When a direction is a genuine matter of taste, show two directions in one line each and let the user pick. Every pick teaches the skill something. Ask at most one taste question per delivery, never a questionnaire.

When a preference has become firm and contradicts a default in one of these files, edit that default so the skill itself changes, and note the change in the history at the bottom of `preferences.md`.

These files are the skill's memory, and they only persist if committed. Include changes to `preferences.md`, `design-log.md` or the skill files in the same commit as the design work they came from.

## Words that signal a missing reason

If you need these words to justify a design, you haven't found the reason yet. Replace them with the concrete fact.

- English: modern, sleek, clean, elegant, luxurious, timeless, unique, innovative, harmonious, seamless, dynamic, iconic, elevate, "a blend of tradition and modernity".
- Arabic: عصري، راقي، فخم، فريد، مبتكر، لمسة، تناغم، متكامل، "يجمع بين الأصالة والمعاصرة".

## How to present

Keep it short and let the design do the talking:

1. The concept in one line, and the facts it came from.
2. The system: type, colours with hex values, grid, signature move.
3. What you rejected (the obvious direction A), in one line.
