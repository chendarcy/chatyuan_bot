docker rm -f yuan_bot_client

docker build -t python-run:wechaty-ws .

docker run -it -d \
--name yuan_bot_client \
-e WECHATY_PUPPET_SERVICE_ENDPOINT=172.16.0.97:38080 \
-e WECHATY_PUPPET_SERVICE_TOKEN=d5ef8a75-1bfb-4090-8c88-3a6c4ffb8a12 \
-e SERVER_URL=172.16.0.97:9092 \
-e TZ=Asia/Shanghai \
-e WHITELIST_ROOM="源微信小程序项目组&&aihpc-chat&&大模型数据准备&&大模型肯尼亚标注小工组&&周末测试群" \
-e WHITELIST_FRIEND="wxid_ndrljba0pskg12" \
-e WECHAT_NAME="陈曦" \
python-run:wechaty-ws

sleep 3
docker logs -f yuan_bot_client
