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

### Installation

1. Clone this repo:
   ```bash
   git clone https://github.com/eric-zhang16/Biostatistics-skills.git
   ```

2. Copy the skill folder(s) you need into your project's `.claude/skills/` directory:
   ```
   your-project/
   └── .claude/
       └── skills/
           └── group-sequential-design/
               ├── SKILL.md
               ├── reference.md
               └── ...
   ```

3. Follow the skill-specific setup instructions in its README.

## Repo Structure

```
Biostatistics-skills/
├── README.md
├── group-sequential-design/       # Group sequential trial design skill
├── km-digitizer/                  # KM plot digitization and IPD reconstruction skill
└── <future-skill>/                # Additional skills to come
```

## Contributing

To add a new skill:

1. Create a folder named after the skill (e.g., `sample-size-reestimation/`)
2. Include at minimum: `SKILL.md` (instructions), `README.md` (documentation), and `evals/evals.json` (test scenarios)
3. Follow the existing skill structure as a template

## License

Each skill may have its own license. See the individual skill folders for details.
