# Koala Layout Prompts

This folder replaces the old single `docs/prompts.md` file.

Each file is a self-contained prompt for an LLM specialized in one Koala layout:

- `tree.md`
- `synoptic.md`
- `synoptic_boxes.md`
- `radial.md`

Each prompt includes:

- the core DSL syntax
- the numbering model
- optional semantic kinds
- the minimum layout-specific rules

Use the prompt that matches the target layout. The generated answer should be Koala DSL only.

As a general rule, prompts should keep metadata minimal and only set the target `@layout` unless the user explicitly asks for additional settings.
