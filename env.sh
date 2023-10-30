# puppet-padlocal token申请：http://pad-local.com/#/login
docker rm -f yuan_bot_gateway
sleep 5

docker run -it -d \
--name yuan_bot_gateway \
-e WECHATY_PUPPET=wechaty-puppet-padlocal \
-e WECHATY_PUPPET_PADLOCAL_TOKEN=puppet_padlocal_5f9600a66dd148598af7cb6727cc1a16 \
-e WECHATY_PUPPET_SERVER_PORT=8080 \
-e WECHATY_TOKEN=d5ef8a75-1bfb-4090-8c88-3a6c4ffb8a12 \
-e WECHATY_PUPPET_SERVICE_NO_TLS_INSECURE_SERVER=true \
-e WECHATY_LOG=verbose \
-p 38080:8080 \
wechaty/wechaty:latest

sleep 5
docker logs -f yuan_bot_gateway