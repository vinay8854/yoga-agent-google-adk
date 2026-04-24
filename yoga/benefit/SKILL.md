---
name: benefit
description: Provide clear, factual benefits of practicing yoga.
metadata:
  output_schema: schema.json
resources:
  assets:
    schema.json: schema.json
---
# Benefit of Yoga

## Purpose
Provide clear, factual benefits of practicing yoga.

## Key Points

### Physical Benefits
- Improves flexibility and mobility
- Increases muscle strength
- Enhances posture and body alignment
- Supports better digestion
- Helps in weight management

### Mental Benefits
- Reduces stress and anxiety
- Improves focus and concentration
- Enhances emotional stability
- Promotes better sleep

### Long-Term Benefits
- Improves overall lifestyle discipline
- Helps manage chronic conditions (like back pain, mild hypertension)
- Increases body awareness

## Response Guidelines
- Keep explanations simple and direct
- Avoid exaggeration (no “instant cure” claims)
- Link benefits to consistency, not one-time practice
- **STRUCTURED OUTPUT**: You MUST use the `physical_benefits`, `mental_benefits`, and `expert_note` fields from the JSON schema. Set `general_talk` to an empty string.
