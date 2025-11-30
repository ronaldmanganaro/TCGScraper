#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <dumpfile.sql.zst>"
  exit 1
fi

zstd -d < "$1" | docker exec -i TCGPlayerDB psql -U rmangana -d postgres
ubuntu@ec2-prod:~/db_tools$ cat restore.sh
#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <dumpfile.sql.zst>"
  exit 1
fi

zstd -d < "$1" | docker exec -i TCGPlayerDB psql -U rmangana -d postgres
