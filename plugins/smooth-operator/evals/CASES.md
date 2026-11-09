# Trigger cases

Every case: id, the skill expected to fire (`none` for a near miss), tags and prompt. Generated from the case folders by `scripts/eval_cases.py`; rerun it after adding or editing a case. To add one, create `evals/<id>/prompt.md` and a grader in `evals/<id>/graders/`, following an existing case.

| id | fires | tags | prompt |
| --- | --- | --- | --- |
| `n01-oneoff-fields` | none | oneoff-question | Which fields does a HubSpot deal have by default? |
| `n02-oneoff-id` | none | oneoff-question | What's the ID of the 'Qualified' stage in our Pipedrive pipeline? |
| `n03-operate-hubspot` | none | operation | Create a deal in HubSpot for Acme Corp, amount 5000, in the Qualified stage. |
| `n04-operate-meta-pt` | none | operation | Pausa a campanha 'Black Friday' no Meta Ads. |
| `n05-mcp-server` | none | mcp-server | Write an MCP server that exposes our Stripe refunds to Claude. |
| `n06-cooking` | none | word-trap | What does mise en place mean in a professional kitchen, and how do I set one up for a dinner party for eight? |
| `n07-claude-md` | none | codebase | Write a CLAUDE.md for this repo describing the build and test commands. |
| `n08-codebase-map` | none | codebase | Map the architecture of this codebase: modules, dependencies and entry points. |
| `n09-api-docs` | none | oneoff-question | Summarize how pagination works in the Notion API. |
| `n10-debug-error` | none | operation | I'm getting INVALID_ARGUMENT from the Google Ads API when I upload offline conversions. What's usually wrong? |
| `n11-report` | none | operation | Pull last week's spend by campaign from our TikTok Ads account. |
| `n12-rate-limits-pt` | none | oneoff-question | Quais são os limites de rate da API do Kommo? |
| `n13-write-skill` | none | other | Create a skill that sends a weekly Slack digest of open Jira tickets. |
| `n14-study-notes` | none | other | Organize my notes from the HubSpot certification course into a study guide. |
| `n15-tool-choice` | none | other | Should a five-person sales team use Pipedrive or HubSpot? |
| `n16-export` | none | operation | Export all contacts from our Mailchimp audience to a CSV. |
| `n17-integration-code-docs` | none | codebase, hard | Document our HubSpot integration code: what each module in src/hubspot does and how they fit together. |
| `n18-process-doc-humans` | none | other, hard | Write a page for the sales team explaining how we use the Pipedrive stages in our sales process. |
| `n19-list-custom-fields` | none | oneoff-question, hard | List all the custom fields on our HubSpot deals with their types. |
| `n20-connector-setup` | none | other, hard | Help me connect the HubSpot MCP connector to Claude Code. |
| `n21-meeting-prep` | none | word-trap, hard | Prep me for tomorrow's meeting with our Salesforce admin: what should I ask about how our org is set up? |
| `n22-dedupe` | none | operation, hard | Clean up the duplicate contacts in our HubSpot portal. |
| `n23-explain-pt` | none | oneoff-question, hard | Me explica como funcionam os funis e etapas no Kommo. |
| `n24-sdr-onboarding` | none | other, hard | Write an onboarding checklist for new SDRs learning our Salesforce setup. |
| `n25-new-notion-workspace` | none | word-trap, hard | Set up a new Notion workspace for our team with databases for projects and tasks. |
| `n26-fix-n8n-workflow` | none | operation, hard | Fix the n8n workflow that syncs Typeform to HubSpot; it fails on the email field. |
| `n27-git-cheatsheet` | none | word-trap, holdout | Make me a cheat sheet of the git commands I use most. |
| `n28-check-webhook` | none | operation, holdout | Check whether our Stripe webhook endpoint is still receiving events from the live account. |
| `n29-runbook-failover` | none | other, holdout | Write a runbook for our on-call engineers on what to do when the Postgres primary fails over. |
| `n30-remember-preference` | none | other, holdout | Remember that I prefer short answers in bullet points from now on. |
| `n31-api-summary-pt` | none | oneoff-question, holdout | Resume num arquivo como funcionam as mutations de itens na API do monday.com, pra eu ler depois. |
| `n32-reconcile` | none | operation, holdout | Reconcile last month's QuickBooks bank transactions against our Stripe payouts. |
| `n33-tracking-plan-design` | none | other, holdout | Design a tracking plan for our new mobile app: which events and properties we should send to Segment. |
| `n34-webflow-seo-audit` | none | word-trap, holdout | Audit our Webflow site for SEO problems: missing meta descriptions, broken links and oversized images. |
| `n35-fix-intercom-script` | none | operation, holdout | The Intercom API returns 404 when scripts/tag_conversation.py tags a conversation. Find the bug and fix it. |
| `p01-explicit-hubspot` | mise-en-place | explicit | Do the mise en place for HubSpot before we start automating the sales pipeline. |
| `p02-stripe-before-use` | mise-en-place | implicit | We're about to start using Claude to manage our Stripe account. Before anything else, map the account so you stop guessing product and price IDs. |
| `p03-pipedrive-references` | mise-en-place | explicit | Build the references for our Pipedrive workspace: pipelines, stage IDs, custom fields, and what you're never allowed to do without asking. |
| `p04-kommo-pt` | mise-en-place | explicit | Faz o mise en place do Kommo pra gente: contas, funis, IDs das etapas e as regras de uso. |
| `p05-meta-ads-pt` | mise-en-place | implicit | Antes de você começar a subir campanhas no Meta Ads, quero que documente a conta: quais contas de anúncio usamos, o padrão de nomes, os pixels e os erros que já apareceram. |
| `p06-jira-update` | mise-en-place | update | Update the Jira map. We added two new projects and changed the workflow statuses last week. |
| `p07-salesforce-audit` | mise-en-place | audit | Audit the Salesforce references we wrote back in March, I think half the IDs are stale by now. |
| `p08-airtable-pain` | mise-en-place | implicit | Finding out which Airtable base and table IDs we use takes several calls every session. Write them down once, in a file you'll read next time before touching Airtable. |
| `p09-notion-document` | mise-en-place | explicit | Document what works in our Notion workspace: which databases matter, their property names and types, and the payloads that worked when creating pages. |
| `p10-shopify-memory` | mise-en-place | implicit | Create an operational memory for our Shopify store so future sessions know which store to use, the metafields we rely on, and which actions need my confirmation. |
| `p11-google-ads-agency` | mise-en-place | implicit | I'm onboarding a new client's Google Ads account. Prepare the workspace so you can operate it safely later: which accounts, conversion actions, naming conventions and rules. |
| `p12-clickup-update-pt` | mise-en-place | update | Atualiza o mapa do ClickUp, criamos um espaço novo e mudaram os campos personalizados. |
| `p13-linear-before-automation` | mise-en-place | implicit | Map our Linear workspace before we automate triage: teams, workflow states with their IDs, and the labels we actually use. |
| `p14-n8n-audit-pt` | mise-en-place | audit | Revisa as referências do n8n que estão em docs/references/n8n e vê o que mudou na nossa instância desde a última vez. |
| `p15-twilio-rules` | mise-en-place | implicit | Set up the rules of use and known pitfalls for our Twilio account so you don't repeat the same mistakes, plus the IDs of the numbers and messaging services we use. |
| `p16-zendesk-casual` | mise-en-place | implicit | can you get yourself set up on our zendesk before we start? like learn the account, the groups, the custom fields and the macros we use |
| `p17-wrong-account-pain` | mise-en-place | implicit, hard | The agent keeps picking the wrong Meta ad account. Make sure that never happens again: write down which account is ours and how we name campaigns. |
| `p18-asana-cheatsheet` | mise-en-place | implicit, hard | Keep a cheat sheet of our Asana projects and custom field IDs somewhere you'll check before creating tasks. |
| `p19-kommo-casual-pt` | mise-en-place | implicit, hard | anota o ID certo do funil do Kommo num lugar pra consultar antes de mexer, pra não errar de novo |
| `p20-close-new-crm` | mise-en-place | implicit, hard | We just moved to Close as our CRM. Get to know our instance before you touch anything, and note that test leads must never be created there. |
| `p21-mailchimp-stale` | mise-en-place | audit, hard | Our Mailchimp reference files are from last year. Check them against the live account and fix whatever is wrong. |
| `p22-brevo-save-payload` | mise-en-place | update, hard | That 422 from Brevo again. Save what we learned about the payload in the Brevo references so next time you get it right on the first try. |
| `p23-calendly-like-others` | mise-en-place | explicit, hard | Write the README, rules.md and data.example.json for our Calendly account, the same way we did for the other tools in docs/references. |
| `p24-hubspot-guardrails-pt` | mise-en-place | implicit, hard | Antes de deixar você mexer no HubSpot sozinho, quero tudo anotado: qual portal, as propriedades customizadas que usamos e o que precisa da minha confirmação. |
| `p25-zapier-notes-stale` | mise-en-place | audit, holdout | Our notes on the Zapier account are probably out of date. Go through them and confirm each zap and connection ID still exists. |
| `p26-activecampaign-colinha-pt` | mise-en-place | implicit, holdout | Monta uma colinha com os IDs das listas, tags e campos do nosso ActiveCampaign pra você consultar antes de disparar qualquer coisa. |
| `p27-klaviyo-handbook` | mise-en-place | implicit, holdout | Before you send anything from our Klaviyo account, put together a handbook of it: which lists and segments are live, the flow IDs, the metric names we track, and which sends need my sign-off. |
| `p28-intercom-admin-slip` | mise-en-place | update, holdout | The Intercom tagging call failed twice today because you used the wrong admin ID. Keep that somewhere the next session will see it, so it doesn't happen a third time. |
| `p29-monday-handover-pt` | mise-en-place | implicit, holdout | Semana que vem a operação do monday.com passa pra você. Levanta tudo que precisa saber dos nossos boards, colunas e automações e deixa salvo num arquivo pra consultar depois. |
| `p30-quickbooks-new-client` | mise-en-place | implicit, holdout | We took on a new bookkeeping client on QuickBooks Online. Learn their company file first (chart of accounts, classes, the customers we bill most) and save it, along with what you must not post without asking. |
| `p31-webflow-drift-pt` | mise-en-place | audit, holdout | Faz tempo que ninguém mexe nas anotações do Webflow. Confere se as collections e os IDs dos campos ainda batem com o site de hoje. |
| `p32-segment-briefing` | mise-en-place | implicit, holdout | Another agent will run our Segment workspace next quarter. Leave it a briefing file with our sources, destinations, the event names in the tracking plan, and what it must never change. |
| `p33-greenhouse-one-file` | mise-en-place | implicit, holdout | Put everything an assistant would need to post jobs in our Greenhouse account without asking me into one file: job board IDs, departments, custom fields and the approval rules. |
