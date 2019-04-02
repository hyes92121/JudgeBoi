docker-compose down
unzip dist.zip
cp -r dist/JudgeBoi/. nginx/my-site/
docker-compose up --scale torchnet=10 -d
rm -f dist.zip
rm -rf dist/
