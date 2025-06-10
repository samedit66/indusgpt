if [ ! -d data ]; then
  mkdir data
  touch ./data/bot.log
fi

docker compose up --build --watch
