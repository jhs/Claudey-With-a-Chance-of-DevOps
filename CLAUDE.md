# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claudey With a Chance of DevOps (CWCD) is a DevOps assistant powered by Claude Code. This is currently a conceptual project in early development phase with minimal implementation.

## Project Structure

This is a minimal repository containing:
- `README.md` - Project description and whiteboard ideas
- `LICENSE` - Apache License 2.0
- Basic git repository structure

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

**Knowledge Evolution**: Apache Answer captures decisions and outcomes as the system operates, building institutional DevOps memory.

**Policy Updates**: Organizations can refine policies either:
- Directly in Apache Answer
- Through conversational alignment with Claude (which then updates Apache Answer)

## Development Context

This project is in the conceptual/planning phase with minimal implementation. Key components under consideration:
- Container support (Docker)
- Apache Answer integration as policy engine
- Atomic Agents and Magentic-UI for specialized DevOps personas
- RAGFlow for knowledge aggregation
- Infrastructure as Code enforcement (Terraform)

## Current State

No build tools, dependencies, or implementation code present yet.

## Key Design Principles

- **Enforcement over Suggestion**: CWCD enforces best practices rather than suggesting them
- **Policy-First**: Organizational policies in Apache Answer override general DevOps advice
- **Institutional Memory**: Capture and evolve organizational DevOps knowledge over time
- **Progressive Adoption**: Support both greenfield projects (full enforcement) and brownfield projects (guided compliance)