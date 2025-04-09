# 导入必要的库
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
import sqlite3
import numpy as np
import cv2
from PIL import Image
import io
import base64
import sys
import traceback
from datetime import datetime

# 导入YOLOv8模型
from ultralytics import YOLO

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置上传文件夹
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 加载YOLOv8模型
# 注意：首次运行时，如果没有模型文件，将自动下载预训练模型
model = YOLO('yolov8n.pt')  # 使用YOLOv8n轻量级模型

# 初始化数据库
def init_db():
    conn = sqlite3.connect('food_database.db')
    cursor = conn.cursor()
    
    # 创建食物营养信息表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS food_nutrition (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_name TEXT UNIQUE,
        calories REAL,
        protein REAL,
        carbs REAL,
        fat REAL
    )
    ''')
    
    # 创建用户饮食记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_diet_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_name TEXT,
        calories REAL,
        protein REAL,
        carbs REAL,
        fat REAL,
        date TEXT,
        meal_type TEXT
    )
    ''')
    
    # 插入一些示例食物数据
    sample_foods = [
        ('apple', 52, 0.3, 14, 0.2),
        ('banana', 89, 1.1, 23, 0.3),
        ('rice', 130, 2.7, 28, 0.3),
        ('chicken breast', 165, 31, 0, 3.6),
        ('broccoli', 55, 3.7, 11, 0.6),
        ('egg', 78, 6.3, 0.6, 5.3),
        ('salmon', 208, 20, 0, 13),
        ('pizza', 285, 12, 36, 10),
        ('hamburger', 295, 17, 30, 14),
        ('orange', 47, 0.9, 12, 0.1),
        ('carrot', 41, 0.9, 10, 0.2),
        ('potato', 77, 2, 17, 0.1),
        ('tomato', 18, 0.9, 3.9, 0.2),
        ('bread', 265, 9, 49, 3.2),
        ('pasta', 131, 5, 25, 1.1),
        ('steak', 271, 26, 0, 19),
        ('cake', 257, 3, 38, 11),
        ('ice cream', 207, 3.5, 24, 11),
        ('chocolate', 546, 4.9, 61, 31),
        ('milk', 42, 3.4, 5, 1)
    ]
    
    cursor.executemany(
        'INSERT OR IGNORE INTO food_nutrition (food_name, calories, protein, carbs, fat) VALUES (?, ?, ?, ?, ?)',
        sample_foods
    )
    
    conn.commit()
    conn.close()

# 获取食物的营养信息
def get_food_nutrition(food_name):
    conn = sqlite3.connect('food_database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM food_nutrition WHERE food_name = ?', (food_name.lower(),))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return {
            'food_name': result[1],
            'calories': result[2],
            'protein': result[3],
            'carbs': result[4],
            'fat': result[5]
        }
    else:
        # 如果数据库中没有该食物，返回默认值
        return {
            'food_name': food_name,
            'calories': 100,  # 默认卡路里值
            'protein': 0,
            'carbs': 0,
            'fat': 0
        }

# 保存饮食记录
def save_diet_record(food_data, meal_type='lunch'):
    conn = sqlite3.connect('food_database.db')
    cursor = conn.cursor()
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute(
        'INSERT INTO user_diet_records (food_name, calories, protein, carbs, fat, date, meal_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (food_data['food_name'], food_data['calories'], food_data['protein'], food_data['carbs'], food_data['fat'], current_date, meal_type)
    )
    
    conn.commit()
    conn.close()

# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

# 处理图像上传和食物识别
@app.route('/detect', methods=['POST'])
def detect_food():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # 保存上传的图像
    img_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(img_path)
    
    # 使用YOLOv8进行食物检测
    results = model(img_path)
    
    # 处理检测结果
    detected_objects = []
    for result in results:
        boxes = result.boxes.cpu().numpy()
        for i, box in enumerate(boxes):
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            # 获取类别名称
            class_name = result.names[cls_id]
            
            # 只保留可能是食物的类别，并且置信度大于0.5
            food_classes = ['apple', 'banana', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'sandwich', 
                           'bowl', 'dining table', 'spoon', 'fork', 'knife', 'cup', 'bottle']
            
            if conf > 0.5 and (class_name in food_classes or 'food' in class_name.lower()):
                # 获取边界框坐标
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # 获取食物的营养信息
                nutrition = get_food_nutrition(class_name)
                
                detected_objects.append({
                    'class_name': class_name,
                    'confidence': conf,
                    'box': [x1, y1, x2, y2],
                    'nutrition': nutrition
                })
    
    # 如果没有检测到食物，尝试使用更通用的检测
    if not detected_objects:
        # 这里可以添加更多的食物识别逻辑，例如使用特定的食物识别模型
        # 目前使用一个简单的默认值作为示例
        detected_objects.append({
            'class_name': 'unknown food',
            'confidence': 0.5,
            'box': [0, 0, 100, 100],
            'nutrition': get_food_nutrition('unknown food')
        })
    
    # 在图像上标注检测结果
    img = cv2.imread(img_path)
    for obj in detected_objects:
        x1, y1, x2, y2 = obj['box']
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, f"{obj['class_name']} ({obj['confidence']:.2f})", (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # 保存标注后的图像
    annotated_img_path = os.path.join(app.config['UPLOAD_FOLDER'], 'annotated_' + file.filename)
    cv2.imwrite(annotated_img_path, img)
    
    # 返回检测结果和标注后的图像路径
    return jsonify({
        'detected_objects': detected_objects,
        'annotated_image': '/'.join(annotated_img_path.split(os.sep)[-2:])
    })

# 保存饮食记录的API
@app.route('/save_record', methods=['POST'])
def save_record():
    data = request.json
    food_data = data.get('food_data')
    meal_type = data.get('meal_type', 'lunch')
    
    if not food_data:
        return jsonify({'error': 'No food data provided'}), 400
    
    save_diet_record(food_data, meal_type)
    
    return jsonify({'success': True, 'message': 'Diet record saved successfully'})

# 获取饮食记录的API
@app.route('/get_records', methods=['GET'])
def get_records():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    conn = sqlite3.connect('food_database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM user_diet_records WHERE date = ?', (date,))
    records = cursor.fetchall()
    
    conn.close()
    
    result = []
    for record in records:
        result.append({
            'id': record[0],
            'food_name': record[1],
            'calories': record[2],
            'protein': record[3],
            'carbs': record[4],
            'fat': record[5],
            'date': record[6],
            'meal_type': record[7]
        })
    
    return jsonify(result)

# 初始化数据库并启动应用
if __name__ == '__main__':
    try:
        print("正在初始化数据库...")
        init_db()
        print("数据库初始化完成！")
        print("正在启动应用服务器...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"错误: {e}")
        print("详细错误信息:")
        traceback.print_exc()
        sys.exit(1)