# 使用 Windows 基础镜像
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# 安装 Python
RUN powershell.exe -Command \
    $ErrorActionPreference = 'Stop'; \
    Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.10.5/python-3.10.5-amd64.exe -OutFile python-installer.exe; \
    Start-Process python-installer.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -NoNewWindow -Wait; \
    Remove-Item -Force python-installer.exe

# 设置工作目录
WORKDIR /app

# 复制当前目录内容到工作目录
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露 Flask 应用程序运行的端口
EXPOSE 5000

# 启动 Flask 应用程序
CMD ["python", "app.py"]
