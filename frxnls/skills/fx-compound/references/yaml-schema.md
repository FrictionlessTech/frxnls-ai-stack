# YAML Frontmatter Schema

`schema.yaml` in this directory is the canonical contract for `docs/solutions/`
frontmatter written by `fx-compound`. This file is the quick reference for
required fields, enum values, validation, the category mapping, and track
classification.

## Tracks

The `problem_type` determines which **track** applies. Each track has different
required and optional fields.

| Track | problem_types | Description |
|-------|--------------|-------------|
| **Bug** | `build_error`, `test_failure`, `runtime_error`, `performance_issue`, `database_issue`, `security_issue`, `ui_bug`, `integration_issue`, `logic_error` | Defects and failures that were diagnosed and fixed |
| **Knowledge** | `best_practice`, `documentation_gap`, `workflow_issue`, `developer_experience`, `architecture_pattern`, `design_pattern`, `tooling_decision`, `convention` | Practices, patterns, conventions, decisions, workflow improvements, and documentation. Prefer the narrowest applicable value; `best_practice` is the fallback. |

## Required Fields (both tracks)

- **module**: Module or area affected (free text)
- **date**: ISO date in `YYYY-MM-DD`
- **problem_type**: one of the values in the Tracks table above
- **component**: one of `expo_screen`, `rn_component`, `navigation`, `native_module`, `api_route`, `server`, `database`, `migration`, `auth`, `payments`, `state_management`, `data_fetching`, `styling`, `ci_cd`, `skill_or_agent`, `tooling`, `testing`, `documentation`, `development_workflow`. Prefer the narrowest applicable value.
- **severity**: one of `critical`, `high`, `medium`, `low`

## Bug Track Fields (required on bug-track docs)

- **symptoms**: YAML array, 1-5 observable symptoms (errors, broken behavior)
- **root_cause**: one of `missing_index`, `missing_migration`, `missing_relation`, `wrong_api`, `scope_issue`, `race_condition`, `async_timing`, `memory_leak`, `config_error`, `logic_error`, `type_error`, `test_isolation`, `missing_validation`, `missing_permission`, `rls_policy`, `platform_specific`, `stale_cache`, `dependency_mismatch`, `missing_workflow_step`, `inadequate_documentation`, `missing_tooling`, `incomplete_setup`
- **resolution_type**: one of `code_fix`, `migration`, `config_change`, `test_fix`, `dependency_update`, `native_rebuild`, `environment_setup`, `workflow_improvement`, `documentation_update`, `tooling_addition`

## Knowledge Track Fields

No additional required fields beyond the shared ones. All optional:

- **applies_when**: conditions or situations where this guidance applies
- **symptoms**: observable gaps or friction that prompted this guidance
- **root_cause**: underlying cause, if there is a specific one
- **resolution_type**: type of change, if applicable

## Optional Fields (both tracks)

- **related_components**: other components involved
- **tags**: search keywords, lowercase and hyphen-separated
- **versions**: relevant version pins, free text, only when load-bearing

## Category Mapping (problem_type → directory)

- `build_error` → `docs/solutions/build-errors/`
- `test_failure` → `docs/solutions/test-failures/`
- `runtime_error` → `docs/solutions/runtime-errors/`
- `performance_issue` → `docs/solutions/performance-issues/`
- `database_issue` → `docs/solutions/database-issues/`
- `security_issue` → `docs/solutions/security-issues/`
- `ui_bug` → `docs/solutions/ui-bugs/`
- `integration_issue` → `docs/solutions/integration-issues/`
- `logic_error` → `docs/solutions/logic-errors/`
- `developer_experience` → `docs/solutions/developer-experience/`
- `workflow_issue` → `docs/solutions/workflow-issues/`
- `best_practice` → `docs/solutions/best-practices/`
- `documentation_gap` → `docs/solutions/documentation-gaps/`
- `architecture_pattern` → `docs/solutions/architecture-patterns/`
- `design_pattern` → `docs/solutions/design-patterns/`
- `tooling_decision` → `docs/solutions/tooling-decisions/`
- `convention` → `docs/solutions/conventions/`

## Validation Rules

1. Determine the track from `problem_type` using the Tracks table.
2. All shared required fields must be present.
3. Bug-track required fields (`symptoms`, `root_cause`, `resolution_type`) must be present on bug-track docs.
4. Knowledge-track docs have no additional required fields beyond the shared ones.
5. Enum fields must match the allowed values exactly.
6. Array fields must respect min/max item counts.
7. `date` must match `YYYY-MM-DD`.

## YAML Safety Rules

Strict YAML 1.2 parsers (`yq`, `js-yaml` strict, PyYAML) reject array items that
start with a reserved indicator character as unquoted scalars. When writing items
for any array-of-strings field (`symptoms`, `applies_when`, `tags`,
`related_components`, or any future array field), wrap the value in double quotes
if it starts with any of:

`` ` ``, `[`, `*`, `&`, `!`, `|`, `>`, `%`, `@`, `?`

Also quote if the value contains the substring `": "` — that punctuation confuses
flow-style parsers.

Example — before (breaks strict YAML):

    symptoms:
      - `npx expo prebuild` wipes the ios/ directory

Example — after (parses cleanly):

    symptoms:
      - "`npx expo prebuild` wipes the ios/ directory"

`scripts/validate-frontmatter.py` catches the silent-corruption subset of these
(unquoted ` #` and `: ` in scalar values) but does not enforce schema rules — run
it after writing, and fix until it exits 0.
