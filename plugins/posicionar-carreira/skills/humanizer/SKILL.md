---
name: humanizer
description: Review prose for AI-generated patterns and rewrite only passages where they materially hurt clarity, precision, or the writer's voice. Preserve facts, meaning, and already-natural writing. Use for inflated claims, sales language, vague sources, repetitive structure, stock AI words, passive voice, filler, or chatbot artifacts. Based on Wikipedia's "Signs of AI writing."
---
# Humanizer: remove AI writing patterns

Review text for AI-generated writing patterns. Rewrite only passages that need it so they read like the writer, not a chatbot. Keep the writer's facts, meaning, voice, and already-good prose. A correct result may contain no changes.

The patterns below come from Wikipedia's ["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup.

## What to do

When given text to humanize:

1. **Identify the editable prose.** Separate it from quotations, source material, code, metadata, data, link targets, and anything the user says to preserve.
2. **Diagnose before editing.** Find specific AI patterns and state internally what each one harms: clarity, precision, rhythm, credibility, or the writer's recognizable voice.
3. **Decide whether a rewrite is justified.** This skill is not a general copy editor. First decide whether AI patterns are isolated or sustained across the document. Use the strict passage-level gate below for isolated patterns. A sustained diagnosis may come from a cluster distributed across separate passages; all three families need not occur in one paragraph. When the document qualifies, find and resolve material remnants from the diagnosed families without requiring every remnant to contain a new three-family cluster. If the text is within the normal range of human writing and fits the writer's voice, leave it unchanged even when another version could be clearer, shorter, more explicit, or more polished. When in doubt, do not edit.
4. **Rewrite only diagnosed passages.** Do not replace a natural sentence with an equivalent sentence merely because another wording is possible.
5. **Keep every claim and relationship.** Before changing a passage, inventory its facts, opinions, qualifications, contrasts, causal links, scope, actor, epistemic strength, and intended function. Require bidirectional semantic fidelity: the rewrite must preserve every proposition in the source passage, and every proposition in the rewrite must be supported by the source or user. Do not weaken, strengthen, generalize, or merely imply a claim that the source states explicitly. Repetition elsewhere in the document does not compensate for information lost from a section that may be read or reused on its own. You may shorten, expand, merge, or split only when a diagnosed problem requires it; shorter is not automatically better.
6. **Do not invent facts.** Do not add a fact, name, number, date, quote, or citation unless it comes from the source or the user. If a sentence needs a missing detail, ask for it or use a simpler sentence. You may add an opinion or reaction when the writer's voice calls for one, but you may not add a factual claim. Fiction is exempt because invented details are part of the task.
7. **Preserve the writer's voice.** Follow any style guidance provided for the current text and preserve the voice evident in the original.

The input type controls what you return. See [How to return the result](#how-to-return-the-result). Use the same rewrite process in every mode.

Fidelity is a veto, not a tradeoff. Discard an edit if it changes meaning, claim strength, certainty, uncertainty, or the writer's stated self-assessment, even when the new wording sounds smoother or more cautious. Humanization is not fact-checking. Do not soften a strong claim or hedge a direct statement unless the source itself expresses that uncertainty.

Treat words that carry propositional claim force as semantic anchors. This includes modals, quantifiers, rankings, scope limits, certainty markers, and factual descriptions of the writer's role or actions. Prefer to keep those words unchanged. For example, do not turn *I know* into *I think*, *I led* into *I contributed to*, *is* into *may be*, or *always* into *usually*.

Do not confuse propositional force with rhetorical inflation. Promotional intensifiers and self-aggrandizing labels are not protected merely because they sound strong. When that inflation is the diagnosed artifact, replace it with the concrete basis already present in the source, such as experience, results, role, or evidence. Preserve the underlying fact and the writer's actual position; do not preserve unsupported grandeur as if it were a separate fact.

Treat an explicit contrast as two propositions plus the relationship between them. If a formula such as *X, not Y* is the diagnosed artifact, rewrite the formula but keep both sides explicit whenever both carry information. For example, *the constraint is contractual, not technical* may become *the contract creates the constraint; the technology is not the blocker*. It may not become only *the contract creates the constraint*.

## Decide whether to rewrite

Judge the current prose itself. Do not add or consult a marker, metadata field, comment, or other signal that says the text was previously humanized. The skill must recognize acceptable writing from the writing.

No change is a successful result. Leave a passage unchanged unless all four conditions hold:

1. You can identify the exact pattern in the current wording.
2. The passage contains one severe artifact, is dominated by a cluster from at least three independent pattern families, or belongs to a document with a sustained pattern as defined below. Passage- and document-level clusters must include a content or chatbot pattern rather than only style or clarity concerns. A severe artifact is something like chatbot residue, an invented or unsupported attribution, or sustained stock sales/corporate prose. Ordinary stylistic weakness, repetition, abstraction, or a mild clarity issue is not severe and cannot form a qualifying cluster by itself.
3. The pattern causes a concrete problem in context, rather than merely matching a watched word or punctuation mark.
4. The proposed edit materially improves the passage instead of exchanging one natural formulation for another.

The cluster gate diagnoses isolated passages; it is not permission to stop after fixing representative examples. A document has a sustained AI pattern when one severe artifact recurs or when patterns from at least three independent families appear across at least two separate passages, at least one family is content or chatbot, and at least two of the families recur. The full cluster may be distributed across the document rather than repeated inside each passage. In that state, inspect all editable prose for remnants from the families already diagnosed. A remnant may be rewritten without forming another three-family cluster only when the exact pattern is present, it causes a concrete problem in context, and the edit is a material improvement. This does not lower the gate for unrelated patterns or authorize polishing natural passages.

A material improvement must be observable in the resulting prose: it removes a qualifying high-confidence AI pattern, resolves genuine ambiguity about an actor or relationship, replaces unsupported vagueness with specificity already present in the source, or reduces substantial cognitive load. Marginal polish does not count.

One watched word, an em dash, curly quotation marks, a long sentence, polished grammar, a vague adjective, a greeting, a pronoun, a demonstrative, a first- versus third-person choice, a heading formulation, or a personal stylistic preference is not enough. Use the full passage, the document's register, and the writer's established voice as evidence. Do not combine several observations from the same pattern family to manufacture a cluster.

A referent is genuinely ambiguous only when a reasonable reader cannot identify its antecedent from the immediate context or when more than one antecedent is plausible. A demonstrative that clearly summarizes the preceding sentence is not vague merely because it could be replaced with a more explicit noun phrase. Abstract wording is not an AI pattern by itself.

Use the writer's established voice and any style guidance supplied by the user after a passage fails the threshold, not as an invitation to optimize every sentence. Do not make acceptable prose more formal, direct, elegant, consistent, specific, cautious, or personal. Do not cycle synonyms, rephrase headings, swap greetings, add first person, replace a clear pronoun with a name, or change sentence openings only to produce a visible diff.

Every changed span must trace to a supported diagnosis and a concrete benefit. If no such edit remains, return the prose unchanged. This stability must come from evaluating the text, not from detecting whether the skill ran before.

A passage is finished when no high-confidence pattern materially harms it, its claims and relationships remain explicit, and its register fits the document. Judge the proposed final prose on its own. If another pass could only make an already-good sentence differently good, stop.

## Preserve the writer's voice

Follow instructions for the current text. If the user provides a style guide or samples, use them to understand the writer's tone, rhythm, vocabulary, and level of formality. Otherwise, take those cues from the source text and its audience. Preserve deliberate choices in language and style when they work for the text.

## Add personality only when it fits

Removing AI patterns is only half the job. The result should still sound like a person.

Use personality in blog posts, essays, opinions, and personal writing when it fits the writer. Keep reference, technical, legal, and factual text neutral. Do not add opinions or first-person language where they do not belong.

When personality fits, keep the writer's opinions, uncertainty, mixed feelings, humor, asides, and uneven rhythm. Never invent facts to make the text feel personal.

## Pattern catalog

Use these categories as diagnostic prompts, not as a checklist that must produce edits:

- inflated importance, sales language, or vague sources;
- stock transitions, contrast formulas, forced groups, slogans, dramatic fragments, or generic endings;
- passive voice, missing actors, or vague referents that hide a concrete action or relationship;
- repetitive structure, synonym cycling, filler, hedging, chatbot residue, and unsupported speculation;
- formatting habits that conflict with the writer's established style.

If a candidate is ambiguous, or if its boundary matters to the decision, read [references/patterns.md](references/patterns.md). Do not load the catalog merely to find something to change. A listed word or construction is evidence only in context.

## How to return the result

**Pasted text (default).** When changes are justified, return the draft, a short list of remaining AI patterns, and the final rewrite. When no change is justified, say so and return the original text unchanged.
**File mode.** When the user names a file, diagnose it before writing. If changes are justified, write only the final text to the file. Change prose only. Keep code blocks, YAML metadata, data, and link targets unchanged. If no change is justified, leave the file untouched. In the summary, name the pattern families that justified each changed passage; if you cannot name them, revert the edit. When no passage passes the threshold, say that no changes were needed.
**Embedded mode.** When another task uses this skill for a pull request, commit message, or document, return only the final text. If no change is justified, return the input unchanged.

## Rewrite process

1. Read the source. Identify editable prose and protected content before considering changes.
2. Mark each candidate AI pattern and the concrete problem it causes. Decide whether the evidence is isolated or sustained across the document. When the document meets the sustained-pattern rule, scan all editable prose for remnants from every diagnosed family, not only the first pattern or passage found. Apply [Decide whether to rewrite](#decide-whether-to-rewrite) to every candidate before drafting.
3. If no edit passes that gate, stop and return the unchanged input as required by the current mode.
4. Rewrite only the diagnosed passages. Read the draft aloud. Check the rhythm, details, simple verbs such as *is* and *has*, and the right level of formality.
5. Compare every changed passage with its source, side by side. Make one internal checklist item for each independent clause and each side of an explicit comparison or contrast, then map every item to explicit wording in the rewrite. A missing mapping fails the edit. Check facts and semantic anchors sentence by sentence; similarity of the overall gist is not enough. Then ask three questions:
   - **"What still sounds AI-generated?"**
   - **"Does every change fix an identified problem, or did I merely substitute equivalent wording?"**
   - **"Can a reader recover every original proposition, with the same strength and explicit relationships, from the rewritten passage? Is every new proposition supported by the source or user?"**
   Revert any edit that merely changes style without a diagnosed benefit. Also revert an edit that removes, weakens, strengthens, generalizes, or leaves implicit any original fact, opinion, relationship, qualification, contrast, causal link, scope, actor, intended function, name, number, date, quote, citation, ranking, or other claim. Do not rely on the same information appearing elsewhere in the document.
6. Rescan the full editable text, not only the changed passages, for every pattern family diagnosed in this run. Resolve in this pass every remaining occurrence allowed by the isolated- or sustained-pattern rule. Do not stop after a representative sample of fixes.
7. Judge the draft as if it were the input to a fresh run, without using a marker or knowledge of the current edit. If the only remaining options are alternate phrasings of already-good prose, stop.
8. Write the final version. State each point naturally instead of patching one flagged phrase at a time. If a sentence stays awkward, rewrite the paragraph around its main point. In passages already being rewritten, change em and en dashes when doing so helps readability and fits the writer's style. Do not edit an otherwise acceptable passage solely to remove a dash.

Return the result required by [How to return the result](#how-to-return-the-result).

## Source

This skill is based on [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup. Its patterns come from reviews of AI-generated text on Wikipedia.

The [pattern catalog](references/patterns.md) credits the Wikipedia contributors and identifies the license for the adapted examples.
