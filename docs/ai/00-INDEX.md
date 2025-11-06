# AI Documentation Index

This folder contains machine-readable documentation optimized for AI assistants, automation tools, and programmatic access.

## Documentation Organization

### Core Reference

- **[Repository Metadata](00-metadata.json)** - Project metadata in JSON format
- **[Environment Schema](01-environment.json)** - Complete environment variable definitions
- **[Configuration Schema](02-config-schema.json)** - Configuration file schemas

### API Documentation

- **[REST API Spec](10-rest-api.json)** - OpenAPI/Swagger specification
- **[WebSocket Protocol](11-websocket-protocol.json)** - WebSocket message schemas
- **[API Examples](12-api-examples.json)** - Request/response examples

### Data Models

- **[Database Schemas](20-database-schemas.json)** - SQLite and InfluxDB schemas
- **[Pydantic Models](21-pydantic-models.json)** - Python data model definitions
- **[Type Definitions](22-type-definitions.json)** - TypeScript-style type definitions

### Service Interfaces

- **[Discovery Service](30-discovery-service.md)** - Discovery service interface and examples
- **[Identification Service](31-identification-service.md)** - Identification service interface
- **[Monitoring Service](32-monitoring-service.md)** - Monitoring service interface
- **[SNMP Service](33-snmp-service.md)** - SNMP service interface

### Automation

- **[CLI Commands](40-cli-commands.json)** - Command-line interface reference
- **[Task Automation](41-task-examples.md)** - Common automation task examples
- **[CI/CD Integration](42-cicd-integration.md)** - Integration with CI/CD systems

### Code Generation

- **[Service Templates](50-service-templates.md)** - Service code templates
- **[Test Templates](51-test-templates.md)** - Test generation templates
- **[Migration Templates](52-migration-templates.md)** - Database migration templates

---

**Purpose:** This documentation is designed to be parsed and used by:

- AI coding assistants (GitHub Copilot, ChatGPT, Claude, etc.)
- Code generation tools
- Automated testing frameworks
- API clients and SDKs
- Documentation generators
- CI/CD pipelines

**Format Standards:**

- JSON files use JSON Schema where applicable
- Markdown files contain structured code blocks
- All examples are runnable and tested
- Schemas include validation rules and defaults
