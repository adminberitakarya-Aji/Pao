# Contributing to PAO

Thank you for your interest in contributing to PAO — the AI Life Companion Platform. This document outlines the guidelines and standards for contributing to this project.

---

## Code of Conduct

By participating in this project, you agree to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to fostering an inclusive, respectful, and safe community.

---

## Ways to Contribute

### 1. Documentation
- Fill in empty documentation templates in `docs/`
- Improve existing documentation clarity and completeness
- Translate documentation to other languages

### 2. Code Contributions
- Core engine implementations (Identity, Memory, Relationship, Emotion)
- Mobile app (Flutter)
- Backend services (TypeScript/Node.js)
- AI Runtime (Python/LangGraph)
- Infrastructure/DevOps

### 3. Research & Design
- AI safety research
- UX/UI design for companion interactions
- Memory architecture research
- Emotional intelligence modeling

### 4. Community
- Report bugs and issues
- Suggest features via RFC process
- Help other contributors
- Share feedback from user testing

---

## Getting Started

### Prerequisites
- Git
- Node.js 20+
- Python 3.11+
- Flutter 3.19+
- Docker & Docker Compose

### Development Setup

```bash
# Clone the repository
git clone https://github.com/pao-ai/pao.git
cd pao

# Install dependencies (per service)
# Backend
cd backend && npm install

# AI Runtime
cd ai-runtime && pip install -r requirements.txt

# Mobile
cd mobile && flutter pub get

# Start development environment
docker-compose up -d
```

---

## Development Workflow

### Branch Naming
```
feature/<short-description>     # New features
fix/<short-description>         # Bug fixes
docs/<short-description>        # Documentation updates
refactor/<short-description>    # Code refactoring
rfc/<rfc-number>-<title>        # RFC implementation
```

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `security`

Examples:
```
feat(memory): add episodic memory consolidation
fix(identity): prevent personality drift on long conversations
docs(foundation): add grief policy to safety principles
```

### Pull Request Process

1. **Create an issue** or reference existing issue
2. **Fork** the repository and create your branch
3. **Write tests** for new functionality
4. **Ensure all tests pass** (`npm test`, `pytest`, `flutter test`)
5. **Run linters** (`npm run lint`, `ruff check`, `flutter analyze`)
6. **Update documentation** if needed
7. **Submit PR** with clear description linking to issue

### PR Requirements
- [ ] All CI checks pass
- [ ] Code coverage ≥ 80% for new code
- [ ] Documentation updated
- [ ] No breaking changes without ADR
- [ ] Safety review for AI-related changes
- [ ] Privacy impact assessment for data changes

---

## Coding Standards

### General Principles
- **Readability over cleverness** — Code is read more than written
- **Explicit over implicit** — Avoid magic, prefer clarity
- **Safety first** — Especially for AI, memory, and user data
- **Consistency** — Follow existing patterns in the codebase

### Language-Specific Standards

#### TypeScript/Node.js (Backend)
- Follow `docs/04-engineering/420-coding-standard.md`
- Use strict TypeScript config
- ESLint + Prettier enforced
- Async/await over promises
- Zod for validation

#### Python (AI Runtime)
- Follow `docs/04-engineering/420-coding-standard.md`
- Ruff for linting, Black for formatting
- Type hints required (mypy strict)
- Pydantic for data models
- Structured logging (structlog)

#### Dart/Flutter (Mobile)
- Follow `docs/04-engineering/420-coding-standard.md`
- Very Good Analysis rules
- Bloc/Cubit for state management
- Repository pattern for data layer
- Golden tests for UI

---

## Testing Strategy

### Test Pyramid
```
         /\
        /  \     E2E Tests (Critical user journeys)
       /____\
      /      \   Integration Tests (Engine interactions)
     /________\
    /          \ Unit Tests (Pure functions, business logic)
   /____________\
```

### Requirements
- **Unit tests**: ≥ 90% coverage for core engines
- **Integration tests**: All engine interfaces
- **E2E tests**: Critical user flows (onboarding, conversation, memory recall)
- **Contract tests**: API contracts between services
- **Chaos tests**: Memory corruption, network partitions, LLM failures

---

## Documentation Standards

### LPDS (Lumina Product Documentation System)
All documentation follows the structure in `docs/`:

| Category | Prefix | Purpose |
|----------|--------|---------|
| Foundation | 000-099 | Constitution, vision, principles |
| Product | 100-199 | PRD, personas, journeys, features |
| AI | 200-299 | Engine specs, safety, prompts |
| Architecture | 300-399 | System, mobile, backend, memory, voice, avatar, deployment |
| Engineering | 400-499 | Roadmap, workflow, standards, testing, release, DevOps |
| Business | 500-599 | Model, pricing, GTM, marketing, finance, investment |
| Legal | 600-699 | Privacy, ethics, grief policy, compliance |
| ADR | 700-799 | Architecture Decision Records |
| RFC | 800-899 | Request for Comments |

### Writing Guidelines
- Use clear, concise language
- Include diagrams (Mermaid) where helpful
- Keep documents focused and modular
- Cross-reference related documents
- Update `CHANGELOG.md` for significant changes

---

## AI Safety & Ethics Review

### Mandatory Reviews For
- Changes to Identity Engine (personality, values, boundaries)
- Changes to Memory Engine (storage, retrieval, forgetting)
- Changes to Relationship Engine (trust, intimacy, attachment metrics)
- Changes to Emotion Engine (detection, response, empathy)
- New companion types or capabilities
- Data collection or processing changes

### Review Process
1. Create PR with `safety-review` label
2. Assigned to AI Safety reviewers
3. Risk assessment completed
4. Mitigation plan documented
5. Approval required before merge

### Safety Principles (from FOUNDATION.md)
- PAO acknowledges it is AI
- PAO does not replace human relationships
- PAO does not manipulate emotions
- PAO does not encourage dependency
- Reality Anchor is mandatory
- Grief Policy enforced
- Privacy is paramount

---

## Privacy & Security

### Data Handling
- User data = user property
- Minimal data collection
- End-to-end encryption for sensitive data
- Local-first architecture where possible
- Right to export/delete (GDPR/CCPA compliant)

### Security Requirements
- All dependencies scanned (Dependabot, Snyk)
- Secrets management (Vault/Sealed Secrets)
- Regular penetration testing
- Incident response plan documented

---

## Release Process

See `docs/04-engineering/440-release-process.md` for detailed process.

### Version Types
- **Major**: Breaking engine changes, safety principle changes
- **Minor**: New features, companion types, capabilities
- **Patch**: Bug fixes, docs, minor improvements

### Release Checklist
- [ ] All tests pass
- [ ] Security scan clean
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Migration scripts ready (if needed)
- [ ] Rollback plan documented
- [ ] Stakeholder sign-off

---

## RFC Process

For significant changes, follow the RFC process in `docs/08-rfc/`:

1. **Draft** — Create RFC from template
2. **Discuss** — 2-week comment period
3. **Decide** — Core team decision (accept/reject/defer)
4. **Implement** — Linked PRs with RFC reference
5. **Review** — Post-implementation review

RFC required for:
- New engines or major engine changes
- New companion types
- Architecture changes
- Data model changes
- Safety/privacy policy changes

---

## ADR Process

Architecture Decision Records in `docs/07-adr/`:

1. Create ADR from template
2. Document context, decision, consequences
3. Link from related PRs and docs
4. Mark as Accepted/Superseded/Deprecated

---

## Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` (all contributors)
- Release notes (significant contributions)
- Hall of Fame (long-term contributors)

---

## Questions?

- **General**: Open a GitHub Discussion
- **Bugs**: GitHub Issues with bug template
- **Features**: GitHub Issues with feature template or RFC
- **Security**: security@pao.ai (private disclosure)
- **AI Safety**: safety@pao.ai

---

## License

By contributing, you agree that your contributions will be licensed under the project's [LICENSE](LICENSE).

---

*PAO is built on trust. Every contribution should strengthen the four foundations: Identity, Memory, Relationship, Emotion.*