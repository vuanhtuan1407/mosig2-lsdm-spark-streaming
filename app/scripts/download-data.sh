#!/usr/bin/env bash
set -euo pipefail

BUCKET="gs://clusterdata-2011-2"
LOCAL_DIR="./data/clusterdata-2011-2"

mkdir -p "$LOCAL_DIR"

ROOT_FILES=(MD5SUM SHA1SUM SHA256SUM README schema.csv)
FOLDERS=(job_events machine_attributes machine_events task_constraints task_events task_usage)

for folder in "${FOLDERS[@]}"; do
    mkdir -p "$LOCAL_DIR/$folder"

    FILES=$(gsutil ls "$BUCKET/$folder" 2>/dev/null | grep 'part-.*\.csv\.gz' || true)

    if [ -z "$FILES" ]; then
        echo "No part files found in $folder, skipping."
        continue
    fi

    FILE_COUNT=$(echo "$FILES" | wc -l)

    if [ "$FILE_COUNT" -eq 1 ]; then
        echo "$FILES" | while IFS= read -r f; do
            [ -n "$f" ] || continue
            gsutil cp "$f" "$LOCAL_DIR/$folder/"
            gzip -dk "$LOCAL_DIR/$folder/$(basename "$f")"
        done
    else
        for i in $(seq -f "%05g" 160 164); do
            MATCH=$(echo "$FILES" | grep "part-${i}-of-" || true)
            if [ -n "$MATCH" ]; then
                echo "$MATCH" | while IFS= read -r mf; do
                    [ -n "$mf" ] || continue
                    gsutil cp "$mf" "$LOCAL_DIR/$folder/"
                    gzip -dk "$LOCAL_DIR/$folder/$(basename "$mf")"
                done
            fi
        done
    fi
done

for f in "${ROOT_FILES[@]}"; do
    gsutil cp "$BUCKET/$f" "$LOCAL_DIR/" || true
done

echo "Download and extraction completed."
