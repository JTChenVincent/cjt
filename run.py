#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import webbrowser
import time

def check_dependencies():
    """检查必要的依赖项是否已安装"""
    try:
        import flask
        import ultralytics
        import numpy
        import cv2
        import sqlite3
        return True
    except ImportError as e:
        print(f"缺少必要的依赖项: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_model():
    """检查YOLOv8模型是否存在，如果不存在则下载"""
    model_path = 'yolov8n.pt'
    if not os.path.exists(model_path):
        print("YOLOv8模型不存在，正在下载...")
        try:
            from ultralytics import YOLO
            model = YOLO('yolov8n.pt')  # 这将自动下载模型
            print("模型下载完成！")
            return True
        except Exception as e:
            print(f"模型下载失败: {e}")
            print("请手动下载YOLOv8模型并放置在项目根目录")
            return False
    return True

def create_directories():
    """创建必要的目录"""
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/img', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)

def main():
    print("=== AI 智能菜品识别+卡路里计算助手 ===\n")
    
    # 检查依赖项
    print("检查依赖项...")
    if not check_dependencies():
        return
    
    # 检查模型
    print("检查YOLOv8模型...")
    if not check_model():
        return
    
    # 创建必要的目录
    create_directories()
    
    # 初始化数据库
    print("初始化数据库...")
    try:
        # 直接导入并运行初始化数据库脚本
        import init_database
        food_count = init_database.init_db()
        print(f"数据库初始化完成！共有 {food_count} 种食物的营养数据。")
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 启动Flask应用
    print("\n启动应用服务器...")
    print("应用将在浏览器中打开，请稍候...\n")
    
    # 启动应用并在浏览器中打开
    url = "http://localhost:5000"
    
    try:
        # 使用子进程启动Flask应用
        process = subprocess.Popen([sys.executable, 'app.py'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE, 
                                  universal_newlines=True)
        
        # 等待服务器启动
        time.sleep(2)
        
        # 检查进程是否已经退出
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print("应用启动失败!")
            print(f"标准输出: {stdout}")
            print(f"错误输出: {stderr}")
            return
        
        # 打开浏览器
        webbrowser.open(url)
        
        print(f"应用已启动，请访问: {url}")
        print("按Ctrl+C停止服务器")
        
        # 等待进程结束
        process.wait()
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        process.terminate()
        print("服务器已停止")
    except Exception as e:
        print(f"启动应用时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()