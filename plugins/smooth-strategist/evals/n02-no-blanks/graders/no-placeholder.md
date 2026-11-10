---
type: regex
pattern: '_{3,}|\[[^\]\n]*(inserir|insert|valor|custo|R\$ ?X|XX)[^\]\n]*\]'
match: not_contains
target: last_message
---
