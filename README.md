# QEditToolkit 🎬

**QEditToolkit** là một ứng dụng desktop chuyên nghiệp dành cho những người làm video editing. Nó cung cấp bộ công cụ quản lý asset, tổ chức dự án và hỗ trợ các mẫu dự án tiêu chuẩn cho các loại video khác nhau.

## 📋 Mục Lục

- [Giới Thiệu](#giới-thiệu)
- [Tính Năng Chính](#tính-năng-chính)
- [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
- [Cài Đặt](#cài-đặt)
- [Hướng Dẫn Sử Dụng](#hướng-dẫn-sử-dụng)
  - [Quản Lý Asset](#quản-lý-asset)
  - [Tạo Dự Án Mới](#tạo-dự-án-mới)
- [Cấu Trúc Dự Án](#cấu-trúc-dự-án)
- [Kiến Trúc Ứng Dụng](#kiến-trúc-ứng-dụng)
- [Troubleshooting](#troubleshooting)
- [Đóng Góp](#đóng-góp)
- [Giấy Phép](#giấy-phép)

---

## 🎯 Giới Thiệu

QEditToolkit được phát triển để giải quyết bài toán quản lý tài nguyên, tổ chức cấu trúc dự án và tự động hóa quy trình setup cho các video editor. Ứng dụng hỗ trợ:

- 📦 **Quản lý thư viện asset** (video, hình ảnh, âm thanh, file DaVinci)
- 📁 **Tạo cấu trúc dự án** theo các mẫu chuẩn
- 🔍 **Tìm kiếm và phân loại** asset nhanh chóng
- 💾 **Lưu trữ tập trung** với database SQLite
- 🎨 **Giao diện Dark Theme** hiện đại

---

## ✨ Tính Năng Chính

### 1. **DVR Asset Manager**

- Nhập file từ máy tính vào thư viện
- Tìm kiếm asset theo tên
- Phân loại asset theo thư mục
- Đánh dấu yêu thích (⭐ Favorites)
- Xem preview hình ảnh/video
- Xoá asset và quản lý thư mục

### 2. **Dynamic Project Generator** 🆕

- **4 Mẫu Dự Án:**
  - 🎬 **Vlog** - Cho video YouTube
  - 📱 **Shorts/Reels** - Cho TikTok & Instagram
  - 💍 **Wedding** - Cho video cưới
  - 🎉 **Event** - Cho sự kiện
- Tạo tên dự án tự động: `YYYYMMDD_PREFIX_ProjectName`
- Tự động tạo cấu trúc thư mục
- Tạo file README.txt với thông tin dự án
- Live preview đường dẫn dự án

### 3. **Deep Link DaVinci Resolve** 🎬 (NEW)

- **Sync Folder Structure to Bins:**
  - Quét cấu trúc thư mục dự án
  - Tự động tạo Bins trong DaVinci Resolve
  - Import media files vào đúng vị trí
  - Tiết kiệm thời gian setup

- **Quick Import to Timeline:**
  - Double-click file để gửi vào Timeline
  - Right-click → "Send to Timeline"
  - File tự bay vào vị trí con trỏ hiện tại
  - Hỗ trợ video, audio, ảnh

### 4. **Database Management**

- SQLite database để lưu metadata asset
- Quản lý category tự động
- Hỗ trợ search toàn văn

---

## 🖥️ Yêu Cầu Hệ Thống

### Phần Cứng

- CPU: Intel i5 / AMD Ryzen 5 (hoặc tương đương)
- RAM: 8GB trở lên
- Ổ cứng: 100GB không gian trống cho asset
- Màn hình: 1024x768 trở lên (khuyến nghị 1920x1080)

### Phần Mềm

- **Python**: 3.9 hoặc cao hơn
- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **PyQt6**: Tự cài đặt qua dependencies

---

## 📦 Cài Đặt

### 1. Clone Repository

```bash
git clone https://github.com/QuocGP99/QEditToolkit.git
cd QEditToolkit
```

### 2. Tạo Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Cài Đặt Dependencies

```bash
pip install -r requirements.txt
```

### 4. Chạy Ứng Dụng

```bash
python main.py
```

---

## 🚀 Hướng Dẫn Sử Dụng

### Quản Lý Asset

#### **Nhập Asset**

1. Nhấp nút **"Import Asset"** ở thanh công cụ trên
2. Chọn file muốn thêm (hỗ trợ video, hình ảnh, âm thanh, file DaVinci)
3. Chọn thư mục đích hoặc để trống để lưu vào gốc
4. Asset sẽ được sao chép vào thư mục `storage/`

#### **Tìm Kiếm Asset**

- Gõ tên asset vào ô "Search assets..." để tìm kiếm real-time
- Kết quả sẽ cập nhật tự động

#### **Phân Loại**

- Nhấp vào thư mục ở panel **FOLDERS** bên trái để xem asset theo category
- Nhấp **"All Assets"** để xem tất cả

#### **Yêu Thích**

- Nhấp nút ⭐ trên asset để đánh dấu
- Xem danh sách yêu thích qua nút **"⭐ Favorites"**

#### **Xoá Asset**

- Right-click thư mục → **"Delete Folder"**
- Xác nhận, asset và thư mục sẽ bị xoá vĩnh viễn

### Tạo Dự Án Mới

#### **Sử Dụng Project Generator**

1. Nhấp nút **"📁 New Project"** trên sidebar
2. **Chọn Template:**
   - 🎬 Vlog - YouTube videos
   - 📱 Shorts/Reels - TikTok & Instagram
   - 💍 Wedding - Wedding videos
   - 🎉 Event - Event coverage

3. **Nhập Project Name:**
   - Ví dụ: "Da Lat Trip", "Wedding Day", etc.
   - Spaces sẽ được chuyển thành underscores

4. **Chọn Parent Directory:**
   - Nhấp **Browse** để chọn nơi lưu dự án
   - Preview sẽ hiển thị đường dẫn đầy đủ

5. **Tạo Project:**
   - Nhấp **Create Project**
   - Ứng dụng sẽ:
     - Tạo folder: `YYYYMMDD_PREFIX_ProjectName`
     - Tạo cấu trúc thư mục tự động
     - Tạo file README.txt

### Sync Folder to DaVinci Resolve

#### **Tự động tạo Bins từ Folder Structure**

1. Nhấp nút **"🎬 Sync to Resolve"** trên sidebar
2. Chọn folder chứa dự án
3. Nhấp **"Start Sync"**
4. Ứng dụng sẽ:
   - Kết nối tới DaVinci Resolve
   - Quét cấu trúc thư mục
   - Tạo Bins y hệt trong Resolve
   - Import media files vào bin tương ứng

**Yêu cầu:** DaVinci Resolve phải đang chạy

### Quick Import to Timeline

#### **Gửi Media từ QEditToolkit vào Timeline**

**Phương pháp 1: Double-Click**

- Tìm file audio/video muốn import
- Double-click vào file
- File tự động thêm vào timeline hiện tại

**Phương pháp 2: Right-Click Menu**

- Right-click vào file
- Chọn **"🎬 Send to Timeline"**
- File được import vào vị trí con trỏ

**Hỗ trợ các định dạng:**

- Video: MP4, MOV, AVI, MXF, M2TS
- Audio: WAV, MP3, AAC, FLAC
- Hình ảnh: PNG, JPG, TIFF, DPX

---

## 📂 Cấu Trúc Dự Án

### Project Vlog

```
20240117_VLOG_DaLatTrip/
├── 00_ProjectFiles/       # File project (Premiere, Final Cut Pro)
├── 01_Footage/
│   ├── Cam_A/            # Footage từ camera A
│   └── Cam_B/            # Footage từ camera B
├── 02_Audio/
│   └── Music/            # Nhạc nền
├── 05_Exports/
│   └── Final/            # Video xuất cuối cùng
└── README.txt
```

### Project Shorts/Reels

```
20240117_REEL_BeautyTips/
├── 00_ProjectFiles/
├── 01_Raw_Footage/
├── 02_Audio/
│   └── SFX/              # Sound Effects
├── 04_Exports/
│   └── TikTok/           # Xuất cho TikTok
└── README.txt
```

### Project Wedding

```
20240117_WED_JohnJane/
├── 00_ProjectFiles/
├── 01_Footage/
│   ├── Ceremony/
│   └── Reception/
├── 02_Audio/
│   └── Vows/
├── 05_Exports/
│   └── Highlight/
└── README.txt
```

### Project Event

```
20240117_EVENT_TechConf2024/
├── 00_ProjectFiles/
├── 01_Footage/
│   └── MasterCam/
├── 05_Exports/
│   └── FullShow/
└── README.txt
```

---

## 🏗️ Kiến Trúc Ứng Dụng

```
QEditToolkit/
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── .gitignore             # Git ignore rules
├── README.md              # Documentation
│
├── src/
│   ├── core/
│   │   ├── file_manager.py       # Quản lý import file
│   │   ├── preview_generator.py  # Tạo preview thumbnail
│   │   ├── resolve_installer.py  # DaVinci Resolve templates
│   │   └── resolve_api.py        # Deep link Resolve API
│   │
│   ├── database/
│   │   └── db_manager.py         # SQLite database management
│   │
│   └── ui/
│       ├── main_window.py        # Main application window
│       ├── asset_grid.py         # Asset grid view
│       ├── preview_panel.py      # Preview panel
│       ├── project_generator.py  # Dynamic Project Generator
│       └── resolve_sync_dialog.py # Resolve Sync Dialog
│
├── storage/               # Thư mục lưu asset
│   └── SFXs/             # Thư mục SFX mặc định
│
├── cache/                # Cache preview
│   └── previews/
│
└── assets/              # Assets ứng dụng
    └── styles/
```

### Công Nghệ Sử Dụng

- **GUI Framework**: PyQt6
- **Database**: SQLite3
- **File Management**: Python os/shutil
- **Image Processing**: Pillow
- **Date/Time**: datetime

---

## 🔧 Troubleshooting

### Vấn đề: Ứng dụng không chạy

```bash
# Kiểm tra Python version
python --version  # Cần 3.9+

# Cài đặt lại dependencies
pip install -r requirements.txt --force-reinstall
```

### Vấn đề: Import asset thất bại

- Kiểm tra quyền ghi thư mục `storage/`
- Đảm bảo file không bị lock bởi chương trình khác
- Thử chạy ứng dụng với quyền admin

### Vấn đề: Database lỗi

```bash
# Xoá database cũ và tạo mới
rm storage/database.db
python main.py
```

### Vấn đề: Giao diện không hiển thị đúng

- Kiểm tra phiên bản PyQt6: `pip show PyQt6`
- Cập nhật: `pip install PyQt6 --upgrade`

---

## 🤝 Đóng Góp

Chúng tôi vui lòng nhận các đóng góp từ cộng đồng!

1. Fork repository
2. Tạo branch cho feature (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push đến branch (`git push origin feature/amazing-feature`)
5. Mở Pull Request

---

## 📝 Giấy Phép

Project này được cấp phép dưới [MIT License](LICENSE) - xem file LICENSE để chi tiết.

---

## 👨‍💻 Tác Giả

- **Quoc** - @QuocGP99

---

## 📧 Liên Hệ

- Issues: [GitHub Issues](https://github.com/QuocGP99/QEditToolkit/issues)
- Email: contact@example.com

---

## 🙏 Cảm Ơn

Cảm ơn tất cả những người đã hỗ trợ và đóng góp cho dự án này!

---

**Last Updated**: January 17, 2026  
**Version**: 2.0.0
