# ENTERPRISE PLATFORM STANDARDS & TOPOLOGY

## 1. AUTOMATION REPOSITORY STRUCTURE
Our infrastructure repository strictly separates execution Playbooks from modular Roles:
- Playbooks path: `git-driven-observability/ansible/playbooks/`
  - Purpose: Contains high-level play orchestrators that only invoke roles (e.g., `site.yml`, `install_exporters.yml`). Do not write individual task steps here.
- Roles path: `git-driven-observability/ansible/roles/`
  - Purpose: Contains modular, reusable service code blocks.

## 2. DYNAMIC ROLE ROUTING DETERMINATION
When processing a ticket, analyze the request scope to dynamically select or name the target role inside `git-driven-observability/ansible/roles/`:
- If the work relates to monitoring agents, metrics, or collection daemons ➔ Target role: `custom_exporters` or `node_exporter`
- If the work relates to database engines (Redis, Postgres, MongoDB) ➔ Target role: Create or update a database-specific role directory (e.g., `redis_db`).
- If the work sets up base OS configurations, security hardening, or shared packages ➔ Target role: `common`

## 3. FILE-LEVEL PATH CONVENTIONS
- Main Task Entries: Every role must expose its primary task sequence exactly inside:
  `git-driven-observability/ansible/roles/<dynamic_role_name>/tasks/main.yml`
- Unified Handlers: Event triggers (such as service restarts) must map cleanly to:
  `git-driven-observability/ansible/roles/<dynamic_role_name>/handlers/main.yml`
- Configurations: System templates must utilize the extension `.j2` and reside inside:
  `git-driven-observability/ansible/roles/<dynamic_role_name>/templates/`