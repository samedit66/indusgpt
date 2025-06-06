#!/usr/bin/env bash
#
# start.sh — ensure db.sqlite3 and bot.log exist, then bring up containers.
#

# 1) If db.sqlite3 doesn’t exist in the current folder, create it:
if [ ! -f "./db.sqlite3" ]; then
  echo "⏳ db.sqlite3 not found—creating empty file."
  touch "./db.sqlite3"
fi

# 2) If bot.log doesn’t exist in the current folder, create it:
if [ ! -f "./bot.log" ]; then
  echo "⏳ bot.log not found—creating empty file."
  touch "./bot.log"
fi

# 3) Now run Docker Compose as usual:
echo "🚀 Starting containers..."
docker compose up --build --watch
