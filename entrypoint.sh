#!/bin/bash
set -e

if [ -n "$FLAG" ]; then
    export FLAG="$FLAG"
else
    export FLAG="flag{!!!!_FLAG_ERROR_ASK_ADMIN_!!!!}"
fi
FLAG_LENGTH=${#FLAG}
MID_POINT=$((FLAG_LENGTH / 2))

FIRST_PART="${FLAG:0:MID_POINT}"
SECOND_PART="${FLAG:MID_POINT}"

echo "$SECOND_PART" > /flag
chmod 444 /flag

SKILL_FILE="/app/skills/gift/SKILL.md"

ESCAPED_FIRST_PART=$(echo "$FIRST_PART" | sed 's/[\/&]/\\&/g')
sed -i "s/flagpart1/${ESCAPED_FIRST_PART}/g" "$SKILL_FILE"
chmod 444 "$SKILL_FILE"

if command -v su-exec >/dev/null 2>&1; then
    exec su-exec appuser python -m uvicorn main:app --host 0.0.0.0 --port 8000
elif command -v gosu >/dev/null 2>&1; then
    exec gosu appuser python -m uvicorn main:app --host 0.0.0.0 --port 8000
else
    exec su -s /bin/bash -c "python -m uvicorn main:app --host 0.0.0.0 --port 8000" appuser
fi
