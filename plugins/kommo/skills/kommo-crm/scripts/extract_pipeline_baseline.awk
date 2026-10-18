# Emit the last Markdown table with columns `sort | id | nome` as id|name|sort.
# Later live snapshots supersede historical tables earlier in the same document.
/^\| sort \| id \| nome( \||$)/ {
  in_table=1
  count=0
  for (key in rows) delete rows[key]
  next
}

in_table && /^\|[-: ]+\|/ { next }

in_table && /^\| [0-9]+ \| [0-9]+ \|/ {
  gsub(/^\| /, "")
  gsub(/ \|$/, "")
  n = split($0, fields, /\|/)
  if (n >= 3) {
    gsub(/^ +| +$/, "", fields[1])
    gsub(/^ +| +$/, "", fields[2])
    gsub(/^ +| +$/, "", fields[3])
    rows[++count] = fields[2] "|" fields[3] "|" fields[1]
  }
  next
}

in_table && !/^\|/ { in_table=0 }

END {
  for (i=1; i<=count; i++) print rows[i]
}
