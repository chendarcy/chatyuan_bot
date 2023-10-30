FROM python:3.9.16-wechaty-ws
ADD ./chatyuan_wechat.py /bot/chatyuan_wechat.py
ADD ./Dockerfile /bot/Dockerfile
ADD ./deploy.sh /bot/deploy.sh
CMD python /bot/chatyuan_wechat.py
