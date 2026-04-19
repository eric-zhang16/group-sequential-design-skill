# Biostatistics Skills for Claude Code

A collection of [Claude Code](https://claude.ai/code) skills for biostatistics workflows in clinical development. Each skill automates a specific domain — from trial design to analysis to reporting — through structured conversations that produce verified, reproducible outputs.

## Skills

| Skill | Description | Status |
|-------|-------------|--------|
| [Group Sequential Design](./group-sequential-design/) | Design group sequential clinical trials for survival endpoints with interim analyses, spending functions, multiplicity, and simulation verification | Available |
| [KM Digitizer](./km-digitizer/) | Digitize Kaplan-Meier survival curves from PNG images, reconstruct individual patient-level IPD, and generate Word reports with KM comparison plots, survival statistics, and hazard rate curves | Available |

## What Are Claude Code Skills?

Skills are structured instructions that teach Claude Code how to perform specialized tasks. When you invoke a skill (via `/skill-name` or by describing the task), Claude follows a defined workflow — asking the right questions, writing and executing code, verifying results, and producing deliverables.

Each skill in this repo is self-contained: it includes its own instructions, reference material, code examples, and evaluation scenarios.

## Getting Started

### Prerequisites

- [Claude Code](https://claude.ai/code) (CLI, desktop app, or IDE extension)
- Skill-specific dependencies (see each skill's README)

### Installation via Plugin Marketplace (recommended)

Add this repo as a Claude Code marketplace (one-time setup):

```bash
/plugin marketplace add https://github.com/eric-zhang16/Biostatistics-skills.git
```

Then install individual skills:

```bash
/plugin install km-digitizer@Biostatistics-skills
/plugin install group-sequential-design@Biostatistics-skills
```

### Manual Installation

1. Clone this repo:
   ```bash
   git clone https://github.com/eric-zhang16/Biostatistics-skills.git
   ```

2. Copy the skill folder(s) you need into your project's `.claude/skills/` directory:
   ```
   your-project/
   └── .claude/
       └── skills/
           └── km-digitizer/
   ```

3. Follow the skill-specific setup instructions in its README.

## Repo Structure

This repo is a Claude Code plugin marketplace. Each top-level folder is a **plugin** — a self-contained package containing one skill.

```
Biostatistics-skills/
├── .claude-plugin/
│   └── marketplace.json              # Marketplace index ($schema: anthropic.com/claude-code/marketplace.schema.json)
├── group-sequential-design/          # Plugin: group sequential trial design
│   ├── .claude-plugin/
│   │   └── plugin.json               # Plugin metadata (name, description, author)
│   ├── skills/
│   │   └── group-sequential-design/  # Skill content
│   │       ├── SKILL.md              # Workflow instructions
│   │       ├── reference.md
│   │       ├── examples.md
│   │       ├── post_design.md
│   │       ├── scripts/
│   │       └── evals/
│   ├── LICENSE
│   └── README.md
├── km-digitizer/                     # Plugin: KM plot digitization and IPD reconstruction
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── skills/
│   │   └── km-digitizer/             # Skill content
│   │       ├── SKILL.md
│   │       ├── scripts/
│   │       └── evals/
│   └── README.md
└── README.md
```

## Contributing

To add a new skill, follow the plugin structure used by this marketplace:

1. Create a plugin folder named after the skill (e.g., `sample-size-reestimation/`)
2. Add `.claude-plugin/plugin.json` with `name`, `description`, and `author`
3. Create `skills/<skill-name>/` containing at minimum:
   - `SKILL.md` — workflow instructions for Claude
   - `evals/evals.json` — evaluation scenarios
4. Add a `README.md` at the plugin root (user-facing docs)
5. Register the plugin in `.claude-plugin/marketplace.json` under `plugins`
6. Follow the existing plugin folders as a template

## License

Each skill may have its own license. See the individual skill folders for details.
