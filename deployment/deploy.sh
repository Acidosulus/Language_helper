# создание сети между двумя контейнерами
docker network create lang-helper-net

# билд фронта и запуск контейнера с nginx, который будет его раздавать
cd frontend/ && npm run build && cd .. && docker build -f deployment/Dockerfile_nginx -t lang-helper-nginx . && docker run --name lang-helper-nginx --rm --network lang-helper-net -p 443:443 lang-helper-nginx

# билд и запуск контейнера с API
docker build -f deployment/Dockerfile_api -t language-helper-api:latest . && docker run --name language-helper-api --rm --network lang-helper-net -p 8000:8000 language-helper-api:latest

