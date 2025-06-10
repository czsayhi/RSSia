# 使用Node.js 18官方镜像
FROM node:18-alpine

# 设置工作目录
WORKDIR /app

# 复制package.json和package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制应用代码
COPY . .

# 构建应用（生产环境）
# RUN npm run build

# 暴露端口
EXPOSE 3000

# 开发环境启动命令
CMD ["npm", "run", "dev"]

# 生产环境启动命令（取消注释下面的行，注释上面的行）
# CMD ["npm", "start"] 