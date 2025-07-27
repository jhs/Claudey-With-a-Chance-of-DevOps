# Claudey With a Chance of DevOps

Claudey With a Chance of DevOps ("CWCD") is a DevOps assistant powered by Claude Code. Say what you want. Claude Code will build and deploy it.

At this moment it is also vaporware.

## Is CWCD "Vibes DevOps"?

Yes, Claudey With a Chance of DevOps is vibes DevOps if and only if you believe that compared to coding, DevOps is a more serious domain with more serious decisions and consequences, and that the tooling should reflect that. CWCD enforces best practices rather than just suggesting them.

## Architecture: Policy-Driven DevOps

CWCD implements a **policy-driven DevOps** model where organizational standards and best practices are enforced, not suggested.

### Core Components

**Apache Answer as Policy Engine**: Apache Answer serves as the single source of truth for organizational DevOps policies. It contains:
- Tech stack requirements (cloud platform, IaC tools, programming languages)
- Operational standards (backup/restore, disaster recovery, monitoring)
- Compliance requirements and patterns
- Organizational decision history and rationale

**Policy-First Enforcement**: When conflicts arise between Claude's general DevOps knowledge and organizational policies in Apache Answer, **Apache Answer always wins**. Claude will escalate to the user rather than override established policies.

**Progressive Enforcement Model**:
- **New Projects**: Day-1 full policy enforcement from project initialization
- **Existing Projects**: Selective assistance respecting current state while guiding toward compliance
- **Initialization Phase**: Similar to Claude Code's `/init`, CWCD has a discovery phase to understand project context and applicable policies

### Knowledge Evolution

Apache Answer captures decisions, rationale, and outcomes as the system operates, building institutional DevOps memory. Organizations can:
- Update policies directly in Apache Answer
- Refine policies through conversational alignment with Claude
- Share/fork policy datasets across teams or organizations
- Build community-driven "DevOps constitutions" for different contexts (startup, enterprise, regulated industries)

# Whiteboard

- Eject
- Maybe seed a workbook or something to eject vibes.diy
- Testing
- D-R out of the box, tested
- Undecided: Copy the claude model, i.e. boot up in a folder, help maintain that repo.
- Docker - runs in a container? Can run containers? Can pull containers?
- Apache Answer
- Possibly Atomic Agents as the persona, depends how easily it works with Magentic-UI and how useful both Magentic-UI and Atomic Agents are
- Unknown whether RAGFlow adds value (e.g. as a MCP resource to DEERFlow to aggregate/integrate Apache Answers?)
- Maybe an ingestion step like claude does, just read-only learning the ropes, the environment, the context
- Maybe part of using or forking is seeding/pruning the knowledge base with opinions and mandatory requirements. Default KB seed might be mandatory site policy:
  - Must have DR. All DR must be tested regularly.
  - Must have backup and restore. All backups must be tested regularly.
  - Must use AWS/Azure/GCP/etc
  - Must use IaC, e.g. terraform
  - Primary programming language, primary tech stack, etc.
- Maybe use this project to dogfood a public registry/KB that people's CWCD can use
