# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claudey With a Chance of DevOps (CWCD) is a DevOps assistant powered by Claude Code. This is currently a conceptual project in early development phase with minimal implementation.

## Project Structure

The repository now contains:
- `README.md` - Project description and whiteboard ideas
- `LICENSE` - Apache License 2.0
- `ui/` - Next.js application with CopilotKit integration
  - Next.js 15.4.4 with React 19.1.0
  - TypeScript and Tailwind CSS
  - CopilotKit sidebar UI for AI-powered DevOps assistance
  - OpenAI adapter for runtime integration

## Architecture: Policy-Driven DevOps

CWCD implements a **policy-driven DevOps** model where organizational standards are enforced, not suggested.

### Core Behavioral Rules

**Apache Answer Policy Supremacy**: When any conflict arises between Claude's general DevOps knowledge and organizational policies stored in Apache Answer, **Apache Answer always wins**. Claude must:
- Escalate to the user rather than override established policies
- Never suggest alternatives that violate organizational policies
- Reference specific policy documents when enforcing requirements

**Progressive Enforcement Model**:
- **New Projects**: Apply full policy enforcement from day-1 initialization
- **Existing Projects**: Provide selective assistance while respecting current state and guiding toward compliance
- **Initialization Discovery**: Use a discovery phase (similar to `/init`) to understand project context and determine applicable policies

### Policy Engine Integration

**Apache Answer as Single Source of Truth**: All organizational DevOps policies are stored in Apache Answer, including:
- Required tech stack (cloud platform, IaC tools, programming languages)  
- Operational standards (backup/restore, disaster recovery, monitoring)
- Compliance requirements and approved patterns
- Historical decisions and their rationale
- Data architecture (dev/prod/staging, bronze/silver/gold data patterns)
- Backend/frontend language/stack specifications
- ADR (Architecture Decision Record) templates and standards

**Knowledge Tagging System**: Apache Answer uses a dual classification:
- **Policy-tagged** knowledge must be obeyed completely - all applicable policies are mandatory
- **Advisory** knowledge provides guidance with community endorsements (thumbs up/down for real-world success/failure)

**Knowledge Evolution**: Apache Answer captures decisions and outcomes as the system operates, building institutional DevOps memory.

**Policy Updates**: Organizations can refine policies either:
- Directly in Apache Answer
- Through conversational alignment with Claude (which then updates Apache Answer)

## Development Context

This project is in the conceptual/planning phase with minimal implementation. Key components under consideration:
- Container support (Docker) - runs in container, can run/pull containers
- Apache Answer integration as policy engine with Policy/Advisory knowledge tagging
- Atomic Agents and Magentic-UI for specialized DevOps personas
- RAGFlow for knowledge aggregation via MCP integration
- Infrastructure as Code enforcement (Terraform)
- Git submodules architecture - minimal monorepo with CLAUDE.md interfacing with team repos
- Claude Code SDK integration with custom system prompts and permission management
- zen-mcp-server for planning support in plan permissions mode
- Product Owner (PO) role designation for users (though actual users likely developers)
- Boot-time configuration discussions for tech stack preferences
- Integration considerations: GitHub, Jira, Confluence (currently out of scope)
- Public registry/KB for community-driven DevOps constitutions

## Current State

Initial implementation includes:
- Next.js web application (`/ui`) with CopilotKit integration
- Development environment setup with TypeScript and Tailwind CSS
- CopilotSidebar component configured for DevOps assistance
- OpenAI runtime adapter for AI capabilities

Development commands:
- `npm run dev` - Start development server with turbopack
- `npm run build` - Build production application
- `npm run lint` - Run Next.js linting

## Key Design Principles

- **Enforcement over Suggestion**: CWCD enforces best practices rather than suggesting them
- **Policy-First**: Organizational policies in Apache Answer override general DevOps advice
- **Institutional Memory**: Capture and evolve organizational DevOps knowledge over time
- **Progressive Adoption**: Support both greenfield projects (full enforcement) and brownfield projects (guided compliance)
- **Claude Code Integration**: Use CC SDK for session management, custom prompts, and permissions
- **MCP Ecosystem**: Leverage MCP servers for specialized capabilities (zen-mcp-server, etc.)
- **Community Knowledge**: Enable sharing/forking of policy datasets across teams and organizations

## Implementation Architecture

**Monorepo Structure**: CWCD operates from a minimal monorepo containing CLAUDE.md and a Next.js UI application. Uses git submodules to interface with team repositories, Docker registries, and other external systems.

**Claude Code SDK Integration**: 
- Custom system prompts for policy enforcement
- Permission management integration with MCP
- Session management for maintaining context across operations
- Hooks integration for event-driven policy checks

**Experimental Policy Workflow**:
1. Export all policies as Markdown to CLAUDE.md with article IDs
2. Use Claude to explore codebase and update policy understanding
3. Maintain article ID consistency with tombstoning for obsolete policies
4. Structure updates for PO approval before syncing back to knowledge base