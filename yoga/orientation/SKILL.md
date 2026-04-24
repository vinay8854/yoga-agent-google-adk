---
name: orientation
description: Help users understand how the yoga program works and how to get started.
metadata:
  output_schema: schema.json
resources:
  assets:
    schema.json: schema.json
---
# Yoga Orientation

## Purpose
Help users understand how the yoga program works and how to get started.

## Key Information

### What to Expect
- Daily or scheduled sessions
- Guided instructions
- Beginner-friendly approach

### Session Timings
- Morning and/or evening batches (if applicable)

### Requirements
- Comfortable space
- Yoga mat (optional but recommended)
- Consistent timing

### Rules / Guidelines
- Join sessions on time
- Practice on an empty or light stomach
- Follow instructions carefully

## Response Guidelines
- Keep it structured and practical
- Focus on clarity, not motivation
- Avoid unnecessary storytelling
- **STRUCTURED OUTPUT**: You MUST use the `program_overview` and `getting_started_steps` fields from the JSON schema. Set `general_talk` to an empty string.
