import cv2
import numpy as np
import time
import random

# 引入原本舊檔案的 AI 追蹤元件
from gesture_system import HandTracker, GestureController # 引用

class CV2Renderer3D:
    """OpenCV 專屬 3D 幾何投影渲染器"""
    def __init__(self):
        # 定義 3D 立方體頂點
        self.base_vertices = np.array([
            [-0.3, -0.3,  0.3], [ 0.3, -0.3,  0.3], [ 0.3,  0.3,  0.3], [-0.3,  0.3,  0.3],
            [-0.3, -0.3, -0.3], [ 0.3, -0.3, -0.3], [ 0.3,  0.3, -0.3], [-0.3,  0.3, -0.3]
        ], dtype=np.float32)

        # 定義 12 條稜邊
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]

    def render_cube(self, frame, rot_x, rot_y, zoom, position, color=(0, 255, 0)):
        h, w = frame.shape[:2]
        focal_length = w # 決定相機視野
        # 相機內參矩陣
        camera_matrix = np.array([
            [focal_length, 0, w / 2],
            [0, focal_length, h / 2],
            [0, 0, 1]
        ], dtype=np.float32)
        dist_coeffs = np.zeros(4, dtype=np.float32) # 我現在要在一個完全平整、沒有任何鏡頭扭曲的空間裡繪圖

        # 使用傳入的專屬角度進行投影
        # 把原本存在於大腦（或是 3D 空間）裡的虛擬方塊，精準地壓成 2D 像素，畫在 Webcam 影格上
        rvec = np.array([np.radians(rot_x), np.radians(rot_y), 0], dtype=np.float32) # 告訴電腦方塊怎麼轉
        tvec = np.array([position[0], position[1], zoom], dtype=np.float32) # 告訴電腦方塊要放在哪

        # 3d -> 2d，輸出8個頂點在2d平面上的x y 像素位置
        try:
            img_pts, _ = cv2.projectPoints(self.base_vertices, rvec, tvec, camera_matrix, dist_coeffs)
            img_pts = img_pts.reshape(-1, 2).astype(int) # 格式整理並轉成整數，方便後續讀取

            for start, end in self.edges: # 方塊連線
                p1 = tuple(img_pts[start])
                p2 = tuple(img_pts[end])
                # 邊界檢查，在畫面內的才畫出來
                if (0 <= p1[0] < w and 0 <= p1[1] < h) or (0 <= p2[0] < w and 0 <= p2[1] < h):
                    cv2.line(frame, p1, p2, color, 2)
        except:
            pass
        return frame

class ARApp:
    def __init__(self):
        print("=== 啟動全息手勢 AR 系統 (自動旋轉+上限5個版) ===")
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.tracker = HandTracker() # 引用
        self.gesture = GestureController() #引用
        self.renderer = CV2Renderer3D()

        self.cubes = []                # 存放所有方塊
        self.prev_hand_open = False    # 狀態機變數
        # self.prev_tip_pos = [0, 0] # 上一畫面指尖的位置
        
        self.last_time = time.time()
        self.fps = 0.0

        self.is_ready_to_zoom = False # 初始縮放狀態

    def calculate_fps(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        if 0.001 < dt < 1.0:
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt) # 一階低通濾波器，讓fps數值穩定

    def draw_hud(self, frame):
        h, w = frame.shape[:2]
        overlay = np.zeros_like(frame) # 跟畫面一樣大的圖層
        cv2.rectangle(overlay, (0, 0), (w, 120), (0, 0, 0), -1) # 提示區
        cv2.rectangle(overlay, (0, 120), (w, h), (40, 20, 10), -1) # 方塊生成區

        # alpha 越高，背景越暗
        alpha = 0.6 
        cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)

        if self.gesture.is_active:
            status, color = f"ACTIVE - Controlling Cubes ({len(self.cubes)}/1)", (0, 255, 0)
        else:
            status, color = f"IDLE - Auto Rotating ({len(self.cubes)}/1)", (0, 255, 255) # 黃色代表自動旋轉中

        cv2.putText(frame, status, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, "Tip: Open hand again to spawn. Max 1 cubes.", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"FPS: {self.fps:.1f} | [R] Reset | [Q] Quit", (15, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        #.lf 讀取fps到小數後第一位
        return frame

    # 食指移動方塊
    def get_point_mode(self, landmarks):
        if landmarks is None or len(landmarks) < 21: return False
        
        # landmarks[i][1] 代表第 i 個點的 Y 座標
        # 注意：在像素座標中，數值越小代表位置越高
        index_up = landmarks[8][1] < landmarks[6][1]
        middle_up = landmarks[12][1] < landmarks[10][1] 
        
        ring_down = landmarks[16][1] > landmarks[14][1]
        pinky_down = landmarks[20][1] > landmarks[18][1]
        return index_up and middle_up and ring_down and pinky_down
    
    # 握拳判定
    def check_grab(self, landmarks):
        if not landmarks: 
            return False
        # 8:食指尖, 6:食指第二關節 | 12:中指尖, 10:中指第二關節 | 16:無名指尖, 14:無名指第二關節
        f1 = landmarks[8][1] > landmarks[6][1]
        f2 = landmarks[12][1] > landmarks[10][1]
        f3 = landmarks[16][1] > landmarks[14][1]
        return f1 and f2 and f3
    
    def run(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret: break

            self.calculate_fps() 
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2] # 720, 1280

            # 偵測手部，引用process_frame
            frame, landmarks = self.tracker.process_frame(frame) 

            # 初始化
            tip_pos = [0, 0]
            is_precision_mode = False
            finger_dist = 0.0 # 拇指與食指 (縮放用)
            is_grab = False # 歸位判斷

            if landmarks and len(landmarks) > 20:
                # 以食指為基準
                # 減號: 平移中心、除號: 標準化、乘號: 靈敏度調整
                tip_x = ((landmarks[8][0]  - w / 2) / (w / 2)) * 3.5  
                tip_y = ((landmarks[8][1]  - h / 2) / (h / 2)) * 1.8   
                tip_pos = [tip_x, tip_y]

                # 判定縮放
                p4 = np.array([landmarks[4][0] , landmarks[4][1] ])
                p8 = np.array([landmarks[8][0] , landmarks[8][1] ])
                finger_dist = np.linalg.norm(p4 - p8) # 算歐式距離

                # 判定拖移模式：只要食指、中指伸直就算進入模式
                is_precision_mode = self.get_point_mode(landmarks)

                # 握拳判定
                is_grab = self.check_grab(landmarks)

                self.gesture.update(landmarks, self.tracker)

            # -------------------------- 生成邏輯  -----------------------------------
            is_open = self.tracker.is_hand_open(landmarks) if landmarks else False
            if is_open and not self.prev_hand_open:
                spawn_x, spawn_y = tip_pos[0] + random.uniform(-0.25, 0.25), tip_pos[1] + random.uniform(-0.25, 0.25)
                
                # 印出方塊生成位置
                print(f"方塊生成位置: X={spawn_x:.2f}, Y={spawn_y:.2f}")
                
                neon_colors = [(255, 255, 100), (100, 255, 100), (100, 255, 255), (255, 100, 255), (255, 255, 255)]
                
                self.cubes.append({
                    "position": [spawn_x, spawn_y], 
                    "z": 6.0, # 讓每個方塊都有自己的z軸
                    "color": random.choice(neon_colors),
                    "rx": 0, # 初始旋轉角是0，隨時間改變 
                    "ry": 0,
                    "sx": random.choice([-1, 1]), 
                    "sy": random.choice([-1, 1])
                })
                if len(self.cubes) > 1: 
                    self.cubes.pop(0) # 生成第2個方塊時 消除最舊的
            
            self.prev_hand_open = is_open 

            # -------------- 多方塊時的避讓邏輯: 讓方塊兩兩判斷，不會疊圖(被動避讓) ---------------------
            for i in range(len(self.cubes)):
                for j in range(i + 1, len(self.cubes)):
                    c1, c2 = self.cubes[i], self.cubes[j]
                    dist_vec = np.array(c1["position"]) - np.array(c2["position"])
                    dist = np.linalg.norm(dist_vec)
                    if 0.01 < dist < 0.55:
                        push_dir = dist_vec / (dist + 1e-5)
                        push_strength = (0.55 - dist) * 0.5
                        c1["position"] += push_dir * push_strength
                        c2["position"] -= push_dir * push_strength

            self.draw_hud(frame) # 先放置畫布，再渲染方塊

            # ------------------------------- 渲染與操作迴圈 ---------------------------------
            for cube in self.cubes:
                cube["rx"] += cube["sx"] # 手沒操作時自轉
                cube["ry"] += cube["sy"]
                dist_to_cube = np.linalg.norm(np.array(tip_pos) - np.array(cube["position"]))

                if dist_to_cube < 0.6:
                    if is_grab: # 握拳歸位
                        cube["z"] = 6.0 # 回到原本大小
                        self.is_ready_to_zoom = False

                    elif is_precision_mode: # 伸直模式
                        cube["position"][0] += (tip_pos[0] - cube["position"][0]) * 0.2
                        cube["position"][1] += (tip_pos[1] - cube["position"][1]) * 0.2
                    
                    if not is_grab:
                        if finger_dist < 100:
                            if not self.is_ready_to_zoom:
                                self.is_ready_to_zoom = True

                        if self.is_ready_to_zoom and finger_dist > 200: # 張開觸發放大
                            cube["z"] = max(cube["z"] - 1.5, 2.5) 
                            self.is_ready_to_zoom = False

                frame = self.renderer.render_cube(
                    frame,
                    self.gesture.rotation_x + cube["rx"],
                    self.gesture.rotation_y + cube["ry"],
                    cube["z"], 
                    cube["position"],
                    cube["color"]
                ) # 打包資訊給def render_cube

            if landmarks:
                # 這樣印出來的 Ready 才會是最新、最準確的狀態
                debug_txt = f"Mode: {is_precision_mode} | Dist: {finger_dist:.1f} | Ready: {self.is_ready_to_zoom}"
                cv2.putText(frame, debug_txt, (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # 如果 Ready 成功，加一個顯眼的顏色提醒
                if self.is_ready_to_zoom:
                    cv2.putText(frame, "ZOOM READY!", (10, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            cv2.imshow("AR Neon Fixed", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): break
            if key == ord('r'): self.cubes = []

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        ar_app = ARApp()
        ar_app.run()
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()
