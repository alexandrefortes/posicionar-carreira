# Pattern catalog and false-positive guide

Use this guide when the context leaves a pattern in doubt. Apply the [rewrite criteria](../SKILL.md#decide-whether-to-rewrite) before editing. Examples illustrate local changes. Preserve every supported claim in the actual passage.

## Content patterns

### 1. Inflated claims about importance and legacy

Look for *a pivotal moment*, *indelible mark*, *stands as a testament*, or claims that one event reflects a wider trend. Keep the event and any documented relationship. “The institute was established in 1989 as part of Spain's decentralization” gives a date and context without declaring its historical importance.

### 2. Name-dropping to prove importance

A list of outlets or followers establishes where someone appeared or how large an audience was. It cannot establish influence on its own. Keep relevant names, counts, and what the person said if the source supplies it.

### 3. Shallow analysis with -ing phrases

Inspect chains of *highlighting*, *symbolizing*, *fostering*, or *showcasing*. Keep concrete relationships. “The blue and gold evoke the coast” states a design intention if the source supports it. A claim about “reflecting the community's deep connection” needs its own basis.

### 4. Sales language

Watch for *boasts*, *vibrant*, *nestled in*, *groundbreaking*, or *must-visit*, especially in descriptions of places, products, or organizations. “The town is in Gonder” gives the location. Retain any specific cultural or geographic feature the source describes.

### 5. Vague sources

“Experts believe”, “industry reports show”, and “observers have noted” need a source. Name the source if supplied. Remove unsupported attribution rather than inventing an expert or presenting their supposed opinion as fact.

### 5a. Vague evaluation when exact evidence is available

If a passage must convey a measured result on its own, use the comparison already in the source in place of *large*, *strong*, or *significant*. Keep deliberate qualitative summaries and the force of personal opinions and self-assessments.

### 6. Formulaic challenges and outlook sections

A heading such as “Future Outlook” often introduces generic adversity and optimism. Identify the actual issue, such as recurring traffic congestion and water shortages. Include dates, public action, or plans only when documented.

## Language and grammar patterns

### 7. Overused AI words

Watch for clusters of *actually, additionally, align with, crucial, delve, emphasize, enduring, enhance, foster, garner, gate, highlight, interplay, intricate, key, landscape, pivotal, quietly, showcase, tapestry, testament, underscore, valuable,* and *vibrant*. Figurative uses of *gate* or *landscape* differ from established technical meanings. A cluster matters when the words obscure the point or disrupt the writer's voice.

### 8. Avoiding is and are

When *serves as*, *stands as*, *boasts*, or *features* carries no additional meaning, use the simple verb. “Gallery 825 is the exhibition space. It has four rooms.”

### 9. Not X but Y and clipped negative endings

In formulas such as “It's not just X, it's Y”, identify both claims. Keep both when the distinction matters. A clipped “The options come from the selected item, no guessing” can become “The options come from the selected item, so the user does not have to guess.”

### 10. Forced groups of three

Distinguish a real list from a trio added to sound complete. “Talks, panels, and time for networking” describes a program. “Innovation, inspiration, and insights” adds little unless the source says what attendees will learn.

### 11. Changing names and repeating sentence openings

Use one name for one subject. Switching between *protagonist*, *main character*, and *central figure* can imply different people. When repeated openings add no rhythm or meaning, combine actions or change the subject. “She noted the door. She noted the lock” becomes “She noted the door and its lock.”

### 12. False from X to Y ranges

Use “from X to Y” for a real range. If the examples are separate subjects, list them directly. “The book covers the Big Bang, star formation, and dark matter.”

### 13. Passive voice, missing subjects, and vague referents

Name the actor or referent when that resolves uncertainty. “The system saves the results” identifies who saves them. A pronoun or demonstrative that clearly refers to the preceding sentence needs no replacement.

## Style patterns

### 14. Em and en dashes

A dash alone never triggers a rewrite. When a passage needs editing for another reason, change its punctuation only if it improves readability and fits the writer’s voice.

### 15. Too much bold text

Reserve bold for meaningful emphasis. Several acronyms in one sentence rarely need every term and expansion in bold. Keep the expansions themselves.

### 16. Lists with bold mini-headings

A label that repeats the following words can go. For example, “**Performance:** Performance improved through optimized algorithms” can become “Optimized algorithms improved performance.” Preserve labels when they help the reader find an item.

### 17. Title case in headings

Follow the publication's style. In sentence case, “Strategic Negotiations and Global Partnerships” becomes “Strategic negotiations and global partnerships.”

### 18. Emojis

Remove purely decorative icons from headings or lists when they conflict with the writer's style. “🚀 **Launch Phase:** The product launches in Q3” can become “The product launches in Q3.”

### 19. Curly quotation marks

Match the writer or target format when editing a passage. Word processors and content management systems often supply curly quotes automatically.

## Chatbot patterns

### 20. Chatbot text left in the answer

Remove conversational leftovers from standalone material, including “Of course!”, “Here is an overview”, “I hope this helps”, or “Would you like more examples?” Start with the first fact the source actually gives.

### 21. Knowledge-limit disclaimers and guesses

Remove statements about the model's training cutoff. Where a gap matters, describe what the available sources document. “Her early life is undocumented” does not support claims that she preferred privacy or grew up in a middle-class household. Omit an empty section when the gap does not matter.

### 22. Overly agreeable tone

Delete automatic praise or assent, such as “Great question!” or “You're absolutely right!” Answer the substance. Keep a deliberate expression of agreement when it conveys the writer's position.

## Filler and hedging

### 23. Filler phrases

| Wording | Shorter form |
| --- | --- |
| in order to | to |
| due to the fact that | because |
| at this point in time | now |
| in the event that | if |
| has the ability to | can |
| it is important to note that the data shows | the data shows |

### 24. Too many qualifiers

Keep the uncertainty the source expresses. Stacked qualifiers (*could potentially*, *might arguably*, *in some cases it may*) can express the same uncertainty several times. “The policy may affect outcomes” retains uncertainty. Remove a caveat that only repairs an earlier overstatement.

### 25. Generic positive endings

Drop send-offs such as “Exciting times lie ahead.” End on the last concrete fact or an actual plan the source gives.

### 26. Too many hyphenated word pairs

Follow the grammar of the phrase. Compare “a high-quality report” with “the report is high quality.” Combinations such as *client-facing*, *data-driven*, and *long-term* need a decision in context.

### 27. Pretending to reveal a deeper truth

“At its core”, “the real question”, and “what really matters” can announce a revelation where a direct claim suffices. “Teams need to change their habits” identifies the requirement.

### 28. Announcing the next point

Delete announcements such as “Let's dive into caching” or “Here's what you need to know.” Casual warnings can do the same thing. “One thing that bit me hard: the webpack dev server doesn't send the CORS header by default” can start at “The webpack dev server”.

### 29. A heading repeated in the first sentence

Under “Performance”, remove an empty “Speed matters” and start with the consequence the section explains, such as “When users hit a slow page, they leave.”

### 30. Writing about the previous version

Describe current behavior in reference documentation. “The function uses a hash map for O(1) lookups” is sufficient when the change itself is irrelevant. Keep history in release notes, change logs, migration guides, or other documents about a change.

### 31. Forced punchlines and dramatic fragments

One short sentence can carry emphasis. A series such as “No preference for symmetry. No aesthetic prior. No nostalgia for human taste” can express the connected observations as a sentence with a subject and verb.

### 32. Formulaic sayings

Look for slogans built around *the language of*, *the currency of*, or *X becomes a trap*. If the source means that symmetric layouts feel more predictable to users, state that claim directly.

### 33. Fake-candid openings

“Honestly?”, “Real talk”, and “Here's the thing” can stage a pause before an ordinary point. “Whether it's worth the price depends on how often you'll use it” can stand alone. *Honestly* or *look* can be natural in conversation.

### 34. Answering objections no one raised

Phrases such as “Don't get me wrong” and “I'm not saying” may defend against an objection absent from the text. Keep a real claim, named objection, or fully developed reply. A direct limitation such as “the API is not thread-safe” conveys technical information.

### 35. Rejecting fake alternatives

Check what a rejected option contributes. “One might be tempted to restart the service” is expendable if no reader would consider that option and it never matters again. Several unrelated rejections often reflect earlier drafts. Keep real alternatives, tradeoffs, and constraints a reader needs to decide.

## Check for false positives

### What not to flag

- Polished grammar, dry prose, a mixed register, academic vocabulary, and precise formatting can all reflect a writer, editor, or template. Lack of citations alone establishes nothing about authorship.
- Look for a pattern across the passage. A solitary transition, greeting, sign-off, short sentence, curly quote, or em dash is insufficient.
- Repeated openings can create deliberate rhythm. “She came. She saw. She conquered.” Keep the repetition when it does that work.
- Keep useful limits, legal and safety notices, real corrections, replies, FAQ answers, and options a reader would consider in a tutorial, argument, or design document.
- Preserve watched phrases in quotations, titles, proper names, and examples that discuss those phrases.

### Human details to keep

Preserve unusual specifics, mixed feelings, unresolved tension, deliberate first person, varied sentence lengths, genuine asides, and self-corrections. “The lawyer who used to work upstairs from my dentist” conveys more of the writer than a generic “acquaintance”.

Keep slang, memes, and in-jokes tied to their era or community. Consider provenance when available. Text written before ChatGPT's public launch on November 30, 2022 rarely warrants an inference of ChatGPT authorship.

## Attribution

The catalog includes adapted examples from contributors to Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). Those adaptations are available under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
