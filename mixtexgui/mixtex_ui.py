# Renqing Luo
# Commercial use prohibited
import tkinter as tk
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem as item
import threading
from transformers import RobertaTokenizer, ViTImageProcessor
import onnxruntime as ort
import numpy as np
from PIL import ImageGrab
import pyperclip
import time
import sys
import os
import csv
import re
import ctypes
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['mathtext.fontset'] = 'cm'  # 公式预览使用 Computer Modern 字体

if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
    settings_dir = os.path.dirname(sys.executable)
else:
    base_path = os.path.abspath(".")
    settings_dir = os.path.abspath(".")
FONT_SETTINGS_FILE = os.path.join(settings_dir, 'font_settings.json')

class MixTeXApp:
    def __init__(self, root):
        self.root = root
        
        # 添加 DPI 感知支持 — 使用 tkinter 自身 API，PY 和 EXE 下行为一致
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        try:
            # winfo_fpixels('1i') 返回每英寸像素数，比 GetScaleFactorForDevice 更可靠
            pixels_per_inch = self.root.winfo_fpixels('1i')
            self.dpi_scale = pixels_per_inch / 96.0
            self.root.tk.call('tk', 'scaling', self.dpi_scale)
        except Exception as e:
            print(f"DPI 缩放获取失败: {e}")
            self.dpi_scale = 1.0
        
        # 加载字体设置（必须在创建控件之前）
        self.load_font_settings()

        self.root.title('MixTeX')
        self.root.resizable(True, True)
        self.root.overrideredirect(True)
        self.root.wm_attributes('-topmost', 1)
        self.root.attributes('-alpha', 0.85)
        self.root.minsize(self.scale_size(400), self.scale_size(300))
        self.TRANSCOLOUR = '#a9abc6'
        self.is_only_parse_when_show = False
        self.icon = self.load_scaled_image(os.path.join(base_path, "icon.png"))
        self.icon_tk = ImageTk.PhotoImage(self.icon)

        self.main_frame = tk.Frame(self.root, bg=self.TRANSCOLOUR)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.icon_label = tk.Label(self.main_frame, image=self.icon_tk, bg=self.TRANSCOLOUR)
        self.icon_label.pack(pady=self.scale_size(5))

        # OCR 状态指示
        self.status_label = tk.Label(self.main_frame, text="", bg=self.TRANSCOLOUR,
                                     fg='#666666', font=('Arial', self.scale_size(9)))
        self.status_label.pack()

        # 使用 PanedWindow 实现可拖拽分隔的文本区和预览区
        self.pane = tk.PanedWindow(self.main_frame, orient=tk.VERTICAL, bg='white',
                                   sashwidth=4, sashrelief=tk.RAISED)
        self.pane.pack(padx=self.scale_size(5), pady=self.scale_size(5), fill=tk.BOTH, expand=True)

        self.text_frame = tk.Frame(self.pane, bg='white', bd=1, relief=tk.SOLID)
        self.pane.add(self.text_frame, stretch='always')

        # 使用可配置的编辑器字体大小（含DPI缩放）
        font_size = self.scale_size(self.editor_font_size)
        self.text_box = tk.Text(self.text_frame, wrap=tk.WORD, bg='white', fg='black',
                               height=12, width=40, font=('Arial', font_size))
        self.text_box.pack(padx=self.scale_size(2), pady=self.scale_size(2), fill=tk.BOTH, expand=True)

        # 公式预览区域（初始隐藏，有结果时显示）
        self.preview_frame = tk.Frame(self.pane, bg='white', bd=1, relief=tk.SOLID)
        self.preview_label = tk.Label(self.preview_frame, bg='white')
        self.preview_label.pack(padx=self.scale_size(5), pady=self.scale_size(5))

        # 窗口拖拽（通过图标区域）
        self.icon_label.bind('<ButtonPress-1>', self.start_move)
        self.icon_label.bind('<B1-Motion>', self.do_move)
        self.icon_label.bind('<ButtonPress-3>', self.show_menu)
        self.icon_label.bind('<Double-Button-1>', self.toggle_ocr)

        # 编辑 LaTeX 后重新渲染预览（带防抖）
        self._edit_timer = None
        self.text_box.bind('<KeyRelease>', self._on_text_edit)

        # 窗口边缘缩放
        self.root.bind('<Motion>', self._on_mouse_move)
        self.root.bind('<ButtonPress-1>', self._on_button_press, add='+')
        self.root.bind('<B1-Motion>', self._on_drag, add='+')
        self.root.bind('<ButtonRelease-1>', self._on_release, add='+')
        self.root.bind('<Configure>', self._on_window_configure, add='+')
        # F2 切换 OCR 暂停/恢复
        self.root.bind_all('<F2>', self.toggle_ocr)
        self.root.bind('<Button-1>', self._on_click_focus, add='+')
        self.data_folder = "data"
        self.metadata_file = os.path.join(self.data_folder, "metadata.csv")
        self.use_dollars_for_inline_math = False
        self.convert_align_to_equations_enabled = False
        self.ocr_paused = False
        self.annotation_window = None
        self.current_image = None
        self.output = None
        self._last_rendered = None
        self._full_preview_image = None
        self._resize_data = None  # 边缘缩放状态
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)

        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['file_name', 'text', 'feedback'])

        # Create the menu
        self.menu = tk.Menu(self.root, tearoff=0)
        settings_menu = tk.Menu(self.menu, tearoff=0)
        settings_menu.add_checkbutton(label="$ 公式 $", onvalue=1, offvalue=0, command=self.toggle_latex_replacement, variable=tk.BooleanVar(value=self.use_dollars_for_inline_math))
        settings_menu.add_checkbutton(label="$$ 单行公式 $$", onvalue=1, offvalue=0, command=self.toggle_convert_align_to_equations, variable=tk.BooleanVar(value=self.convert_align_to_equations_enabled))
        settings_menu.add_command(label="字体设置", command=self.show_font_settings)
        self.menu.add_cascade(label="设置", menu=settings_menu)
        self.menu.add_command(label="反馈标注", command=self.show_feedback_options)
        self.menu.add_command(label="最小化", command=self.minimize)
        self.menu.add_command(label="关于", command=self.show_about)
        self.menu.add_command(label="打赏", command=self.show_donate)
        self.menu.add_command(label="退出", command=self.quit)
        if sys.platform == 'darwin':  # macOS
            self.root.config(menu=self.menu)
        else:  # Windows/Linux
            self.root.bind('<Button-3>', self.show_menu)
            self.root.wm_attributes("-transparentcolor", self.TRANSCOLOUR)

        self.create_tray_icon()

        self.model = self.load_model('onnx')
        if self.model is None:
            self.log("模型加载失败，部分功能将不可用")
            self.ocr_paused = True  # 暂停OCR功能
        else:
            self.ocr_thread = threading.Thread(target=self.ocr_loop, daemon=True)
            self.ocr_thread.start()

        # 初始化状态指示
        self.root.after(100, self.update_icon)

        self.donate_window = None

        self.is_only_parse_when_show = False
    
    def scale_size(self, size):
        """根据DPI缩放尺寸"""
        return int(size * self.dpi_scale)

    # ── 字体设置持久化 ─────────────────────────────────────
    def load_font_settings(self):
        """从文件加载字体设置"""
        try:
            if os.path.exists(FONT_SETTINGS_FILE):
                with open(FONT_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                self.editor_font_size = settings.get('editor_font_size', 16)
                self.preview_font_size = settings.get('preview_font_size', 28)
            else:
                self.editor_font_size = 16
                self.preview_font_size = 28
        except Exception:
            self.editor_font_size = 16
            self.preview_font_size = 28

    def save_font_settings(self):
        """保存字体设置到文件"""
        try:
            settings = {
                'editor_font_size': self.editor_font_size,
                'preview_font_size': self.preview_font_size,
            }
            with open(FONT_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存字体设置失败: {e}")

    def show_font_settings(self):
        """显示字体设置对话框"""
        win = tk.Toplevel(self.root)
        win.title("字体设置")
        win.overrideredirect(True)
        win.wm_attributes('-topmost', 1)
        win.configure(bg='white')

        # 居中于主窗口
        mx = self.root.winfo_x()
        my = self.root.winfo_y()
        mw = self.root.winfo_width()
        mh = self.root.winfo_height()
        dw, dh = 280, 200
        win.geometry(f"{dw}x{dh}+{mx + (mw - dw)//2}+{my + (mh - dh)//2}")

        frame = tk.Frame(win, bg='white', padx=20, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # 编辑器字体大小
        tk.Label(frame, text="编辑器字体大小:", bg='white',
                font=('Arial', 11)).pack(anchor='w')
        editor_var = tk.IntVar(value=self.editor_font_size)
        tk.Spinbox(frame, from_=8, to=48, textvariable=editor_var,
                  width=8, font=('Arial', 11)).pack(anchor='w', pady=(0, 10))

        # 预览字体大小
        tk.Label(frame, text="预览字体大小:", bg='white',
                font=('Arial', 11)).pack(anchor='w')
        preview_var = tk.IntVar(value=self.preview_font_size)
        tk.Spinbox(frame, from_=12, to=72, textvariable=preview_var,
                  width=8, font=('Arial', 11)).pack(anchor='w', pady=(0, 15))

        # 按钮区域
        btn_frame = tk.Frame(frame, bg='white')
        btn_frame.pack(fill=tk.X)

        def apply():
            new_editor = editor_var.get()
            new_preview = preview_var.get()
            if new_editor != self.editor_font_size or new_preview != self.preview_font_size:
                self.editor_font_size = new_editor
                self.preview_font_size = new_preview
                self.save_font_settings()
                # 更新编辑器字体
                self.text_box.config(font=('Arial', self.scale_size(self.editor_font_size)))
                # 强制重新渲染预览
                self._last_rendered = None
                if self.output:
                    self.update_preview()
            win.destroy()

        tk.Button(btn_frame, text="应用", command=apply,
                 bg='#e0e0e0', font=('Arial', 10)).pack(side='right', padx=(5, 0))
        tk.Button(btn_frame, text="取消", command=win.destroy,
                 bg='#e0e0e0', font=('Arial', 10)).pack(side='right')

    def load_scaled_image(self, image_path, custom_scale=None):
        """按DPI比例加载图像"""
        # 使用自定义缩放因子或系统DPI缩放
        scale = custom_scale if custom_scale is not None else getattr(self, 'dpi_scale', 1.0)
        
        # 确保路径存在
        if not os.path.exists(image_path):
            # 尝试查找替代路径
            alt_path = os.path.join(os.path.dirname(sys.executable), os.path.basename(image_path))
            if os.path.exists(alt_path):
                image_path = alt_path
            else:
                print(f"找不到图像文件: {image_path}")
                # 创建一个空白图像替代
                return Image.new('RGB', (64, 64), (200, 200, 200))
        
        # 加载原始图像
        original = Image.open(image_path)
        
        # 如果需要缩放
        if scale > 1.0:
            # 计算新尺寸
            new_size = (int(original.width * scale), int(original.height * scale))
            # 使用高质量缩放
            return original.resize(new_size, Image.LANCZOS)
        return original

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def show_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def save_data(self, image, text, feedback):
        file_name = f"{int(time.time())}.png"
        file_path = os.path.join(self.data_folder, file_name)
        image.save(file_path, 'PNG')

        rows = []
        with open(self.metadata_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        updated = False
        for row in rows[1:]:
            if row[1] == text:
                row[2] = feedback
                updated = True
                break

        if not updated:
            rows.append([file_name, text, feedback])

        with open(self.metadata_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def toggle_latex_replacement(self):
        self.use_dollars_for_inline_math = not self.use_dollars_for_inline_math

    def toggle_convert_align_to_equations(self):
        self.convert_align_to_equations_enabled = not self.convert_align_to_equations_enabled

    def minimize(self):
        self.root.withdraw()
        self.tray_icon.visible = True

    def show_about(self):
        about_text = "MixTeX\n版本: 3.2.4b \n作者: lrqlrqlrq \nQQ群：612725068 \nB站：bilibili.com/8922788 \nGithub:github.com/RQLuo"
        self.text_box.delete(1.0, tk.END)
        self.text_box.insert(tk.END, about_text)

    def show_donate(self):
        donate_text = "\n!!!感谢您的支持!!!\n"
        self.text_box.delete(1.0, tk.END)
        self.text_box.insert(tk.END, donate_text)

        donate_frame = tk.Frame(self.main_frame, bg='white')
        donate_frame.pack(padx=self.scale_size(5), pady=self.scale_size(5), fill=tk.BOTH, expand=True)

        # 加载并缩放打赏图像
        donate_size = self.scale_size(400)
        donate_image = self.load_scaled_image(os.path.join(base_path, "donate.png"))
        donate_image = donate_image.resize((donate_size, donate_size), Image.LANCZOS)
        donate_photo = ImageTk.PhotoImage(donate_image)

        image_label = tk.Label(donate_frame, image=donate_photo)
        image_label.image = donate_photo
        image_label.pack(expand=True, fill=tk.BOTH)

        close_button = tk.Button(donate_frame, text="☒", 
                                command=lambda: donate_frame.destroy())
        close_button.place(relx=1.0, rely=0.0, 
                          x=-self.scale_size(15), 
                          y=self.scale_size(5), 
                          width=self.scale_size(12), 
                          height=self.scale_size(12), 
                          anchor="ne")

    def quit(self):
        self.tray_icon.stop()
        self.root.quit()

    def only_parse_when_show(self):
        self.is_only_parse_when_show = not self.is_only_parse_when_show
        
    def create_tray_icon(self):
        menu = pystray.Menu(
            item('显示', self.show_window),
            item("开关只在最大化启用", self.only_parse_when_show),
            item('退出', self.quit)
        )

        self.tray_icon = pystray.Icon("MixTeX", self.icon, "MixTeX", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self):
        self.root.deiconify()
        self.tray_icon.visible = False

    def load_model(self, path):
        try:
            # 检查模型文件是否存在，优先查找外部onnx文件夹
            model_paths = [
                path,  # 原始路径（相对路径）
                os.path.join(os.path.dirname(sys.executable), 'onnx'),  # exe同目录下的onnx文件夹
                os.path.abspath("onnx"),  # 当前运行目录下的onnx文件夹
            ]

            # 向上搜索exe父目录中的onnx（适配dist/目录结构）
            exe_dir = os.path.dirname(sys.executable)
            for _ in range(4):
                exe_dir = os.path.dirname(exe_dir)
                model_paths.append(os.path.join(exe_dir, 'onnx'))
            
            # 添加脚本所在目录及上级目录下的onnx路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            model_paths.append(os.path.join(script_dir, 'onnx'))
            model_paths.append(os.path.join(os.path.dirname(script_dir), 'onnx'))

            # 寻找第一个有效的模型路径
            valid_path = None
            for model_path in model_paths:
                if os.path.exists(model_path):
                    # 检查必要文件是否都存在
                    required_files = [
                        os.path.join(model_path, "encoder_model.onnx"),
                        os.path.join(model_path, "decoder_model_merged.onnx"),
                        os.path.join(model_path, "tokenizer.json"),
                        os.path.join(model_path, "vocab.json")
                    ]
                    
                    all_files_exist = all(os.path.exists(file_path) for file_path in required_files)
                    if all_files_exist:
                        valid_path = model_path
                        self.log(f"使用模型路径: {valid_path}")
                        break
            
            if valid_path is None:
                self.log("找不到有效的模型文件")
                # 显示错误对话框
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, 
                    "找不到必要的模型文件\n请确保exe同目录下的onnx文件夹包含完整的模型文件。", 
                    "模型加载错误", 0)
                return None
                    
            tokenizer = RobertaTokenizer.from_pretrained(valid_path)
            feature_extractor = ViTImageProcessor.from_pretrained(valid_path)
            encoder_session = ort.InferenceSession(f"{valid_path}/encoder_model.onnx", providers=['CPUExecutionProvider'])
            decoder_session = ort.InferenceSession(f"{valid_path}/decoder_model_merged.onnx", providers=['CPUExecutionProvider'])
            self.log('\n===成功加载模型===\n')
            return (tokenizer, feature_extractor, encoder_session, decoder_session)
        except Exception as e:
            self.log(f"模型加载失败: {e}")
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, 
                f"模型加载失败: {str(e)}\n请确保exe同目录下的onnx文件夹包含完整的模型文件。", 
                "模型加载错误", 0)
            return None

    def show_feedback_options(self):
        feedback_menu = tk.Menu(self.menu, tearoff=0)
        feedback_menu.add_command(label="完美", command=lambda: self.handle_feedback("Perfect"))
        feedback_menu.add_command(label="普通", command=lambda: self.handle_feedback("Normal"))
        feedback_menu.add_command(label="失误", command=lambda: self.handle_feedback("Mistake"))
        feedback_menu.add_command(label="错误", command=lambda: self.handle_feedback("Error"))
        feedback_menu.add_command(label="标注", command=self.add_annotation)
        feedback_menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())

    def handle_feedback(self, feedback_type):
        image = self.current_image
        text = self.output
        if image and text:
            if self.check_repetition(text):
                self.log("反馈已记录: Repeat")
            else:
                self.save_data(image, text, feedback_type)
                self.log(f"反馈已记录: {feedback_type}")
        else:
            self.log("反馈无法记录: 缺少图片或者推理输出")

    def add_annotation(self):
        if self.annotation_window is not None:
            return  # If there's already an annotation window, do nothing

        self.annotation_window = tk.Toplevel(self.root)
        self.annotation_window.wm_attributes("-alpha", 0.85)
        self.annotation_window.overrideredirect(True)
        self.annotation_window.wm_attributes('-topmost', 1)

        self.update_annotation_position()

        # 使用缩放后的字体
        font_size = self.scale_size(11)
        entry = tk.Entry(self.annotation_window, width=45, font=('Arial', font_size))
        entry.pack(padx=self.scale_size(10), pady=self.scale_size(10))
        entry.focus_set()

        confirm_button = tk.Button(self.annotation_window, text="确认",
                                   command=lambda: self.confirm_annotation(entry))
        confirm_button.pack(pady=(0, self.scale_size(10)))

        # Close the window on moving the main window
        self.root.bind('<Configure>', lambda e: self.update_annotation_position())

    def confirm_annotation(self, entry):
        annotation = entry.get()
        image = self.current_image
        text = self.output
        if annotation and image and text:
            self.handle_feedback(f"Annotation: {annotation}")
            self.log(f"标注已添加: {annotation}")
        else:
            self.log("反馈无法记录: 缺少图片或推理输出或输入标注。")
        self.close_annotation()

    def update_annotation_position(self):
        if self.annotation_window:
            x = self.root.winfo_x() + self.scale_size(10)
            y = self.root.winfo_y() + self.root.winfo_height() + self.scale_size(10)
            self.annotation_window.geometry(f"+{x}+{y}")

    def close_annotation(self):
        if self.annotation_window:
            self.annotation_window.destroy()
        self.annotation_window = None

    def check_repetition(self, s, repeats=12):
        for pattern_length in range(1, len(s) // repeats + 1):
            for start in range(len(s) - repeats * pattern_length + 1):
                pattern = s[start:start + pattern_length]
                if s[start:start + repeats * pattern_length] == pattern * repeats:
                    return True
        return False

    def mixtex_inference(self, max_length, num_layers, hidden_size, num_attention_heads, batch_size):
        tokenizer, feature_extractor, encoder_session, decoder_session = self.model
        try:
            generated_text = ""
            head_size = hidden_size // num_attention_heads
            inputs = feature_extractor(self.current_image, return_tensors="np").pixel_values
            encoder_outputs = encoder_session.run(None, {"pixel_values": inputs})[0]
            
         
            num_layers = 6  # 修改为6层而不是3层
            
            decoder_inputs = {
                "input_ids": tokenizer("<s>", return_tensors="np").input_ids.astype(np.int64),
                "encoder_hidden_states": encoder_outputs,
                "use_cache_branch": np.array([True], dtype=bool),
                **{f"past_key_values.{i}.{t}": np.zeros((batch_size, num_attention_heads, 0, head_size), dtype=np.float32) 
                for i in range(num_layers) for t in ["key", "value"]}
            }
            for _ in range(max_length):
                decoder_outputs = decoder_session.run(None, decoder_inputs)
                next_token_id = np.argmax(decoder_outputs[0][:, -1, :], axis=-1)
                generated_text += tokenizer.decode(next_token_id, skip_special_tokens=True)
                self.log(tokenizer.decode(next_token_id, skip_special_tokens=True), end="")
                if self.check_repetition(generated_text, 21):
                    self.log('\n===?!重复重复重复!?===\n')
                    self.save_data(self.current_image, generated_text, 'Repeat')
                    break
                if next_token_id == tokenizer.eos_token_id:
                    self.log('\n===成功复制到剪切板===\n')
                    break

                decoder_inputs.update({
                    "input_ids": next_token_id[:, None],
                    **{f"past_key_values.{i}.{t}": decoder_outputs[i*2+1+j] 
                    for i in range(num_layers) for j, t in enumerate(["key", "value"])}
                })
            if self.convert_align_to_equations_enabled:
                generated_text = self.convert_align_to_equations(generated_text)
            return generated_text
        except Exception as e:
            self.log(f"Error during OCR: {e}")
            return ""

    def convert_align_to_equations(self, text):
        text = re.sub(r'\\begin\{align\*\}|\\end\{align\*\}', '', text).replace('&','')
        equations = text.strip().split('\\\\')
        converted = []
        for eq in equations:
            eq = eq.strip().replace('\\[','').replace('\\]','').replace('\n','')
            if eq:
                converted.append(f"$$ {eq} $$")
        return '\n'.join(converted)

    def pad_image(self, img, out_size):
        x_img, y_img = out_size
        background = Image.new('RGB', (x_img, y_img), (255, 255, 255))
        width, height = img.size
        if width < x_img and height < y_img:
            x = (x_img - width) // 2
            y = (y_img - height) // 2
            background.paste(img, (x, y))
        else:
            scale = min(x_img / width, y_img / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img_resized = img.resize((new_width, new_height), Image.LANCZOS)
            x = (x_img - new_width) // 2
            y = (y_img - new_height) // 2
            background.paste(img_resized, (x, y))
        return background

    def ocr_loop(self):
        while True:
            if not self.ocr_paused and (self.tray_icon.visible or not self.is_only_parse_when_show):
                try:
                    image = ImageGrab.grabclipboard()
                    if image is not None and type(image) != list:
                        self.current_image = self.pad_image(image.convert("RGB"), (448,448))
                        result = self.mixtex_inference(512, 3, 768, 12, 1)
                        result = result.replace('\\[', '\\begin{align*}').replace('\\]', '\\end{align*}').replace('%', '\\%')
                        self.output = result
                        if self.use_dollars_for_inline_math:
                            result = result.replace('\\(', '$').replace('\\)', '$')
                        pyperclip.copy(result)
                        self.root.after(0, self.update_preview)
                        # OCR 完成后用干净结果替换文本框内容（方便编辑和重新渲染）
                        self.root.after(0, lambda r=result: self._show_clean_result(r))
                except Exception as e:
                    self.log(f"Error: {e}")
                time.sleep(0.1)

    def _on_click_focus(self, event):
        """点击窗口时获取键盘焦点"""
        self.root.focus_set()

    def toggle_ocr(self, event=None):
        self.ocr_paused = not self.ocr_paused
        self.root.after(0, self.update_icon)
        print(f"OCR {'paused' if self.ocr_paused else 'resumed'} (F2)")

    def update_icon(self):
        if self.ocr_paused:
            new_icon = self.load_scaled_image(os.path.join(base_path, "icon_gray.png"))
            self.status_label.config(text="● OCR 已暂停（双击图标恢复）", fg='#cc0000')
        else:
            new_icon = self.load_scaled_image(os.path.join(base_path, "icon.png"))
            self.status_label.config(text="● OCR 运行中（双击图标暂停）", fg='#009900')
        self.icon = new_icon
        self.icon_tk = ImageTk.PhotoImage(self.icon)
        self.icon_label.config(image=self.icon_tk)
        self.tray_icon.icon = self.icon

    def render_latex_to_image(self, latex_str):
        """将LaTeX渲染为PIL图片"""
        try:
            if not latex_str or not latex_str.strip():
                return None

            tex = latex_str
            # 清理环境命令
            for env in ['align*', 'aligned', 'equation*', 'equation', 'gather*', 'gather']:
                tex = tex.replace(f'\\begin{{{env}}}', '')
                tex = tex.replace(f'\\end{{{env}}}', '')
            tex = tex.replace('\\[', '').replace('\\]', '')
            tex = tex.replace('&', ' ')
            tex = tex.strip('\n ')

            if not tex:
                return None

            lines = [l.strip() for l in tex.split('\\\\') if l.strip()]
            if not lines:
                return None

            rendered_lines = []
            for line in lines:
                fig = plt.figure(figsize=(12, 1.2))
                fig.patch.set_facecolor('white')
                fig.text(0.5, 0.5, f'${line}$', fontsize=self.preview_font_size,
                        ha='center', va='center')

                fig.canvas.draw()
                w, h = fig.canvas.get_width_height()
                # matplotlib 3.9+ 使用 buffer_rgba 替代 tostring_rgb
                buf = np.asarray(fig.canvas.buffer_rgba())
                img = Image.fromarray(buf, 'RGBA').convert('RGB')
                plt.close(fig)
                rendered_lines.append(img)

            if len(rendered_lines) == 1:
                return rendered_lines[0]

            total_h = sum(im.height for im in rendered_lines)
            max_w = max(im.width for im in rendered_lines)
            combined = Image.new('RGB', (max_w, total_h), (255, 255, 255))
            y = 0
            for im in rendered_lines:
                combined.paste(im, ((max_w - im.width) // 2, y))
                y += im.height
            return combined

        except Exception as e:
            print(f"公式渲染失败: {e}")
            return None

    def update_preview(self):
        """OCR 结果更新后渲染并显示预览"""
        if not self.output or self.output == self._last_rendered:
            return

        rendered = self.render_latex_to_image(self.output)
        if rendered:
            self._full_preview_image = rendered
            self._last_rendered = self.output
            self._display_preview()
        else:
            self._full_preview_image = None
            self._hide_preview()

    def _display_preview(self):
        """将缓存的预览图缩放到当前窗口宽度并显示"""
        if not self._full_preview_image:
            self._hide_preview()
            return

        # 确保布局已就绪，否则取一个合理的默认宽度
        frame_w = self.text_frame.winfo_width()
        if frame_w <= 1:
            frame_w = self.root.winfo_width() or self.scale_size(500)
        avail_width = max(self.scale_size(500), frame_w - self.scale_size(10))

        img = self._full_preview_image
        if img.width > avail_width:
            ratio = avail_width / img.width
            img = img.resize((avail_width, int(img.height * ratio)), Image.LANCZOS)

        self._preview_photo = ImageTk.PhotoImage(img)
        self.preview_label.config(image=self._preview_photo)
        if not self.preview_frame.winfo_ismapped():
            self._show_preview()
        else:
            # 窗口缩放时维持分割线比例，避免预览区"移动"
            self.root.after_idle(self._set_preview_sash)

    def _hide_preview(self):
        """从 PanedWindow 中移除预览区域"""
        try:
            self.pane.forget(self.preview_frame)
        except tk.TclError:
            pass

    def _show_preview(self):
        """将预览区域添加到 PanedWindow 并设置分割线位置"""
        self.pane.add(self.preview_frame, stretch='never')
        self.pane.after_idle(self._set_preview_sash)

    def _set_preview_sash(self):
        """设置分割线位置：文本区约占65%"""
        try:
            h = self.pane.winfo_height()
            if h > 0:
                self.pane.sash_place(0, 0, int(h * 0.65))
        except Exception:
            pass

    # ── 窗口边缘缩放 ──────────────────────────────────────────
    RESIZE_MARGIN = 6
    MIN_WINDOW_WIDTH = 400
    MIN_WINDOW_HEIGHT = 300

    def _get_resize_edges(self, event):
        """判断鼠标是否在窗口边缘热区，返回 (cursor, edges_tuple)"""
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x, y = event.x, event.y
        left = x < self.RESIZE_MARGIN
        right = x > w - self.RESIZE_MARGIN
        top = y < self.RESIZE_MARGIN
        bottom = y > h - self.RESIZE_MARGIN

        if left and top:    return 'size_nw_se', ('nw',)
        if left and bottom: return 'size_ne_sw', ('sw',)
        if right and top:   return 'size_ne_sw', ('ne',)
        if right and bottom:return 'size_nw_se', ('se',)
        if left:            return 'size_we', ('w',)
        if right:           return 'size_we', ('e',)
        if top:             return 'size_ns', ('n',)
        if bottom:          return 'size_ns', ('s',)
        return None, None

    def _on_mouse_move(self, event):
        """鼠标移动时更新光标形状"""
        cursor, _ = self._get_resize_edges(event)
        self.root.config(cursor=cursor or '')

    def _on_button_press(self, event):
        """鼠标按下 — 仅处理边缘缩放，不接管拖拽"""
        _, edges = self._get_resize_edges(event)
        if edges:
            self._resize_data = {
                'edges': edges,
                'sx': event.x_root, 'sy': event.y_root,
                'wx': self.root.winfo_x(), 'wy': self.root.winfo_y(),
                'ww': self.root.winfo_width(), 'wh': self.root.winfo_height(),
            }

    def _on_drag(self, event):
        """鼠标拖拽 — 仅处理边缘缩放"""
        if not self._resize_data:
            return
        d = self._resize_data
        dx = event.x_root - d['sx']
        dy = event.y_root - d['sy']

        x, y = d['wx'], d['wy']
        w, h = d['ww'], d['wh']

        if 'e' in d['edges']: w = max(self.scale_size(self.MIN_WINDOW_WIDTH), d['ww'] + dx)
        if 'w' in d['edges']:
            w = max(self.scale_size(self.MIN_WINDOW_WIDTH), d['ww'] - dx)
            x = d['wx'] + (d['ww'] - w)
        if 's' in d['edges']: h = max(self.scale_size(self.MIN_WINDOW_HEIGHT), d['wh'] + dy)
        if 'n' in d['edges']:
            h = max(self.scale_size(self.MIN_WINDOW_HEIGHT), d['wh'] - dy)
            y = d['wy'] + (d['wh'] - h)

        self.root.geometry(f'{w}x{h}+{x}+{y}')

    def _on_release(self, event):
        """鼠标释放 — 结束缩放"""
        self._resize_data = None

    # ── 窗口缩放时更新预览 ──────────────────────────────────────
    def _on_window_configure(self, event):
        if event.widget == self.root and self._full_preview_image:
            # 只在尺寸真正变化时才重新缩放预览，避免拖拽移动窗口时重复触发
            cur = (event.width, event.height)
            if not hasattr(self, '_last_win_size') or self._last_win_size != cur:
                self._last_win_size = cur
                self.root.after_idle(self._display_preview)

    # ── OCR 完成后只保留干净 LaTeX ─────────────────────────────
    def _show_clean_result(self, latex):
        """清空文本框，只显示可编辑的干净 LaTeX"""
        self.text_box.delete(1.0, tk.END)
        self.text_box.insert(tk.END, latex)

    # ── 编辑 LaTeX 后重新渲染预览 ──────────────────────────────
    def _on_text_edit(self, event=None):
        """用户编辑文本框后防抖重新渲染预览"""
        if self._edit_timer:
            self.root.after_cancel(self._edit_timer)
        self._edit_timer = self.root.after(500, self._do_render_from_text)

    def _do_render_from_text(self):
        """读取文本框内容并更新预览"""
        self._edit_timer = None
        new_text = self.text_box.get(1.0, tk.END).strip()
        if new_text and new_text != self._last_rendered:
            self.output = new_text
            self._last_rendered = None  # 强制重新渲染
            self.update_preview()

    def log(self, message, end='\n'):
        self.text_box.insert(tk.END, message + end)
        self.text_box.see(tk.END)

if __name__ == '__main__':
    try:
        root = tk.Tk()
        app = MixTeXApp(root)
        root.mainloop()
    except Exception as e:
        # 创建错误日志文件
        with open('error_log.txt', 'w') as f:
            import traceback
            f.write(str(e) + '\n')
            f.write(traceback.format_exc())
        # 显示错误窗口
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f"程序启动失败: {str(e)}\n详细信息已保存到error_log.txt", "错误", 0)