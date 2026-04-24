---
name: asan
description: Provide information about yoga poses (asanas).
metadata:
  output_schema: schema.json
resources:
  assets:
    schema.json: schema.json
---
# Asan of Yoga

## Purpose
Provide information about yoga poses (asanas), including how to perform and their benefits.

## Structure of Response

### Asana Name
- Example: Tadasana, Bhujangasana, Vrikshasana

### Steps
- Step-by-step instructions
- Keep steps short and clear

### Benefits
- Physical or mental benefits of the pose

### Precautions
- Who should avoid or modify the pose
- Common mistakes to avoid

## Response Guidelines
- Do not overload with too many poses at once
- Prefer 1–3 asanas per response
- Keep instructions safe and beginner-friendly
- **STRUCTURED OUTPUT**: You MUST use the `asana_name`, `steps`, `benefits`, and `precautions` fields from the JSON schema. Set `response` to an empty string.
