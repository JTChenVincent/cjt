# 导入必要的库
import os
import cv2
import numpy as np
from ultralytics import YOLO
import sqlite3
import argparse

# 初始化参数解析器
parser = argparse.ArgumentParser(description='测试食物识别功能')
parser.add_argument('--image', type=str, required=True, help='要识别的图像路径')
parser.add_argument('--model', type=str, default='yolov8n.pt', help='YOLOv8模型路径')
args = parser.parse_args()

# 确保上传文件夹存在
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    
    # 计算总营养摄入量
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    
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
                
                # 累加总营养摄入量
                total_calories += nutrition['calories']
                total_protein += nutrition['protein']
                total_carbs += nutrition['carbs']
                total_fat += nutrition['fat']
                
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
    
    # 如果没有检测到食物，显示提示信息
    if not detected_objects:
        print("未检测到任何食物！")
        return
    
    # 在图像底部显示总营养摄入量
    height, width, _ = img.shape
    cv2.rectangle(img, (0, height - 60), (width, height), (0, 0, 0), -1)  # 黑色背景
    cv2.putText(img, f"总卡路里: {total_calories:.1f} kcal | 蛋白质: {total_protein:.1f}g | 碳水: {total_carbs:.1f}g | 脂肪: {total_fat:.1f}g", 
                (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # 保存结果图像
    output_path = os.path.join(UPLOAD_FOLDER, 'result_' + os.path.basename(img_path))
    cv2.imwrite(output_path, img)
    
    print(f"\n检测到 {len(detected_objects)} 个食物项:")
    for i, obj in enumerate(detected_objects):
        print(f"\n{i+1}. {obj['class_name']} (置信度: {obj['confidence']:.2f})")
        print(f"   卡路里: {obj['nutrition']['calories']} kcal")
        print(f"   蛋白质: {obj['nutrition']['protein']}g")
        print(f"   碳水化合物: {obj['nutrition']['carbs']}g")
        print(f"   脂肪: {obj['nutrition']['fat']}g")
    
    print(f"\n总营养摄入量:")
    print(f"总卡路里: {total_calories:.1f} kcal")
    print(f"总蛋白质: {total_protein:.1f}g")
    print(f"总碳水化合物: {total_carbs:.1f}g")
    print(f"总脂肪: {total_fat:.1f}g")
    
    print(f"\n结果图像已保存到: {output_path}")

if __name__ == "__main__":
    main()