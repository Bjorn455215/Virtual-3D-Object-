# Holographic Gesture AR System (OpenCV Based) 🖐️✨
基於 Python 與 OpenCV 開發的增廣實境（AR）應用系統。透過 MediaPipe 進行即時手勢偵測，並利用自定義的 3D 渲染引擎將虛擬的霓虹立方體投影在現實世界中，支援多種手勢互動功能。

## 🚀 核心功能 (Key Features)

* **自定義 3D 渲染引擎**：不依賴重量級遊戲引擎，純使用 `OpenCV` 與 `NumPy` 實作相機內參矩陣投影，繪製立方體與錐體稜邊。
* **動態選單系統 (Interactive UI)**：具備動態展開/收回的下拉選單，並支援 **Dwell Click (停留點擊)** 觸發功能。
* **手勢互動狀態機 (FSM)**：
    * **生成模式 (Spawn)**：手掌張開即可在指尖位置動態生成 3D 物件。
    * **拖移模式 (Precision Mode)**：雙指伸直狀態下，物件會隨指尖平滑移動。
    * **縮放模式 (Zoom Mode)**：食指拇指捏合（Ready）與拉開（Execute）手勢精準控制物件 Z 軸深度。
    * **握拳重置 (Grab Logic)**：握拳動作可將物件強制重置回初始深度。
* **FIFO 物件管理**：自動維護物件清單，確保運算效能並避免畫面過於雜亂。
* **視覺反饋 (Visual Feedback)**：包含指尖讀條動畫（Ellipse Progress）、半透明 HUD 資訊圖層與霓虹色彩渲染。

## 🛠️ 技術核心 (Tech Stack)

* **Language**: Python 3.13
* **Computer Vision**: OpenCV (`cv2`)
* **Hand Tracking**: MediaPipe
* **Mathematics**: NumPy (矩陣投影運算、歐氏距離、一階低通濾波)
* **Design Principles**: 
    * **Alpha Blending**: 多圖層半透明混合效果。
    * **Perspective Projection**: 針孔相機模型（Pinhole Camera Model）。

## 📝 投影與渲染原理 (Rendering Pipeline)

系統透過 **相機內參矩陣 (Camera Intrinsic Matrix)** 將虛擬 3D 座標投影至 2D 像素平面。

在程式中使用 `cv2.projectPoints` 進行轉換，確保虛擬物件在 3D 空間移動時具備物理真實感。

## 🎮 操作指令 (Controls)

| 手勢 / 動作 | 介面反饋 | 功能說明 |
| :--- | :--- | :--- |
| **食指中指伸直** | 移動手勢 | 手滑動即可拖移方塊 |
| **手掌由合變開** | 霓虹光芒 | 生成新方塊 |
| **拇指食指捏合拉開** | ZOOM READY | 縮放物件大小 |
| **握拳 (Grab)** | 歸位 | 將物件重置為初始大小 |

## 📦 安裝與操作流程 (Installation & Usage)

請嚴格依照下列指令順序進行環境設定與執行：
# 1. 下載專案 (Clone Repository)
git clone [https://github.com/JAYP752/Hand-gesture-3d-control]

# 2. 模組重命名 (Rename Component)
為了讓主程式能正確引用模組，請將下載的 **main.py 名稱更改為 gesture_system.py**

# 3. 環境初始化 (Environment Setup)
# 建立虛擬環境
```python -m venv venv```
# 開啟虛擬環境 (Windows):
```.\venv\Scripts\activate```
# 開啟虛擬環境 (Linux/macOS):
```source venv/bin/activate```
# 安裝依賴套件
```pip install -r requirements.txt```

# 4. 啟動系統 (Execution)
```python original_project.py```

## 實測影片(Video)
https://github.com/user-attachments/assets/7fbd7a33-be38-4f4c-9c99-f188a7ef729a

## 參考資料(Reference)
https://github.com/JAYP752/Hand-gesture-3d-control







