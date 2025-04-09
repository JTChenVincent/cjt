# 导入必要的库
import os
import cv2
import numpy as np
from ultralytics import YOLO
import sqlite3
import argparse
from sklearn.metrics import precision_score, recall_score, f1_score
import matplotlib.pyplot as plt

# 初始化参数解析器
parser = argparse.ArgumentParser(description='测试食物识别功能')
parser.add_argument('--image', type=str, required=True, help='要识别的图像路径')
parser.add_argument('--model', type=str, default='yolov8n.pt', help='YOLOv8模型路径')
args = parser.parse_args()

# 确保上传文件夹存在
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 模型性能评估
def evaluate_model(model, test_dir='test_images', conf_threshold=0.5):
    """
    评估模型性能
    :param model: YOLOv8模型
    :param test_dir: 测试图片目录
    :param conf_threshold: 置信度阈值
    :return: 评估指标字典
    """
    true_labels = []
    pred_labels = []
    confidences = []
    
    for img_file in os.listdir(test_dir):
        if not img_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
            
        img_path = os.path.join(test_dir, img_file)
        img = cv2.imread(img_path)
        
        # 获取真实标签（假设文件名格式为'classname_id.jpg'）
        true_class = img_file.split('_')[0]
        true_labels.append(true_class)
        
        # 模型预测
        results = model(img)
        
        # 处理预测结果
        for result in results:
            boxes = result.boxes
            for box in boxes:
                conf = box.conf.item()
                if conf > conf_threshold:
                    pred_class = model.names[int(box.cls)]
                    pred_labels.append(pred_class)
                    confidences.append(conf)
    
    # 计算评估指标
    precision = precision_score(true_labels, pred_labels, average='weighted')
    recall = recall_score(true_labels, pred_labels, average='weighted')
    f1 = f1_score(true_labels, pred_labels, average='weighted')
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'avg_confidence': np.mean(confidences) if confidences else 0
    }

# 模型微调
def fine_tune_model(model, train_dir='train_data', epochs=10):
    """
    微调YOLOv8模型
    :param model: 基础模型
    :param train_dir: 训练数据目录
    :param epochs: 训练轮数
    :return: 微调后的模型
    """
    # 检查训练数据是否存在
    if not os.path.exists(train_dir):
        print(f"训练数据目录不存在: {train_dir}")
        return None
    
    # 微调模型
    try:
        model.train(data=os.path.join(train_dir, 'data.yaml'), epochs=epochs)
        print("模型微调完成！")
        return model
    except Exception as e:
        print(f"模型微调失败: {e}")
        return None

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

# 主函数
def main():
    # 初始化数据库
    init_db()
    
    # 加载YOLOv8模型
    model = YOLO(args.model)
    
    # 读取图像
    img_path = args.image
    if not os.path.exists(img_path):
        print(f"错误：图像文件 {img_path} 不存在")
        return
    
    # 使用YOLOv8进行食物检测
    results = model(img_path)
    
    # 处理检测结果
    detected_objects = []
    img = cv2.imread(img_path)
    
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
                
                # 在图像上标注检测结果
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img, f"{class_name} ({conf:.2f})", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # 在图像上显示营养信息
                y_offset = y1 + 20
                cv2.putText(img, f"卡路里: {nutrition['calories']} kcal", (x1, y_offset), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
                y_offset += 15
                cv2.putText(img, f"蛋白质: {nutrition['protein']}g", (x1, y_offset), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)