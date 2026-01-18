import sys
import random
import time
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, 
                               QVBoxLayout, QWidget, QLineEdit, QStackedWidget)

# --- Configuration & Aesthetics ---
COLORS = {
    "bg": "#121212",        
    "text_main": "#E0E0E0", # Explicit White for visibility
    "text_dim": "#757575",  
    "accent": "#BB86FC",    
    "input_bg": "#1E1E1E",  
    "success_overlay": "rgba(27, 94, 32, 0.4)",
    "error_overlay": "rgba(183, 28, 28, 0.4)",
    "success_text": "#69F0AE",
    "error_text": "#FF5252"
}

FONTS = {
    "equation": "Consolas", 
    "ui": "Segoe UI",       
}

class MathEngine:
    def __init__(self):
        self.mode = "ADD" # ADD or SUB
        self.phase = 1
        self.streak = 0
        self.total_correct_phase = 0
        self.start_time = 0
        self.history = [] 
        
        # --- ADDITION LEVELS (The Scaffolding Strategy) ---
        self.add_levels = [
            # L1: Pure Speed (No Carries)
            {"count": 20, "d": 2, "pool": [0,1,2,3,4,5], "label": "L1: 2D SPEED (0-5)"},
            # L2: Heavy Carry Practice (Force the Round-Up Strategy)
            {"count": 20, "d": 2, "pool": [6,7,8,9], "label": "L2: 2D CARRY (6-9)"},
            # L3: Real World Mixed
            {"count": 20, "d": 2, "pool": list(range(10)), "label": "L3: 2D MIXED"},
            # L4: Memory Stretch
            {"count": 20, "d": 3, "pool": list(range(10)), "label": "L4: 3D MASTER"},
            # L5: Exam Standard
            {"count": 20, "d": 4, "pool": list(range(10)), "label": "L5: 4D GRANDMASTER"},
        ]

        # --- SUBTRACTION LEVELS (Linear to 4D) ---
        self.sub_levels = [
            {"count": 30, "d": 2, "label": "L1: 2D SUBTRACTION"},
            {"count": 30, "d": 3, "label": "L2: 3D SUBTRACTION"},
            {"count": 30, "d": 4, "label": "L3: 4D SUBTRACTION"},
        ]

        self.current_level_idx = 0
        self.current_terms = []
        self.expected_ans = 0
    
    def set_mode(self, mode):
        self.mode = mode
        self.current_level_idx = 0
        self.streak = 0
        self.total_correct_phase = 0
        self.phase = 1
        self.generate_new_problem()

    def generate_number(self, digits, pool=None):
        if pool:
            # Custom pool generation (for Addition L1/L2)
            valid_first = [d for d in pool if d != 0]
            if not valid_first: valid_first = [1]
            num_str = str(random.choice(valid_first))
            for _ in range(digits - 1):
                num_str += str(random.choice(pool))
            return int(num_str)
        else:
            # Standard generation
            start = 10**(digits-1)
            end = (10**digits) - 1
            return random.randint(start, end)

    def generate_new_problem(self):
        self.start_time = time.time()
        
        # Select Level Config based on Mode
        levels = self.add_levels if self.mode == "ADD" else self.sub_levels
        
        if self.phase == 1:
            if self.current_level_idx < len(levels):
                cfg = levels[self.current_level_idx]
                
                if self.mode == "ADD":
                    t1 = self.generate_number(cfg["d"], cfg.get("pool"))
                    t2 = self.generate_number(cfg["d"], cfg.get("pool"))
                    self.current_terms = [t1, t2]
                    self.expected_ans = t1 + t2
                
                elif self.mode == "SUB":
                    # Generate two numbers of the current digit length
                    t1 = self.generate_number(cfg["d"])
                    t2 = self.generate_number(cfg["d"])
                    # Ensure T1 is always larger for positive result
                    big = max(t1, t2)
                    small = min(t1, t2)
                    self.current_terms = [big, small]
                    self.expected_ans = big - small
            else:
                self.phase = 2
                self.generate_new_problem()
                return

        elif self.phase == 2:
            # ENDLESS MODE (God Mode)
            if self.mode == "ADD":
                num_terms = random.randint(3, 6)
                self.current_terms = []
                for _ in range(num_terms):
                    self.current_terms.append(self.generate_number(random.choice([2,3,4])))
                self.expected_ans = sum(self.current_terms)
            
            elif self.mode == "SUB":
                # In endless subtraction, we keep doing 4D - 4D or mixed
                d = random.choice([3, 4])
                t1 = self.generate_number(d)
                t2 = self.generate_number(d)
                self.current_terms = [max(t1, t2), min(t1, t2)]
                self.expected_ans = self.current_terms[0] - self.current_terms[1]

    def check_answer(self, user_ans_str):
        try:
            val = int(user_ans_str)
        except ValueError:
            return False, self.expected_ans

        is_correct = (val == self.expected_ans)
        
        # Stats logic
        if is_correct:
            self.streak += 1
            if self.phase == 1:
                self.total_correct_phase += 1
                levels = self.add_levels if self.mode == "ADD" else self.sub_levels
                current_goal = levels[self.current_level_idx]["count"]
                
                if self.total_correct_phase >= current_goal:
                    self.current_level_idx += 1
                    self.total_correct_phase = 0
                    if self.current_level_idx >= len(levels):
                        self.phase = 2
        else:
            self.streak = 0 

        return is_correct, self.expected_ans

    def get_progress_text(self):
        if self.phase == 1:
            levels = self.add_levels if self.mode == "ADD" else self.sub_levels
            cfg = levels[self.current_level_idx]
            return f"{cfg['label']} | {self.total_correct_phase}/{cfg['count']}"
        else:
            return f"PHASE 2 | GOD MODE | STREAK: {self.streak}"


# --- UI COMPONENTS ---

class LobbyWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("MENTAL DOJO")
        title.setFont(QFont(FONTS['equation'], 48, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_main']};") 
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("PRESS [A] FOR ADDITION\nPRESS [S] FOR SUBTRACTION\nPRESS [ESC] TO QUIT")
        subtitle.setFont(QFont(FONTS['ui'], 18))
        subtitle.setStyleSheet(f"color: {COLORS['text_dim']}; letter-spacing: 4px; line-height: 40px;")
        subtitle.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addSpacing(50)
        layout.addWidget(subtitle)

class DojoWidget(QWidget):
    def __init__(self, engine, switch_to_lobby_callback):
        super().__init__()
        self.engine = engine
        self.go_to_lobby = switch_to_lobby_callback
        
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setContentsMargins(50, 50, 50, 50)

        # 1. Info Label
        self.lbl_info = QLabel("INITIALIZING...")
        self.lbl_info.setFont(QFont(FONTS['ui'], 14))
        self.lbl_info.setStyleSheet(f"color: {COLORS['text_dim']}; letter-spacing: 2px;")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.lbl_info)
        self.layout.addSpacing(60)

        # 2. Equation Label
        self.lbl_problem = QLabel("...")
        self.lbl_problem.setFont(QFont(FONTS['equation'], 64, QFont.Bold))
        self.lbl_problem.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.lbl_problem)
        self.layout.addSpacing(40)

        # 3. Input Field
        self.input_field = QLineEdit()
        self.input_field.setFont(QFont(FONTS['equation'], 32))
        self.input_field.setAlignment(Qt.AlignCenter)
        self.input_field.setFixedWidth(400)
        self.input_field.textChanged.connect(self.check_input_length)
        self.layout.addWidget(self.input_field, 0, Qt.AlignCenter)
        self.layout.addSpacing(20)
        
        # 4. Feedback
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setFont(QFont(FONTS['ui'], 18))
        self.lbl_feedback.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.lbl_feedback)

    def refresh(self):
        self.engine.generate_new_problem()
        
        if self.engine.mode == "ADD":
            equation_str = " + ".join(str(x) for x in self.engine.current_terms)
        else:
            equation_str = f"{self.engine.current_terms[0]} - {self.engine.current_terms[1]}"
            
        self.lbl_problem.setText(equation_str)
        self.lbl_info.setText(self.engine.get_progress_text())
        
        self.input_field.blockSignals(True)
        self.input_field.clear()
        self.input_field.blockSignals(False)
        self.lbl_feedback.setText("")
        self.input_field.setFocus()

    def check_input_length(self, text):
        text = text.strip()
        if not text: return
        expected_len = len(str(self.engine.expected_ans))
        if len(text) >= expected_len:
            self.handle_submit(text)

    def handle_submit(self, text):
        is_correct, correct_val = self.engine.check_answer(text)
        if is_correct:
            self.flash_feedback("success")
            self.refresh()
        else:
            self.flash_feedback("error")
            self.lbl_feedback.setText(f"Correct: {correct_val}")
            self.lbl_feedback.setStyleSheet(f"color: {COLORS['error_text']}; font-weight: bold;")
            self.input_field.setDisabled(True)
            QTimer.singleShot(1500, self.after_error_delay)

    def after_error_delay(self):
        self.input_field.setDisabled(False)
        self.input_field.setFocus()
        self.refresh()

    def flash_feedback(self, mode):
        parent = self.window() 
        if parent:
            parent.flash_background(mode)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mental Dojo")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()
        
        # --- STYLE FIX: Force text color to white ---
        self.base_style = f"""
            QMainWindow {{ background-color: {COLORS['bg']}; }}
            QWidget {{ background-color: {COLORS['bg']}; }}
            QLabel {{ 
                color: {COLORS['text_main']}; 
                border: none; 
            }}
            QLineEdit {{ 
                color: {COLORS['accent']}; 
                background-color: {COLORS['input_bg']}; 
                border: 2px solid {COLORS['text_dim']}; 
                border-radius: 12px;
                padding: 12px;
            }}
        """
        self.setStyleSheet(self.base_style)

        self.engine = MathEngine()
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.lobby = LobbyWidget()
        self.dojo = DojoWidget(self.engine, self.switch_to_lobby)
        
        self.stack.addWidget(self.lobby)
        self.stack.addWidget(self.dojo)
        self.stack.setCurrentWidget(self.lobby)

    def switch_to_dojo(self, mode):
        self.engine.set_mode(mode)
        self.dojo.refresh()
        self.stack.setCurrentWidget(self.dojo)

    def switch_to_lobby(self):
        self.stack.setCurrentWidget(self.lobby)

    def flash_background(self, mode):
        tinted_bg = "#052005" if mode == "success" else "#200505"
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {tinted_bg}; }}
            QWidget {{ background-color: {tinted_bg}; }}
            QLabel {{ 
                color: {COLORS['text_main']}; 
                border: none; 
            }}
            QLineEdit {{ 
                color: {COLORS['accent']}; 
                background-color: {COLORS['input_bg']}; 
                border: 2px solid {COLORS['text_dim']}; 
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        QTimer.singleShot(400, lambda: self.setStyleSheet(self.base_style))

    def keyPressEvent(self, event: QKeyEvent):
        if self.stack.currentWidget() == self.lobby:
            if event.key() == Qt.Key_A:
                self.switch_to_dojo("ADD")
            elif event.key() == Qt.Key_S:
                self.switch_to_dojo("SUB")
            elif event.key() == Qt.Key_Escape:
                self.close()
        
        elif self.stack.currentWidget() == self.dojo:
            if event.key() == Qt.Key_Escape:
                self.switch_to_lobby()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())