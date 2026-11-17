> **lean-marketing** is a connector-free fork of Anthropic's `marketing` plugin. It ships no `.mcp.json`; the `~~category` placeholders resolve to whatever connectors you already have enabled. See NOTICE.

# Connectors

## How tool references work

Plugin files use `~~category` as a placeholder for whatever tool the user connects in that category. For example, `~~marketing automation` might mean HubSpot, Marketo, or any other marketing platform with an MCP server.

Plugins are **tool-agnostic** — they describe workflows in terms of categories (design, SEO, email marketing, etc.) rather than specific products. This fork bundles no MCP servers; any connector you have in that category works.

## Connectors for this plugin

| Category | Placeholder | Examples | Other options |
|----------|-------------|-----------------|---------------|
| Chat | `~~chat` | Slack | Microsoft Teams |
| Design | `~~design` | Canva, Figma | Adobe Creative Cloud |
| Marketing automation | `~~marketing automation` | HubSpot | Marketo, Pardot, Mailchimp |
| Product analytics | `~~product analytics` | Amplitude | Mixpanel, Google Analytics |
| Knowledge base | `~~knowledge base` | Notion | Confluence, Guru |
| SEO | `~~SEO` | Ahrefs, Similarweb | Semrush, Moz |
| Email marketing | `~~email marketing` | Klaviyo | Mailchimp, Brevo, Customer.io |
| Marketing analytics | `~~marketing analytics` | Supermetrics | Google Analytics, Mailchimp, Semrush |
