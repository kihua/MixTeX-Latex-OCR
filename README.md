
<p align="center">
  <a href="#english">English</a> | <a href="#中文">中文</a>
</p>

![](demo/icon.png)

---

<span id="english"></span>

# MixTeX - Multimodal LaTeX OCR with CPU Inference

[![Paper](https://img.shields.io/badge/Paper-arxiv.2406.17148-white)](https://arxiv.org/abs/2406.17148)
<a href="https://colab.research.google.com/github/RQLuo/MixTeX/blob/main/MixTex_Demo.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Community%20Space-blue)](https://huggingface.co/MixTex/ZhEn-Latex-OCR)
[![Demo Video](https://img.shields.io/badge/%F0%9F%93%BA%20Demo-Video-white)](https://www.youtube.com/watch?v=PqQdQ5xT-vk)

MixTeX is a multimodal LaTeX recognition application that performs efficient CPU-based inference locally, offline. Whether it's LaTeX formulas, tables, or mixed text, MixTeX can recognize them with bilingual support for Chinese and English.

## Features

- **LaTeX Formula Recognition**: Accurately recognizes complex LaTeX mathematical formulas.
- **Table Recognition**: Processes and recognizes various tables, generating corresponding LaTeX code.
- **Mixed Text Recognition**: Simultaneously handles text containing words, formulas, and tables.
- **Bilingual Support**: High-precision recognition for both Chinese and English.

## GUI Features

- **Real-time Formula Preview**: Renders recognized LaTeX in real-time using Computer Modern font (the classic LaTeX typeface).
- **Editable LaTeX**: The recognized LaTeX can be edited directly; the preview updates automatically after 500ms.
- **Free-form Window Resizing**: Drag any edge or corner of the window to resize freely.
- **Adjustable Font Sizes**: Configure editor and preview font sizes independently via right-click menu → Settings → Font Settings.
- **Draggable Preview Splitter**: Adjust the ratio between the LaTeX editor and formula preview by dragging the divider.
- **Clipboard Monitoring**: Automatically recognizes images copied to the clipboard.
- **System Tray**: Minimizes to system tray for background operation.

## Quick Start (Pre-built EXE)

1. Download the latest `MixTeX.exe` from the [Releases](https://github.com/RQLuo/MixTeX/releases) page.
2. Download the model files and place the `onnx` folder next to `MixTeX.exe`. Models are available on [Hugging Face](https://huggingface.co/MixTex/ZhEn-Latex-OCR).
3. Run `MixTeX.exe` — the app starts immediately in the system tray. Copy an image with LaTeX content to your clipboard and the recognition result appears automatically.

## Source Code Setup

*Make sure you have read the user agreement before starting.*

1. Navigate to the `mixtexgui` directory: `cd mixtexgui`
2. Create a Conda environment: `conda create -n mixtex python=3.10.14`
3. Activate the environment: `conda activate mixtex`
4. Install dependencies: `pip install -r requirements.txt`
5. Run directly: `python mixtex_ui.py`
6. Build executable: `pyinstaller mixtex_ui.spec`

## Model Setup

Download the model from [Hugging Face](https://huggingface.co/MixTex/ZhEn-Latex-OCR) and place the `onnx` folder:
- Next to `MixTeX.exe` (for EXE mode)
- In the `mixtexgui` directory (for script mode)

Required files:
- `encoder_model.onnx`
- `decoder_model_merged.onnx`
- `tokenizer.json`
- `vocab.json`

## Technical Characteristics

- **Local Offline Inference**: No internet required, ensuring data privacy.
- **Lightweight**: Startup file ~90 MB (EXE with all dependencies bundled).
- **Efficient CPU Operation**: Runs on any Windows computer without GPU.
- **ONNX Runtime**: Uses ONNX for inference instead of PyTorch, reducing package size and improving compatibility.

## Usage Guide

1. **Keyboard Shortcut**: Click the app icon then press `F2` to toggle OCR on/off.
2. **Clipboard Recognition**: Copy an image (`Ctrl+C`) to the clipboard — MixTeX recognizes it automatically.
3. **Right-click Menu**:
   - Settings: Toggle `$` inline math mode, configure font sizes.
   - Feedback & Annotation: Label recognition results for quality tracking.
   - Minimize: Send to system tray.

## Demo

MixTeX excels at recognizing complex text, with strong performance in both English and Chinese.

![](demo/1.gif)

![](demo/3.png)

![](demo/2.png)

## Environment Requirements

MixTeX uses LaTeX for code rendering. Recommended LaTeX preamble:

```latex
\documentclass{ctexart}
\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{stmaryrd}
\usepackage{color}
```

## Limitations

- Currently supports clear printed fonts for Chinese/English mixed formulas and relatively simple tables.
- Handwritten text and complex tables are not yet supported.
- The training dataset is largely synthetic, which may affect recognition robustness in real-world scenarios.

## Changelog

- **v3.2.4+**: Added real-time formula preview (Computer Modern font), resizable borderless window with edge-drag, adjustable font sizes, draggable preview/text splitter, editable LaTeX with auto-re-render.`F2` toggles recognition.

- **v3.2.4**: Fine-tuned 500 real samples. Supports multiple-choice question OCR. Press `F2` after clicking the app icon to toggle recognition. Improved escaping of multi-line and inline formulas into `$$` wrappers.

- **v2.2.3**: Fine-tuned on 150 real manuscripts + 300. Supports handwritten text mixed with formulas and black backgrounds.

- **v2.1.2**: Synthesized handwriting dataset, fine-tuned on 100 real manuscripts. Partially supports handwritten text mixed with formulas.

- **v1.1.2**: Added data collection, fine-tuned on 300 real samples. Optimized curly bracket and table recognition.

- **v1.0.2**: Fixed RGB color space issue for advanced displays.

- **v1.0.1**: Fixed file copy conflict warning.

## User Agreement

MixTeX is permanently free software. It operates fully offline with no advertisements. By using this software, you agree to the terms outlined in the user agreement.

## Contact

- QQ Group: 612725068
- Bilibili: [bilibili.com/8922788](https://bilibili.com/8922788)
- GitHub: [github.com/RQLuo](https://github.com/RQLuo)

![donate](https://github.com/user-attachments/assets/9f52a771-ab84-466c-9a7e-629060e251cc)

---

<span id="中文"></span>

# MixTeX - 多模态 LaTeX OCR 本地 CPU 推理

[![Paper](https://img.shields.io/badge/Paper-arxiv.2406.17148-white)](https://arxiv.org/abs/2406.17148)
<a href="https://colab.research.google.com/github/RQLuo/MixTeX/blob/main/MixTex_Demo.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Community%20Space-blue)](https://huggingface.co/MixTex/ZhEn-Latex-OCR)
[![Demo Vedio](https://img.shields.io/badge/%F0%9F%93%BA%20Demo-Vedio-white)](https://www.bilibili.com/video/BV1hS42197Vp/)

MixTeX 是一款多模态 LaTeX 识别程序，能够在本地离线环境下进行高效的 CPU 推理。无论是 LaTeX 公式、表格，还是混合文字，MixTeX 都能轻松识别，支持中英文双语处理。

## 主要功能

- **LaTeX 公式识别**：精准识别复杂的 LaTeX 数学公式。
- **表格识别**：高效处理并识别各类表格，生成对应的 LaTeX 表格代码。
- **混合文字识别**：同时处理包含文字、公式和表格的混合文本。
- **中英文双语支持**：高精度识别中文和英文。

## GUI 功能

- **实时公式预览**：使用 Computer Modern 字体（经典 LaTeX 字体）实时渲染识别结果。
- **可编辑 LaTeX**：识别结果可直接编辑，编辑后 500ms 自动重新渲染预览。
- **自由缩放窗口**：拖拽窗口任意边缘或角自由调整大小。
- **字体大小可调**：右键菜单 → 设置 → 字体设置，独立调节编辑器和预览字体大小。
- **可拖拽分割线**：拖动编辑区和预览区之间的分割线自由调整比例。
- **剪切板监控**：自动识别复制到剪切板的图片。
- **系统托盘**：最小化到系统托盘后台运行。

## 快速开始（预编译 EXE）

1. 从 [Releases](https://github.com/RQLuo/MixTeX/releases) 页面下载最新的 `MixTeX.exe`。
2. 下载模型文件，将 `onnx` 文件夹放在 `MixTeX.exe` 同目录下。模型下载：[Hugging Face](https://huggingface.co/MixTex/ZhEn-Latex-OCR)。
3. 运行 `MixTeX.exe` — 程序启动后自动最小化到系统托盘。复制包含 LaTeX 的图片到剪切板即可自动识别。

## 源码运行

1. 进入 `mixtexgui` 目录：`cd mixtexgui`
2. 创建 Conda 环境：`conda create -n mixtex python=3.10.14`
3. 激活环境：`conda activate mixtex`
4. 安装依赖：`pip install -r requirements.txt`
5. 直接运行：`python mixtex_ui.py`
6. 打包 EXE：`pyinstaller mixtex_ui.spec`

## 模型设置

从 [Hugging Face](https://huggingface.co/MixTex/ZhEn-Latex-OCR) 下载模型，将 `onnx` 文件夹放置在：
- `MixTeX.exe` 同目录（EXE 模式）
- `mixtexgui` 目录下（源码模式）

必要文件：
- `encoder_model.onnx`
- `decoder_model_merged.onnx`
- `tokenizer.json`
- `vocab.json`

## 技术特点

- **本地离线推理**：无需联网，保证数据隐私安全。
- **轻量化设计**：启动程序约 90 MB（EXE 包含全部依赖）。
- **高效 CPU 运行**：无需 GPU，适合所有 Windows 电脑。
- **ONNX Runtime**：使用 ONNX 替代 PyTorch 推理，减小打包体积，提高兼容性。

## 使用指南

1. **快捷键**：点击应用图标后按 `F2` 开关 OCR 识别。
2. **剪切板识别**：复制图片（`Ctrl+C`）到剪切板，MixTeX 自动识别。
3. **右键菜单**：
   - 设置：切换 `$` 行内公式模式，配置字体大小。
   - 反馈标注：标注识别结果质量。
   - 最小化：发送到系统托盘。

## 效果展示

MixTeX 在识别复杂文本方面表现出色，中英文识别效果俱佳。

![](demo/1.gif)

![](demo/3.png)

![](demo/2.png)

## 环境要求

推荐 LaTeX 配置：

```latex
\documentclass{ctexart}
\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{stmaryrd}
\usepackage{color}
```

## 局限性

- 目前只支持清晰打印字体的中英文混合公式及较为简单的表格。
- 暂不支持手写体和复杂表格。
- 训练数据集多为伪造生成，现实场景下的鲁棒性可能受影响。

## 更新日志

- **v3.2.4+**：新增实时公式预览（Computer Modern 字体）、自由缩放窗口（边缘拖拽）、字体大小设置、可拖拽编辑/预览分割线、可编辑 LaTeX 自动重渲染。`F2` 开关识别。

- **v3.2.4**：微调 500 张真实样本，支持选择题 OCR，支持 F2 暂停/恢复识别，改进了多行公式和行内公式的 `$$` 转义。

- **v2.2.3**：微调 150 张真实手写稿 + 300 张，支持手写文字混合公式及黑底白字。

- **v2.1.2**：合成手写数据集，微调 100 张真实手稿，部分支持手写文字混合公式。

- **v1.1.2**：添加数据收集功能，微调 300 张真实小样本，优化花括号和表格识别。

- **v1.0.2**：修复个别高级显示器色彩格式不兼容问题。

- **v1.0.1**：修复运行中复制文件导致的警告问题。

## 用户协议

MixTeX 作为永久免费软件，承诺持续优化并保持本地离线运行，无任何广告干扰。

## 联系我们

- QQ群：612725068
- B站：[bilibili.com/8922788](https://bilibili.com/8922788)
- GitHub：[github.com/RQLuo](https://github.com/RQLuo)

![image](https://github.com/user-attachments/assets/4981867a-8d6f-4583-b7ab-a95a10ca71ca)
