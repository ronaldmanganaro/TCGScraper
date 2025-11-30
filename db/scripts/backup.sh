#!/bin/bash

# Create compressed backup
timestamp=$(date +%Y-%m-%d_%H-%M-%S)
outfile="dump_${timestamp}.sql.zst"

docker exec -t TCGPlayerDB pg_dumpall -c -U rmangana | zstd -19 -T0 -o "$outfile"
echo "Backup saved to $outfile"

# Delete backup files older than 7 days
find . -type f -name 'dump_*.sql.zst' -mtime +7 -exec rm {} \;

ubuntu@ec2-prod:~/db_tools$ cat restore.sh
#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <dumpfile.sql.zst>"
  exit 1
fi

zstd -d < "$1" | docker exec -i TCGPlayerDB psql -U rmangana -d postgres
