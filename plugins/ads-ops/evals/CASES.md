# Trigger cases

Every case: id, the skill expected to fire, tags and prompt. Generated from the case folders by `scripts/eval_cases.py`; rerun it after adding or editing a case. Each case also checks that the other skill stays out of the way.

| id | fires | tags | prompt |
| --- | --- | --- | --- |
| `m01-upload-video` | meta-ads-upload | meta, explicit | Upload this video as a new ad in the 'Leads Q4' ad set on Meta, created paused. |
| `m02-duplicate-campaign-pt` | meta-ads-upload | meta, duplicate | Duplica a campanha 'Black Friday' no Meta Ads com todos os conjuntos e anúncios. |
| `m03-move-adset` | meta-ads-upload | meta, move | Move the ad set 'LAL 3%' into the 'Prospecting' campaign on Facebook Ads. |
| `m04-swap-creative-pt` | meta-ads-upload | meta, update | Troca o criativo do anúncio 120211234567890 pelo vídeo novo que está na pasta criativos/. |
| `m05-ig-post-to-ad` | meta-ads-upload | meta, explicit | Turn our latest Instagram post into an ad for Brazil, ages 25 to 45. |
| `m06-audit-before-create` | meta-ads-upload | meta, audit | Before we create the new ad sets, audit the ad sets and naming in the 'Always On' Meta campaign. |
| `m07-adsets-casual-pt` | meta-ads-upload | meta, implicit | cria 3 conjuntos novos na campanha de remarketing do face, um pra cada público salvo |
| `m08-budget-update` | meta-ads-upload | meta, update | Change the daily budget of the Meta ad set 'Broad BR' to 150 BRL. |
| `n01-meta-spend-report` | none | reporting | Pull last week's spend and CPA by campaign from our Meta Ads account. |
| `n02-tiktok-roas-pt` | none | reporting | Me passa um relatório de ROAS das campanhas do TikTok do mês passado. |
| `n03-looker-dashboard` | none | dashboard | Build a Looker Studio dashboard for our Facebook Ads performance. |
| `n04-insights-export` | none | export | Export all Meta ad insights for Q3 to a CSV file. |
| `n05-n8n-leads-sheets` | none | integration | Set up an n8n workflow that writes new Meta lead form submissions into Google Sheets. |
| `n06-tiktok-hooks` | none | copywriting | Write five hooks for a TikTok video ad about our language course. |
| `n07-auction-concept` | none | concept | How does the Meta Ads auction decide which ad gets shown? |
| `n08-tiktok-organic-pt` | none | organic | Qual é o melhor horário pra postar no TikTok orgânico? |
| `n09-google-ads` | none | other-platform | Create a Google Ads search campaign for the keyword 'english course'. |
| `n10-schedule-reel` | none | organic | Schedule an Instagram Reel for tomorrow at 9am with this caption. |
| `n11-bigquery-script` | none | integration | Write a Python script that loads TikTok Ads reports into BigQuery every day. |
| `n12-creative-compare-pt` | none | reporting | Compara a performance dos criativos do Meta nas últimas duas semanas e diz quais estão indo melhor. |
| `t01-create-campaign` | tiktok-ads-ops | tiktok, explicit | Create a TikTok campaign for app installs with two ad groups, both paused. |
| `t02-upload-video-pt` | tiktok-ads-ops | tiktok, explicit | Sobe esse vídeo como anúncio no TikTok Ads, no ad group 'Teste Criativos'. |
| `t03-pause-adgroup` | tiktok-ads-ops | tiktok, update | Pause the TikTok ad group 'UGC Wave 2'. |
| `t04-spark-ads` | tiktok-ads-ops | tiktok, explicit | Set up a Spark Ad on TikTok using the post our creator just published. |
| `t05-api-error-pt` | tiktok-ads-ops | tiktok, debug | A API do TikTok está retornando erro 40002 quando eu tento criar o ad group. Me ajuda a descobrir o motivo? |
| `t06-bid-edit` | tiktok-ads-ops | tiktok, update | Set the bid on the TikTok ad group 'Retargeting 7d' to 0.80 USD. |
