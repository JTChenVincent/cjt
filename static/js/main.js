// DOM元素
const uploadArea = document.getElementById('upload-area');
const uploadBtn = document.getElementById('upload-btn');
const fileInput = document.getElementById('file-input');
const uploadContainer = document.getElementById('upload-container');
const previewContainer = document.getElementById('preview-container');
const previewImg = document.getElementById('preview-img');
const detectBtn = document.getElementById('detect-btn');
const cancelBtn = document.getElementById('cancel-btn');
const resultsSection = document.getElementById('results-section');
const resultImg = document.getElementById('result-img');
const foodItems = document.getElementById('food-items');
const totalCalories = document.getElementById('total-calories');
const totalProtein = document.getElementById('total-protein');
const totalCarbs = document.getElementById('total-carbs');
const totalFat = document.getElementById('total-fat');
const saveBtn = document.getElementById('save-btn');
const newDetectionBtn = document.getElementById('new-detection-btn');
const historyContainer = document.getElementById('history-container');
const saveModal = document.getElementById('save-modal');
const closeModal = document.getElementById('close-modal');
const saveForm = document.getElementById('save-form');
const mealType = document.getElementById('meal-type');

// 全局变量
let currentFile = null;
let detectedObjects = [];

// 事件监听器
uploadArea.addEventListener('click', () => fileInput.click());
uploadBtn.addEventListener('click', () => fileInput.click());

// 拖放功能
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.backgroundColor = '#ecf0f1';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.backgroundColor = '';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.backgroundColor = '';
    
    if (e.dataTransfer.files.length) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

// 文件选择处理
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFileSelect(e.target.files[0]);
    }
});

// 处理文件选择
function handleFileSelect(file) {
    // 检查文件类型
    if (!file.type.match('image.*')) {
        alert('请选择图片文件！');
        return;
    }
    
    currentFile = file;
    
    // 显示预览
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        uploadContainer.style.display = 'none';
        previewContainer.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

// 取消按钮
cancelBtn.addEventListener('click', () => {
    uploadContainer.style.display = 'block';
    previewContainer.style.display = 'none';
    currentFile = null;
    fileInput.value = '';
});

// 识别按钮
detectBtn.addEventListener('click', () => {
    if (!currentFile) return;
    
    // 创建FormData对象
    const formData = new FormData();
    formData.append('file', currentFile);
    
    // 显示加载状态
    detectBtn.disabled = true;
    detectBtn.textContent = '识别中...';
    
    // 发送请求到后端
    fetch('/detect', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // 处理识别结果
        detectedObjects = data.detected_objects;
        displayResults(data);
        
        // 重置按钮状态
        detectBtn.disabled = false;
        detectBtn.textContent = '识别食物';
    })
    .catch(error => {
        console.error('Error:', error);
        alert('识别失败，请重试！');
        
        // 重置按钮状态
        detectBtn.disabled = false;
        detectBtn.textContent = '识别食物';
    });
});

// 显示识别结果
function displayResults(data) {
    // 显示标注后的图像
    resultImg.src = data.annotated_image;
    
    // 清空之前的结果
    foodItems.innerHTML = '';
    
    // 计算总营养值
    let calories = 0;
    let protein = 0;
    let carbs = 0;
    let fat = 0;
    
    // 显示每个检测到的食物项
    data.detected_objects.forEach(obj => {
        const foodItem = document.createElement('div');
        foodItem.className = 'food-item';
        
        const nutrition = obj.nutrition;
        
        // 累加营养值
        calories += nutrition.calories;
        protein += nutrition.protein;
        carbs += nutrition.carbs;
        fat += nutrition.fat;
        
        foodItem.innerHTML = `
            <h3>
                ${nutrition.food_name}
                <span class="confidence">${(obj.confidence * 100).toFixed(0)}% 置信度</span>
            </h3>
            <div class="nutrition-info">
                <div class="nutrition-item">
                    <span class="nutrition-label">卡路里:</span>
                    <span class="nutrition-value">${nutrition.calories}</span>
                    <span class="nutrition-unit">kcal</span>
                </div>
                <div class="nutrition-item">
                    <span class="nutrition-label">蛋白质:</span>
                    <span class="nutrition-value">${nutrition.protein}</span>
                    <span class="nutrition-unit">g</span>
                </div>
                <div class="nutrition-item">
                    <span class="nutrition-label">碳水:</span>
                    <span class="nutrition-value">${nutrition.carbs}</span>
                    <span class="nutrition-unit">g</span>
                </div>
                <div class="nutrition-item">
                    <span class="nutrition-label">脂肪:</span>
                    <span class="nutrition-value">${nutrition.fat}</span>
                    <span class="nutrition-unit">g</span>
                </div>
            </div>
        `;
        
        foodItems.appendChild(foodItem);
    });
    
    // 更新总营养值
    totalCalories.textContent = calories.toFixed(1);
    totalProtein.textContent = protein.toFixed(1);
    totalCarbs.textContent = carbs.toFixed(1);
    totalFat.textContent = fat.toFixed(1);
    
    // 显示结果区域
    resultsSection.style.display = 'block';
    
    // 滚动到结果区域
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// 保存按钮
saveBtn.addEventListener('click', () => {
    // 显示保存模态框
    saveModal.style.display = 'flex';
});

// 关闭模态框
closeModal.addEventListener('click', () => {
    saveModal.style.display = 'none';
});

// 点击模态框外部关闭
window.addEventListener('click', (e) => {
    if (e.target === saveModal) {
        saveModal.style.display = 'none';
    }
});

// 保存表单提交
saveForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    // 准备要保存的数据
    const foodData = [];
    let totalNutrition = {
        food_name: '组合餐食',
        calories: 0,
        protein: 0,
        carbs: 0,
        fat: 0
    };
    
    // 计算总营养值
    detectedObjects.forEach(obj => {
        const nutrition = obj.nutrition;
        totalNutrition.calories += nutrition.calories;
        totalNutrition.protein += nutrition.protein;
        totalNutrition.carbs += nutrition.carbs;
        totalNutrition.fat += nutrition.fat;
    });
    
    // 发送保存请求
    fetch('/save_record', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            food_data: totalNutrition,
            meal_type: mealType.value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('饮食记录保存成功！');
            saveModal.style.display = 'none';
            loadDietHistory(); // 重新加载饮食历史
        } else {
            alert('保存失败：' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('保存失败，请重试！');
    });
});

// 新的识别按钮
newDetectionBtn.addEventListener('click', () => {
    // 重置界面状态
    resultsSection.style.display = 'none';
    uploadContainer.style.display = 'block';
    previewContainer.style.display = 'none';
    currentFile = null;
    fileInput.value = '';
    
    // 滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// 加载饮食历史记录
function loadDietHistory() {
    fetch('/get_records')
    .then(response => response.json())
    .then(data => {
        if (data.length === 0) {
            historyContainer.innerHTML = '<p class="empty-history">暂无饮食记录</p>';
            return;
        }
        
        historyContainer.innerHTML = '';
        
        // 显示每条饮食记录
        data.forEach(record => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            
            const mealTypeText = {
                'breakfast': '早餐',
                'lunch': '午餐',
                'dinner': '晚餐',
                'snack': '零食'
            }[record.meal_type] || record.meal_type;
            
            historyItem.innerHTML = `
                <div class="history-food-info">
                    <h3>${record.food_name}</h3>
                    <p>${record.date} - ${mealTypeText}</p>
                </div>
                <div class="history-nutrition">
                    <div class="nutrition-item">
                        <span class="nutrition-value">${record.calories}</span>
                        <span class="nutrition-unit">kcal</span>
                    </div>
                </div>
            `;
            
            historyContainer.appendChild(historyItem);
        });
    })
    .catch(error => {
        console.error('Error:', error);
        historyContainer.innerHTML = '<p class="empty-history">加载饮食记录失败</p>';
    });
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    // 加载饮食历史记录
    loadDietHistory();
});