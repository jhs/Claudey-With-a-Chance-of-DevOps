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
- Undecided: Copy the claude model, i.e. boot up in a folder, help maintain that repo. Is that compatible with an invisible/transparent master repo that uses git submodules?
- For now the user will be called the Product Owner (PO) to evoke that Agile role however actual users are more likely to be developers, etc.
- Docker - runs in a container? Can run containers? Can pull containers?
- Apache Answer
- Maybe CWCD operates out of a main "minimal monorepo" with a CLAUDE.md and it uses git submodules to actually interface with e.g. a team's GH repos, docker repos, etc.
- Possibly Atomic Agents as the persona, depends how easily it works with Magentic-UI and how useful both Magentic-UI and Atomic Agents are
- Unknown whether RAGFlow adds value (e.g. as a MCP resource to DEERFlow to aggregate/integrate Apache Answers?)
- Maybe an ingestion step like claude does, just read-only learning the ropes, the environment, the context
- Maybe part of using or forking is seeding/pruning the knowledge base with opinions and mandatory requirements. Default KB seed might be mandatory site policy:
  - Must have DR. All DR must be tested regularly.
  - Must have backup and restore. All backups must be tested regularly.
  - Must use AWS/Azure/GCP/etc
  - Data processing? Data engineering? Databricks vs. cloud native
  - Dev/prod/staging
  - Bronze/Silver/gold data
  - Backend is language/stack A, front-end is language/stack B.
  - Must use IaC, e.g. terraform
  - Testing
  - Primary programming language, primary tech stack, etc.
  - ADRs
- Maybe during "boot" ask the user if they want to discuss any tech opinions or use the defaults. If they discuss then it updates the KB accordingly, e.g. Docker shop, SoftLayer shop
- Need to decide if it's in scope to hook it into your GH, your Jira, Confluence, so it can learn everything. I think the answer is no for now. That is effectively either buiding a KB importer and/or building a KB out of existing GH, Jira, etc.
- Maybe use this project to dogfood a public registry/KB that people's CWCD can use
- KB answers tagged "Policy" must be obeyed completely and all "Policy" knowledge which applies must be obeyed. KB answers not tagged "Policy" are advisory with thumbs up counts indicating real-world endorsements and thumbs-down real-world failures.
- Maybe zen-mcp-server wrapped by Claude to help plan stuff, perhaps in [plan permissions mode](https://docs.anthropic.com/en/docs/claude-code/iam#permission-modes). Maybe it is a resource of DEERFlow, or of the agent. Perhaps unrelated to running claude to execute the commands, just using CC to call zen for research.
- Running Claude Code
  - Possibly an Atomic Agent or Autogen wrapper around it. CC is not a "member of the team" but rather part of the "brain" of the system
  - Maybe use the [MCP permissions system](https://docs.anthropic.com/en/docs/claude-code/cli-reference)
- I feel like at some point, controlling the repo behind Claude Code's back as it were, and probably controlling CC's state, will happen. Most likely example is updating the CLAUDE.md file. or edit the [claude settings](https://docs.anthropic.com/en/docs/claude-code/settings)
- TODO: Go through all of [Claude Code hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) and see where it should connect. (e.g. MCP)

Claude Code SDK
- There is a CLI, TypeScript, and Python SDK. It seems there is parity but not confirmed.
- [Custom system prompts](https://docs.anthropic.com/en/docs/claude-code/sdk#custom-system-prompts)
- [Custom permission prompt](https://docs.anthropic.com/en/docs/claude-code/sdk#custom-permission-prompt-tool) maybe pipe back into Magentic?
- Feels like session management will be big

MCP
- Identify any mcp servers if any that either could are have been reported to help CC. (Memory? etc)

Debugging
- Unclear if LangGraph's audit/rewind advantages fit in here. I think it requires embracing LangGraph as opposed to Atomic Agents which is on the table
- Maybe LightLLM LLM gateway running audits on everything

Experiment to use CC to help on policy:
1. Output all policy as Markdown into CLAUDE.md with article IDs
2. Tell Claude that CLAUDE.md is obsolete. It needs updating by exploring the real codebase
3. Force it to maintain the article IDs consistently, tombstone them, etc.
4. Use an LLM, Agent, whatever to structure that for the PO to approve then sync to the KB
