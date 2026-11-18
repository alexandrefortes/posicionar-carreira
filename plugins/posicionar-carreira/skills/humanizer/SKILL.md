---
name: humanizer
description: Review prose for AI-generated patterns and rewrite only passages where they materially hurt clarity, precision, or the writer's voice. Preserve facts, meaning, and already-natural writing. Use for inflated claims, sales language, vague sources, repetitive structure, stock AI words, passive voice, filler, or chatbot artifacts. Based on Wikipedia's "Signs of AI writing."
---

# Humanizer

Edit only passages where a recognizable AI writing pattern harms clarity, precision, rhythm, credibility, or the writer's voice. Natural prose may need no changes.

## Decide whether to rewrite

Judge the text itself. Never add or consult a marker, comment, or metadata field recording an earlier pass. Protect quotations, source material, code, metadata, data, link targets, and anything the user wants preserved.

Name the exact pattern and the harm it causes in context. Watch for inflated claims, unnamed sources, sales language, missing actors, repetitive structure, stock phrases, excessive hedging, and chatbot residue. Use the row that fits the evidence.

| Case | Evidence required |
| --- | --- |
| Isolated passage | One severe artifact, such as chatbot residue, invented or unsupported attribution, or sustained stock sales prose. A passage also qualifies if patterns from at least three independent families dominate it and at least one concerns content or chatbot behavior. |
| Sustained pattern across a document | The same severe artifact recurs, or at least three independent families appear across two or more passages. For the latter case, at least one family concerns content or chatbot behavior, and at least two families recur. The families can appear in different paragraphs. |

When the document qualifies, scan all editable prose for the diagnosed families. An occurrence can qualify on its own if you can identify the pattern, show its harm, and materially improve the passage. Apply the original threshold to unrelated patterns.

A useful edit removes a clear artifact, resolves genuine ambiguity, replaces vagueness with evidence already present, or substantially reduces the effort to understand a passage. An antecedent is ambiguous when a reader cannot identify it from the immediate context or can reasonably identify more than one.

A single word, dash, greeting, adjective, long sentence, abstraction, or stylistic preference is insufficient. Multiple instances of the same pattern still count as one family. Keep clear pronouns, natural headings, deliberate repetition, and the writer's choice of person or register. If the only gain is polish, or the evidence is uncertain, leave the passage alone. Consult the [pattern catalog](references/patterns.md) only when it helps decide a case.

## Match the writer's voice

1. Follow the user's instructions for this text.
2. Use the author’s style guide and relevant samples when supplied. Otherwise, infer tone and register from the source and its audience.
3. Apply general guidance where it fits the writer. Keep a deliberate feature of the author's documented style unless the user directs otherwise.

In essays, posts, opinions, or personal writing, preserve mixed feelings, humor, asides, uncertainty, and uneven rhythm. Add an opinion or reaction only when it fits the writer's voice and position. Use a neutral tone for factual, technical, reference, and legal material.

## Rewrite and verify

1. Before drafting, list each changed passage's claims, opinions, qualifications, and purpose. Record who acted, the scope, certainty, causal links, rankings, and each side of a comparison.
2. Rewrite the diagnosed passage around its main point. Use familiar verbs such as *is* and *has*. Read the draft aloud for rhythm, detail, and formality. Change punctuation in a rewritten passage only when it improves readability and fits the author’s voice.
3. Compare source and draft side by side. Map each independent clause and each side of an explicit contrast to explicit wording in the draft. A section that can be read alone must retain its own facts, even if another section repeats them. Keep names, numbers, dates, quotations, and citations. Every new factual claim needs support from the source or user. If a detail is missing, ask for it or simplify the sentence. Fiction can introduce invented details when the task calls for them.
4. Check the strength of each claim. Preserve modal verbs, quantifiers, rankings, stated roles, and self-assessments. *I know*, *I led*, and *always* differ from *I think*, *I contributed*, and *usually*. A contractual constraint can explicitly rule out a technical one. Preserve both facts. When a promotional label is the problem, use the experience, role, result, or evidence the source gives for it. A copy edit never justifies adding a hedge or converting a guess into a fact.
5. Revert any change that alters meaning or lacks a concrete benefit. Rescan the whole editable text for remaining occurrences of the diagnosed families. Apply the same criteria to the final draft as to fresh input. Stop when another pass would only produce equivalent phrasing.

## How to return the result

| Input | Deliverable |
| --- | --- |
| Pasted text (default) | If edits qualify, return the draft, a short list of AI patterns still present in that draft, and the final rewrite. Otherwise, say the original needs no changes and return it unchanged. |
| Named file | Write only the final prose to the file. Preserve code blocks, YAML, data, and link targets. In the summary, identify the families that justified **each** changed passage. Revert any edit you cannot justify. If none qualify, leave the file untouched and say so. |
| Another task using this skill, such as a pull request, commit message, or document | Return only the final text. If no edits qualify, return the input unchanged. |

## Source

The patterns are based on [Wikipedia's Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup. The [catalog](references/patterns.md#attribution) credits the contributors and identifies the license.
