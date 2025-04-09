#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os
import csv
import argparse

# 初始化参数解析器
parser = argparse.ArgumentParser(description='初始化食物营养数据库')
parser.add_argument('--csv', type=str, help='CSV文件路径（可选）')
args = parser.parse_args()

# 基本食物数据
BASIC_FOODS = [
    # 水果类
    ('apple', 52, 0.3, 14, 0.2),
    ('banana', 89, 1.1, 23, 0.3),
    ('orange', 47, 0.9, 12, 0.1),
    ('grape', 67, 0.6, 17, 0.4),
    ('watermelon', 30, 0.6, 8, 0.2),
    ('pear', 57, 0.4, 15, 0.1),
    ('pineapple', 50, 0.5, 13, 0.1),
    ('strawberry', 32, 0.7, 8, 0.3),
    ('mango', 60, 0.8, 15, 0.4),
    ('kiwi', 61, 1.1, 15, 0.5),
    
    # 蔬菜类
    ('broccoli', 55, 3.7, 11, 0.6),
    ('carrot', 41, 0.9, 10, 0.2),
    ('tomato', 18, 0.9, 3.9, 0.2),
    ('potato', 77, 2, 17, 0.1),
    ('cucumber', 15, 0.7, 3.6, 0.1),
    ('lettuce', 15, 1.4, 2.9, 0.2),
    ('spinach', 23, 2.9, 3.6, 0.4),
    ('onion', 40, 1.1, 9.3, 0.1),
    ('bell pepper', 31, 1, 6, 0.3),
    ('mushroom', 22, 3.1, 3.3, 0.3),
    
    # 肉类
    ('chicken breast', 165, 31, 0, 3.6),
    ('beef', 250, 26, 0, 17),
    ('pork', 242, 27, 0, 14),
    ('lamb', 294, 25, 0, 21),
    ('turkey', 189, 29, 0, 7),
    ('duck', 337, 19, 0, 28),
    ('salmon', 208, 20, 0, 13),
    ('tuna', 184, 30, 0, 6),
    ('shrimp', 99, 24, 0, 0.3),
    ('crab', 97, 19, 0, 1.5),
    
    # 主食类
    ('rice', 130, 2.7, 28, 0.3),
    ('bread', 265, 9, 49, 3.2),
    ('pasta', 131, 5, 25, 1.1),
    ('noodles', 138, 4.5, 25, 2.1),
    ('oatmeal', 68, 2.5, 12, 1.4),
    ('corn', 86, 3.2, 19, 1.2),
    ('sweet potato', 86, 1.6, 20, 0.1),
    ('quinoa', 120, 4.4, 21, 1.9),
    ('barley', 123, 2.3, 28, 0.8),
    ('couscous', 112, 3.8, 23, 0.2),
    
    # 乳制品
    ('milk', 42, 3.4, 5, 1),
    ('cheese', 402, 25, 1.3, 33),
    ('yogurt', 59, 3.5, 5, 3.3),
    ('butter', 717, 0.9, 0.1, 81),
    ('cream', 340, 2.1, 2.8, 37),
    ('ice cream', 207, 3.5, 24, 11),
    
    # 零食和甜点
    ('chocolate', 546, 4.9, 61, 31),
    ('cake', 257, 3, 38, 11),
    ('cookie', 488, 5, 64, 24),
    ('donut', 452, 5, 51, 25),
    ('pizza', 285, 12, 36, 10),
    ('hamburger', 295, 17, 30, 14),
    ('french fries', 312, 3.4, 41, 15),
    ('chips', 536, 7, 53, 34),
    ('popcorn', 375, 11, 74, 4.3),
    ('candy', 396, 0, 98, 0.2),
    
    # 饮料
    ('coffee', 2, 0.1, 0, 0),
    ('tea', 1, 0, 0.2, 0),
    ('orange juice', 45, 0.7, 10.4, 0.2),
    ('apple juice', 46, 0.1, 11.3, 0.1),
    ('cola', 42, 0, 10.6, 0),
    ('beer', 43, 0.5, 3.6, 0),
    ('wine', 83, 0.1, 2.6, 0),
    
    # 中式菜品
    ('fried rice', 186, 5.4, 31, 4.5),
    ('dumplings', 112, 5, 19, 2),
    ('spring roll', 154, 4.5, 18, 7),
    ('kung pao chicken', 239, 16, 10, 15),
    ('sweet and sour pork', 231, 11, 26, 10),
    ('mapo tofu', 183, 10, 5.7, 14),
    ('hot pot', 210, 15, 8, 14),
    ('peking duck', 401, 25, 0, 33),
    
    # 西式菜品
    ('spaghetti bolognese', 173, 8, 22, 6),
    ('lasagna', 132, 7, 11, 7),
    ('steak', 271, 26, 0, 19),
    ('roast chicken', 190, 20, 0, 12),
    ('fish and chips', 195, 11, 19, 9),
    ('caesar salad', 163, 5, 8, 13),
    ('club sandwich', 228, 15, 18, 12)
]

def init_db(csv_path=None):
    """初始化食物营养数据库"""
    # 创建数据库连接
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
    
    # 插入基本食物数据
    cursor.executemany(
        'INSERT OR IGNORE INTO food_nutrition (food_name, calories, protein, carbs, fat) VALUES (?, ?, ?, ?, ?)',
        BASIC_FOODS
    )
    
    # 如果提供了CSV文件，从中导入数据
    if csv_path and os.path.exists(csv_path):
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                next(csv_reader)  # 跳过标题行
                
                food_data = []
                for row in csv_reader:
                    if len(row) >= 5:  # 确保行有足够的列
                        food_name = row[0].strip().lower()
                        try:
                            calories = float(row[1])
                            protein = float(row[2])
                            carbs = float(row[3])
                            fat = float(row[4])
                            food_data.append((food_name, calories, protein, carbs, fat))
                        except ValueError:
                            print(f"警告: 跳过行 {row} - 数值格式错误")
                
                if food_data:
                    cursor.executemany(
                        'INSERT OR IGNORE INTO food_nutrition (food_name, calories, protein, carbs, fat) VALUES (?, ?, ?, ?, ?)',
                        food_data
                    )
                    print(f"从CSV文件导入了 {len(food_data)} 条食物数据")
        except Exception as e:
            print(f"从CSV文件导入数据时出错: {e}")
    
    # 提交更改并关闭连接
    conn.commit()
    
    # 检查数据库中的食物数量
    cursor.execute('SELECT COUNT(*) FROM food_nutrition')
    food_count = cursor.fetchone()[0]
    
    conn.close()
    
    return food_count

def main():
    print("=== 初始化食物营养数据库 ===\n")
    
    # 初始化数据库
    food_count = init_db(args.csv)
    
    # 如果未提供CSV参数，尝试加载默认的additional_foods.csv
    if not args.csv and os.path.exists('additional_foods.csv'):
        print("\n检测到additional_foods.csv文件，正在导入数据...")
        additional_count = init_db('additional_foods.csv')
        print(f"从additional_foods.csv导入了 {additional_count - food_count} 条新食物数据")
        food_count = additional_count
    
    print(f"\n数据库初始化完成！共有 {food_count} 种食物的营养数据。")
    print("\n您现在可以运行应用程序: python run.py")

if __name__ == "__main__":
    main()