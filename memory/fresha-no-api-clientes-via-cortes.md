---
name: fresha-no-api-clientes-via-cortes
description: Fresha has no public API/MCP; MaruNails client data is built from daily cortes, not imported
metadata:
  type: project
---

Fresha (the salon's booking platform) has **no public API and no MCP** available, so client/booking data cannot be imported programmatically. Decision (2026-07-07): the MaruNails Clientes module (Fase 2) builds each client profile **from the daily cortes** — the client is identified when a corte is loaded and the profile (first/last visit, spend history, etc.) is derived from there. No double data entry, no Fresha integration.

Relates to [[marunails-fase1-reportes]].
