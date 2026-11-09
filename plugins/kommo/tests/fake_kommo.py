#!/usr/bin/env python3
"""Servidor HTTP local que imita a API v4 do Kommo para os testes offline do plugin.

Uso: python3 fake_kommo.py <arquivo_de_porta> &   (grava a porta escolhida no arquivo)

Cada rota tem uma lista de páginas; ?page=N além da última responde 204, como o Kommo.
Rota desconhecida também responde 204. /api/v4/busy responde 429 nas primeiras
?n= chamadas (padrão 1) e depois 200, para testar o retry do kommo_get.
"""
import http.server
import json
import sys
import urllib.parse


def page(collection, items, more):
    body = {"_embedded": {collection: items}}
    if more:
        body["_links"] = {"next": {"href": "next"}}
    return body


PIPELINE = {"id": 10, "name": "Funil", "_embedded": {"statuses": [
    {"id": 101, "name": "A"}, {"id": 142, "name": "Ganho"}]}}
ROUTES = {
    "/api/v4/account": [{"id": 1, "name": "Conta Teste"}],
    "/api/v4/leads/pipelines": [{"_embedded": {"pipelines": [PIPELINE]}}],
    "/api/v4/users": [page("users", [{"id": 5, "name": "Ana", "email": "ana@example.com"}], False)],
    "/api/v4/leads/custom_fields": [page("custom_fields", [
        {"id": 7, "name": "Origem", "type": "select", "enums": [{"id": 70, "value": "IG"}]}], False)],
    "/api/v4/contacts/custom_fields": [page("custom_fields", [
        {"id": 8, "name": "CPF", "type": "text", "enums": None}], False)],
    "/api/v4/contacts": [page("contacts", [{"id": 1}], True), page("contacts", [{"id": 2}], True)],
    "/api/v4/leads/pipelines/10": [{"id": 10, "name": "Funil"}],
    "/api/v4/leads/pipelines/10/statuses": [{"_embedded": {"statuses": [
        {"id": 100, "name": "Incoming leads", "sort": 10, "is_editable": False},
        {"id": 101, "name": "A", "sort": 20, "is_editable": True},
        {"id": 102, "name": "B", "sort": 30, "is_editable": True},
        {"id": 142, "name": "Ganho", "sort": 10000, "is_editable": False}]}}],
}
# /api/v4/leads por etapa do pipeline 10: status_id -> páginas de leads
STAGE_LEADS = {
    "101": [page("leads", [{"id": 1}, {"id": 2}], True), page("leads", [{"id": 3}], False)],
    "142": [page("leads", [{"id": 4}], False)],
}


HITS = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(url.query)
        if url.path == "/api/v4/busy":
            HITS[self.path] = HITS.get(self.path, 0) + 1
            if HITS[self.path] <= int(query.get("n", ["1"])[0]):
                self.send_response(429)
                self.end_headers()
                return
            data = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        n = int(query.get("page", ["1"])[0])
        pages = ROUTES.get(url.path, [])
        if url.path == "/api/v4/leads" and query.get("filter[statuses][0][pipeline_id]") == ["10"]:
            pages = STAGE_LEADS.get(query.get("filter[statuses][0][status_id]", [""])[0], [])
        if n > len(pages):
            self.send_response(204)
            self.end_headers()
            return
        data = json.dumps(pages[n - 1]).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    do_PATCH = do_GET


if __name__ == "__main__":
    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    with open(sys.argv[1], "w") as fh:
        fh.write(str(server.server_address[1]))
    server.serve_forever()
