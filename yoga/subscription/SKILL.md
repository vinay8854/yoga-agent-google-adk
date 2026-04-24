---
name: subscription
description: Provide clear information about plans, access, and joining process.
metadata:
  output_schema: schema.json
resources:
  assets:
    schema.json: schema.json
---
# Yoga Subscription

## Purpose
Provide clear information about plans, access, and joining process.

## Key Information

### What User Gets
- Access to yoga sessions
- Guidance from instructors
- Structured program

### Plan Details
- Duration (e.g., monthly, quarterly)
- Pricing (if applicable)
- Renewal process

### How to Join
- Step-by-step process
- Payment method (if needed)
- Confirmation flow

### Support
- Contact or help process for issues

## Response Guidelines
- Be direct and transparent
- Avoid vague statements
- No pressure tactics
- **STRUCTURED OUTPUT**: You MUST use the `plan_summary`, `joining_steps`, and `support_info` fields from the JSON schema. Set `general_talk` to an empty string.
