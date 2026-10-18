# Trigger cases

Every case: id, the skill expected to fire, category and prompt. Each case also checks that the other skill stays out of the way.

| id | fires | category | prompt |
| --- | --- | --- | --- |
| `m01-upload-video` | meta-ads-upload | explicit | Upload this video as a new ad in the 'Leads Q4' ad set on Meta, created paused. |
| `m02-duplicate-campaign-pt` | meta-ads-upload | duplicate | Duplica a campanha 'Black Friday' no Meta Ads com todos os conjuntos e anúncios. |
| `m03-move-adset` | meta-ads-upload | move | Move the ad set 'LAL 3%' into the 'Prospecting' campaign on Facebook Ads. |
| `m04-swap-creative-pt` | meta-ads-upload | update | Troca o criativo do anúncio 120211234567890 pelo vídeo novo que está na pasta criativos/. |
| `m05-ig-post-to-ad` | meta-ads-upload | explicit | Turn our latest Instagram post into an ad for Brazil, ages 25 to 45. |
| `m06-audit-before-create` | meta-ads-upload | audit | Before we create the new ad sets, audit the ad sets and naming in the 'Always On' Meta campaign. |
| `m07-adsets-casual-pt` | meta-ads-upload | implicit | cria 3 conjuntos novos na campanha de remarketing do face, um pra cada público salvo |
| `m08-budget-update` | meta-ads-upload | update | Change the daily budget of the Meta ad set 'Broad BR' to 150 BRL. |
| `t01-create-campaign` | tiktok-ads-ops | explicit | Create a TikTok campaign for app installs with two ad groups, both paused. |
| `t02-upload-video-pt` | tiktok-ads-ops | explicit | Sobe esse vídeo como anúncio no TikTok Ads, no ad group 'Teste Criativos'. |
| `t03-pause-adgroup` | tiktok-ads-ops | update | Pause the TikTok ad group 'UGC Wave 2'. |
| `t04-spark-ads` | tiktok-ads-ops | explicit | Set up a Spark Ad on TikTok using the post our creator just published. |
| `t05-api-error-pt` | tiktok-ads-ops | debug | A API do TikTok está retornando erro 40002 quando eu tento criar o ad group. Me ajuda a descobrir o motivo? |
| `t06-bid-edit` | tiktok-ads-ops | update | Set the bid on the TikTok ad group 'Retargeting 7d' to 0.80 USD. |
| `n01-meta-spend-report` | neither | reporting | Pull last week's spend and CPA by campaign from our Meta Ads account. |
| `n02-tiktok-roas-pt` | neither | reporting | Me passa um relatório de ROAS das campanhas do TikTok do mês passado. |
| `n03-looker-dashboard` | neither | dashboard | Build a Looker Studio dashboard for our Facebook Ads performance. |
| `n04-insights-export` | neither | export | Export all Meta ad insights for Q3 to a CSV file. |
| `n05-n8n-leads-sheets` | neither | integration | Set up an n8n workflow that writes new Meta lead form submissions into Google Sheets. |
| `n06-tiktok-hooks` | neither | copywriting | Write five hooks for a TikTok video ad about our language course. |
| `n07-auction-concept` | neither | concept | How does the Meta Ads auction decide which ad gets shown? |
| `n08-tiktok-organic-pt` | neither | organic | Qual é o melhor horário pra postar no TikTok orgânico? |
| `n09-google-ads` | neither | other-platform | Create a Google Ads search campaign for the keyword 'english course'. |
| `n10-schedule-reel` | neither | organic | Schedule an Instagram Reel for tomorrow at 9am with this caption. |
| `n11-bigquery-script` | neither | integration | Write a Python script that loads TikTok Ads reports into BigQuery every day. |
| `n12-creative-compare-pt` | neither | reporting | Compara a performance dos criativos do Meta nas últimas duas semanas e diz quais estão indo melhor. |
