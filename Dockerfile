FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 更新pip并安装依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 暴露端口
EXPOSE 9096

# 设置环境变量
ENV FLASK_APP=feishu_bot.py
ENV FLASK_ENV=production

# 启动应用
CMD ["python", "feishu_bot.py"]