# Koala Layout Prompts

This folder replaces the old single `docs/prompts.md` file.

Each file is a self-contained prompt for an LLM specialized in one Koala layout:

- `tree.md`
- `synoptic.md`
- `synoptic_boxes.md`
- `radial.md`

Each prompt includes:

- the current DSL syntax
- supported metadata options
- available semantic kinds
- layout-specific structure advice
- page-size suggestions
- node-count and depth guidance

Use the prompt that matches the target layout. The generated answer should be Koala DSL only.

As a general rule, prompts should avoid emitting `@show-node-numbers` unless the user explicitly asks for numbering behavior to be embedded in the document metadata.
