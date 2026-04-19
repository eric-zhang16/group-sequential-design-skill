# Biostatistics Skills for Claude Code

A collection of [Claude Code](https://claude.ai/code) skills for biostatistics workflows in clinical development. Each skill automates a specific domain — from trial design to analysis to reporting — through structured conversations that produce verified, reproducible outputs.

## Skills

| Skill | Description | Status |
|-------|-------------|--------|
| [Group Sequential Design](./plugins/group-sequential-design/) | Design group sequential clinical trials for survival endpoints with interim analyses, spending functions, multiplicity, and simulation verification | Available |
| [KM Digitizer](./plugins/km-digitizer/) | Digitize Kaplan-Meier survival curves from PNG images, reconstruct individual patient-level IPD, and generate Word reports with KM comparison plots, survival statistics, and hazard rate curves | Available |

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

### Manual Installation (recommended if you want to update skills locally)

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

This repo is a Claude Code plugin marketplace. Each folder under `plugins/` is a **plugin** containing one skill.

```
Biostatistics-skills/
├── .claude-plugin/                  # Marketplace metadata
├── plugins/
│   ├── group-sequential-design/     # Plugin: group sequential trial design
│   └── km-digitizer/                # Plugin: KM plot digitization and IPD reconstruction
└── README.md
```

## License

Each skill may have its own license. See the individual skill folders for details.
