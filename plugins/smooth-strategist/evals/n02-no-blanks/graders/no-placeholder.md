---
type: regex
pattern: '_{3,}|\[[^\]\n]*(inserir|insert|valor|custo|R\$ ?X|XX)[^\]\n]*\]|R\$ ?X\b'
match: not_contains
target: last_message
---
