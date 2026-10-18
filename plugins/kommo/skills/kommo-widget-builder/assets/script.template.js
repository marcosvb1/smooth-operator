define(['jquery'], function ($) {
  var CustomWidget = function () {
    var self = this;

    // API base = Cloudflare Worker (holds the integration token server-side and
    // proxies only sources + pipelines). The admin session can't hit
    // /api/v4/sources directly ("Only integrations can access this endpoint").
    var API_BASE = 'https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/k';

    // --- API helper (goes through the token proxy) ---
    function api(method, path, body) {
      return $.ajax({
        url: API_BASE + path,
        method: method,
        contentType: 'application/json',
        dataType: 'json',
        data: body ? JSON.stringify(body) : undefined,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
    }

    function slug(s) {
      return (s || '')
        .toLowerCase()
        .normalize('NFD').replace(/[̀-ͯ]/g, '')
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/(^-|-$)/g, '')
        .slice(0, 40);
    }

    function esc(s) {
      return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
      });
    }

    function msg(text, ok) {
      $('#fn8n-msg').html(
        '<span style="color:' + (ok ? '#1a9e57' : '#e0463e') + '">' + esc(text) + '</span>'
      );
    }

    function loadPipes() {
      api('GET', '/leads/pipelines')
        .done(function (r) {
          var ps = (r && r._embedded && r._embedded.pipelines) || [];
          $('#fn8n-pipe').html(
            ps.map(function (p) {
              return '<option value="' + p.id + '">' + esc(p.name) + '</option>';
            }).join('')
          );
        })
        .fail(function (x) { msg('Erro ao carregar pipelines: ' + x.status, false); });
    }

    function loadSources() {
      api('GET', '/sources')
        .done(function (r) {
          var ss = (r && r._embedded && r._embedded.sources) || [];
          var rows = ss.map(function (s) {
            return '<tr style="border-bottom:1px solid #eee">' +
              '<td style="padding:8px">' + esc(s.name) + '</td>' +
              '<td style="padding:8px"><code>' + esc(s.external_id) + '</code></td>' +
              '<td style="padding:8px">' + esc(s.pipeline_id) + '</td>' +
              '<td style="padding:8px;text-align:right"><button class="fn8n-del" data-id="' + s.id +
              '" style="color:#e0463e;border:0;background:none;cursor:pointer">excluir</button></td>' +
              '</tr>';
          }).join('');
          $('#fn8n-table').html(
            '<tr style="text-align:left;color:#9aa">' +
            '<th style="padding:8px">Fonte (vira o rótulo)</th><th style="padding:8px">external_id (N8N usa)</th>' +
            '<th style="padding:8px">pipeline</th><th></th></tr>' +
            (rows || '<tr><td colspan="4" style="padding:8px;color:#aaa">Nenhuma fonte ainda.</td></tr>')
          );
          $('.fn8n-del').off('click').on('click', function () { delSource($(this).data('id')); });
        })
        .fail(function (x) {
          msg('Erro ao carregar fontes: ' + x.status + ' ' + (x.responseText || ''), false);
        });
    }

    function addSource() {
      var name = ($('#fn8n-name').val() || '').trim();
      var pid = parseInt($('#fn8n-pipe').val(), 10);
      if (!name) { msg('Digite um nome para a fonte.', false); return; }
      var ext = slug(name);
      api('POST', '/sources', [{ name: name, external_id: ext, pipeline_id: pid }])
        .done(function () {
          msg('Fonte "' + name + '" criada — external_id: ' + ext, true);
          $('#fn8n-name').val('');
          loadSources();
        })
        .fail(function (x) {
          msg('Erro ao criar: ' + x.status + ' ' + (x.responseText || ''), false);
        });
    }

    function delSource(id) {
      api('DELETE', '/sources', [{ id: id }])
        .done(function () { loadSources(); })
        .fail(function (x) { msg('Erro ao excluir: ' + x.status, false); });
    }

    function renderManager(area) {
      area.innerHTML =
        '<div style="padding:16px;font-family:-apple-system,Segoe UI,sans-serif;max-width:820px">' +
        '<h2 style="margin:0 0 4px">Fontes de leads</h2>' +
        '<p style="color:#9aa;margin:0 0 16px">Crie as fontes que o N8N vai usar. O <b>external_id</b> é o que o N8N referencia em <code>_embedded.source</code>.</p>' +
        '<div style="display:flex;gap:8px;margin-bottom:14px">' +
        '<input id="fn8n-name" placeholder="Nome da fonte (ex: Landing Black Friday)" style="flex:2;padding:9px;border:1px solid #ccc;border-radius:6px">' +
        '<select id="fn8n-pipe" style="flex:1;padding:9px;border:1px solid #ccc;border-radius:6px"></select>' +
        '<button id="fn8n-add" style="padding:9px 18px;background:#1a9e57;color:#fff;border:0;border-radius:6px;cursor:pointer">Adicionar</button>' +
        '</div>' +
        '<div id="fn8n-msg" style="min-height:20px;margin-bottom:12px"></div>' +
        '<table style="width:100%;border-collapse:collapse" id="fn8n-table"></table>' +
        '</div>';
      $('#fn8n-add').off('click').on('click', addSource);
      loadPipes();
      loadSources();
    }

    this.callbacks = {
      settings: function () { return true; },
      init: function () { return true; },
      bind_actions: function () { return true; },
      render: function () { return true; },
      dpSettings: function () {},
      advancedSettings: function () {
        var code = self.params && self.params.widget_code;
        var area = document.querySelector('#work-area-' + code);
        console.log('[sources-widget] BUILD=template-v1 API_BASE=' + API_BASE + ' widget_code=', code, 'area found=', !!area);
        if (area) { renderManager(area); }
        return true;
      },
      destroy: function () {},
      onSave: function () { return true; },
      onInstall: function () { return true; },
      onAddAsSource: function (pipeline_id) {
        console.log('[sources-widget] onAddAsSource pipeline_id=', pipeline_id);
        return true;
      }
    };

    return this;
  };

  return CustomWidget;
});
