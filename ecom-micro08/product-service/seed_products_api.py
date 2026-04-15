import json
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "http://localhost:8003/api"


def http_json(method: str, url: str, payload=None):
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url=url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
        if not body:
            return None
        return json.loads(body)


def get_json(url: str):
    try:
        return http_json("GET", url)
    except urllib.error.HTTPError as ex:
        if ex.code == 404:
            return None
        raise


def ensure_categories(category_defs):
    existing = get_json(f"{BASE_URL}/categories/") or []
    by_name = {str(item.get("name", "")).strip().lower(): item for item in existing}

    out = {}
    for cat in category_defs:
        key = cat["name"].strip().lower()
        if key in by_name:
            out[cat["name"]] = int(by_name[key]["id"])
            continue

        created = http_json("POST", f"{BASE_URL}/categories/", cat)
        out[cat["name"]] = int(created["id"])
    return out


def seed_products(products, category_map):
    all_products = get_json(f"{BASE_URL}/products/") or []
    existing_key = {
        str(item.get("title", "")).strip().lower()
        for item in all_products
    }

    created_count = 0
    skipped_count = 0

    for product in products:
        key = product["title"].strip().lower()
        if key in existing_key:
            skipped_count += 1
            continue

        payload = {
            "title": product["title"],
            "brand": product["brand"],
            "price": product["price"],
            "stock": product["stock"],
            "description": product["description"],
            "category_id": category_map[product["category"]],
            "image_url": product.get("image_url"),
        }
        http_json("POST", f"{BASE_URL}/products/", payload)
        existing_key.add(key)
        created_count += 1

    return created_count, skipped_count


def main():
    categories = [
        {"name": "Điện thoại & Phụ kiện", "description": "Smartphone, máy tính bảng, tai nghe, ốp lưng và các phụ kiện di động."},
        {"name": "Laptop & Máy tính", "description": "Laptop, PC, màn hình, bàn phím, chuột và thiết bị ngoại vi."},
        {"name": "Thời trang Nam", "description": "Áo, quần, giày dép và phụ kiện thời trang dành cho nam."},
        {"name": "Thời trang Nữ", "description": "Áo, váy, giày dép, túi xách và phụ kiện thời trang dành cho nữ."},
        {"name": "Đồ gia dụng", "description": "Thiết bị nhà bếp, nồi chiên, máy xay sinh tố, lò vi sóng."},
        {"name": "Sức khỏe & Làm đẹp", "description": "Mỹ phẩm, dưỡng da, chăm sóc tóc, thực phẩm chức năng."},
        {"name": "Thể thao & Outdoor", "description": "Giày thể thao, quần áo thể thao, dụng cụ tập gym, leo núi."},
        {"name": "Đồ chơi & Trẻ em", "description": "Đồ chơi giáo dục, búp bê, xe điều khiển, đồ dùng mẹ và bé."},
        {"name": "Thực phẩm & Đồ uống", "description": "Thực phẩm khô, đồ uống, đặc sản vùng miền, snack nhập khẩu."},
        {"name": "Nội thất & Trang trí", "description": "Bàn ghế, kệ TV, đèn trang trí, gối sofa và đồ decor nhà."},
    ]

    products = [
        # ===== Điện thoại & Phụ kiện =====
        {
            "title": "iPhone 15 Pro Max 256GB",
            "brand": "Apple",
            "category": "Điện thoại & Phụ kiện",
            "price": "28990000.00",
            "stock": 50,
            "description": "Chip A17 Pro mạnh mẽ, camera 48MP, khung titan cao cấp, màn hình Super Retina XDR 6.7 inch.",
        },
        {
            "title": "Samsung Galaxy S24 Ultra",
            "brand": "Samsung",
            "category": "Điện thoại & Phụ kiện",
            "price": "26490000.00",
            "stock": 40,
            "description": "Bút S Pen tích hợp, camera 200MP, Snapdragon 8 Gen 3, màn hình Dynamic AMOLED 2X 6.8 inch.",
        },
        {
            "title": "Xiaomi 14 Ultra",
            "brand": "Xiaomi",
            "category": "Điện thoại & Phụ kiện",
            "price": "19990000.00",
            "stock": 35,
            "description": "Camera Leica Summilux 50MP, chip Snapdragon 8 Gen 3, sạc nhanh 90W.",
        },
        {
            "title": "OPPO Find X7 Pro",
            "brand": "OPPO",
            "category": "Điện thoại & Phụ kiện",
            "price": "17990000.00",
            "stock": 30,
            "description": "Camera Hasselblad 50MP, chip Dimensity 9300, sạc nhanh SuperVOOC 100W.",
        },
        {
            "title": "Tai nghe AirPods Pro 2",
            "brand": "Apple",
            "category": "Điện thoại & Phụ kiện",
            "price": "5990000.00",
            "stock": 80,
            "description": "Chống ồn chủ động ANC thế hệ 2, âm thanh Adaptive Audio, chống nước IPX4.",
        },

        # ===== Laptop & Máy tính =====
        {
            "title": "MacBook Air M3 15 inch",
            "brand": "Apple",
            "category": "Laptop & Máy tính",
            "price": "32990000.00",
            "stock": 25,
            "description": "Chip Apple M3 8 nhân CPU, RAM 16GB, SSD 512GB, pin 18 giờ, màn hình Liquid Retina 15.3 inch.",
        },
        {
            "title": "Dell XPS 15 2024",
            "brand": "Dell",
            "category": "Laptop & Máy tính",
            "price": "39990000.00",
            "stock": 20,
            "description": "Intel Core Ultra 9, RAM 32GB DDR5, SSD 1TB, GPU NVIDIA RTX 4070, màn hình OLED 15.6 inch.",
        },
        {
            "title": "ASUS ROG Strix G16 2024",
            "brand": "ASUS",
            "category": "Laptop & Máy tính",
            "price": "42990000.00",
            "stock": 18,
            "description": "Intel Core i9-14900HX, RAM 32GB, RTX 4080, màn hình QHD 240Hz, tản nhiệt Tri-Fan Technology.",
        },
        {
            "title": "Lenovo ThinkPad X1 Carbon Gen 12",
            "brand": "Lenovo",
            "category": "Laptop & Máy tính",
            "price": "35990000.00",
            "stock": 22,
            "description": "Intel Core Ultra 7, RAM 16GB LPDDR5, SSD 512GB, siêu nhẹ 1.12kg, màn hình IPS 14 inch.",
        },
        {
            "title": "Màn hình LG 27GP950-B 4K 144Hz",
            "brand": "LG",
            "category": "Laptop & Máy tính",
            "price": "14990000.00",
            "stock": 40,
            "description": "Nano IPS 4K, 144Hz, HDR600, 1ms GTG, kết nối HDMI 2.1 và DisplayPort 1.4.",
        },

        # ===== Thời trang Nam =====
        {
            "title": "Áo Polo Nam Lacoste Classic Fit",
            "brand": "Lacoste",
            "category": "Thời trang Nam",
            "price": "1890000.00",
            "stock": 120,
            "description": "Chất liệu cotton piqué cao cấp, form slim fit, thoáng mát, nhiều màu sắc thời trang.",
        },
        {
            "title": "Quần Jean Nam Levi's 511 Slim",
            "brand": "Levi's",
            "category": "Thời trang Nam",
            "price": "1590000.00",
            "stock": 100,
            "description": "Denim stretch 4 chiều, form slim vừa vặn, nhiều màu wash khác nhau, bền đẹp theo thời gian.",
        },
        {
            "title": "Giày Sneaker Nike Air Force 1 '07",
            "brand": "Nike",
            "category": "Thời trang Nam",
            "price": "2490000.00",
            "stock": 90,
            "description": "Upper da thật, đế Air unit huyền thoại, thiết kế low-top cổ điển, dễ phối đồ.",
        },
        {
            "title": "Áo Sơ Mi Nam Calvin Klein Slim",
            "brand": "Calvin Klein",
            "category": "Thời trang Nam",
            "price": "1290000.00",
            "stock": 80,
            "description": "Chất liệu cotton không nhăn, form slim hiện đại, phù hợp đi làm lẫn dạo phố.",
        },
        {
            "title": "Túi Đeo Chéo Nam Coach Charter",
            "brand": "Coach",
            "category": "Thời trang Nam",
            "price": "3490000.00",
            "stock": 45,
            "description": "Da bò thật Cactus coated canvas, nhiều ngăn tiện lợi, khóa logo Coach sang trọng.",
        },

        # ===== Thời trang Nữ =====
        {
            "title": "Váy Midi Zara Floral Tiered",
            "brand": "Zara",
            "category": "Thời trang Nữ",
            "price": "790000.00",
            "stock": 150,
            "description": "Chất liệu viscose nhẹ nhàng, họa tiết hoa tươi, dáng xòe tầng duyên dáng, phù hợp mùa hè.",
        },
        {
            "title": "Giày Cao Gót Aldo Cruellan",
            "brand": "Aldo",
            "category": "Thời trang Nữ",
            "price": "1490000.00",
            "stock": 70,
            "description": "Mũi nhọn thanh lịch, gót nhọn 8cm, chất liệu da PU cao cấp, dễ phối với váy và quần tây.",
        },
        {
            "title": "Túi Xách Nữ Michael Kors Mercer",
            "brand": "Michael Kors",
            "category": "Thời trang Nữ",
            "price": "5490000.00",
            "stock": 35,
            "description": "Da bò thật Saffiano cao cấp, nhiều ngăn nhỏ tiện lợi, quai đeo vai và đeo chéo.",
        },
        {
            "title": "Áo Blazer Nữ Mango Fitted",
            "brand": "Mango",
            "category": "Thời trang Nữ",
            "price": "1190000.00",
            "stock": 60,
            "description": "Form fitted hiện đại, ve lai sắc sảo, chất liệu polyester pha viscose, nhiều màu trang nhã.",
        },
        {
            "title": "Nước Hoa Chanel N°5 EDP 50ml",
            "brand": "Chanel",
            "category": "Thời trang Nữ",
            "price": "3990000.00",
            "stock": 30,
            "description": "Hương hoa cổ điển huyền thoại, nốt aldehyde - ylang-ylang - hoa nhài - hổ phách, lưu hương 8-10 giờ.",
        },

        # ===== Đồ gia dụng =====
        {
            "title": "Nồi Chiên Không Dầu Philips HD9252",
            "brand": "Philips",
            "category": "Đồ gia dụng",
            "price": "2590000.00",
            "stock": 60,
            "description": "Rapid Air Technology, 5.6 lít, nhiệt độ 80-200°C, màn hình LED, giảm 90% lượng dầu.",
        },
        {
            "title": "Máy Xay Sinh Tố Vitamix E310",
            "brand": "Vitamix",
            "category": "Đồ gia dụng",
            "price": "9990000.00",
            "stock": 25,
            "description": "Motor 2HP, cối thủy tinh 1.4 lít, 10 tốc độ + chế độ Pulse, bảo hành 5 năm.",
        },
        {
            "title": "Nồi Cơm Điện Tử Zojirushi NP-HWH18",
            "brand": "Zojirushi",
            "category": "Đồ gia dụng",
            "price": "6490000.00",
            "stock": 40,
            "description": "Nấu áp suất, dung tích 1.8 lít, hẹn giờ 24h, giữ ấm tự động, lớp phủ chống dính Titanium.",
        },
        {
            "title": "Máy Lọc Không Khí Xiaomi Smart Air Purifier 4 Pro",
            "brand": "Xiaomi",
            "category": "Đồ gia dụng",
            "price": "3490000.00",
            "stock": 55,
            "description": "CADR 500 m³/h, lọc HEPA True 3 lớp, kết nối WiFi, điều khiển qua app Mi Home.",
        },
        {
            "title": "Máy Rửa Bát Bosch SMS4HKI01G",
            "brand": "Bosch",
            "category": "Đồ gia dụng",
            "price": "14990000.00",
            "stock": 15,
            "description": "13 bộ bát đĩa, lớp lót Inox, 6 chương trình rửa, EcoSilence Drive siêu êm, tiết kiệm nước.",
        },

        # ===== Sức khỏe & Làm đẹp =====
        {
            "title": "Kem Dưỡng Da The Ordinary Niacinamide 10%",
            "brand": "The Ordinary",
            "category": "Sức khỏe & Làm đẹp",
            "price": "290000.00",
            "stock": 200,
            "description": "Niacinamide 10% + Zinc 1%, thu nhỏ lỗ chân lông, kiểm soát dầu, mờ thâm mụn hiệu quả.",
        },
        {
            "title": "Serum Vitamin C La Roche-Posay Pure Vitamin C10",
            "brand": "La Roche-Posay",
            "category": "Sức khỏe & Làm đẹp",
            "price": "890000.00",
            "stock": 90,
            "description": "Vitamin C 10% + Salicylic Acid, làm sáng da và đều màu da, kết cấu nhẹ không nhờn.",
        },
        {
            "title": "Mascara Maybelline Sky High",
            "brand": "Maybelline",
            "category": "Sức khỏe & Làm đẹp",
            "price": "189000.00",
            "stock": 150,
            "description": "Lông mi siêu dài tối đa, kháng nước, không lem, công thức Infused Bamboo Extract.",
        },
        {
            "title": "Máy Sấy Tóc Dyson Supersonic HD08",
            "brand": "Dyson",
            "category": "Sức khỏe & Làm đẹp",
            "price": "12990000.00",
            "stock": 20,
            "description": "Motor kỹ thuật số V9, sấy nhanh Intelligent Heat Control, 3 tốc độ x 4 nhiệt độ, kết nối Bluetooth.",
        },
        {
            "title": "Thực Phẩm Chức Năng Collagen DHC",
            "brand": "DHC",
            "category": "Sức khỏe & Làm đẹp",
            "price": "490000.00",
            "stock": 100,
            "description": "Collagen thủy phân 3000mg/ngày, bổ sung vitamin B1, B2, B6, C, E, dạng viên tiện lợi.",
        },

        # ===== Thể thao & Outdoor =====
        {
            "title": "Giày Chạy Bộ Adidas Ultraboost 23",
            "brand": "Adidas",
            "category": "Thể thao & Outdoor",
            "price": "3990000.00",
            "stock": 70,
            "description": "Đế BOOST energy return, lớp Primeknit+ ôm chân, Continental rubber outsole chống trơn trượt.",
        },
        {
            "title": "Áo Thể Thao Nike Dri-FIT Training",
            "brand": "Nike",
            "category": "Thể thao & Outdoor",
            "price": "590000.00",
            "stock": 130,
            "description": "Công nghệ Dri-FIT thấm hút mồ hôi nhanh, chất liệu polyester nhẹ, thoáng khí cho mọi vận động.",
        },
        {
            "title": "Tạ Tay Vinyl 5kg PowerBlock",
            "brand": "PowerBlock",
            "category": "Thể thao & Outdoor",
            "price": "390000.00",
            "stock": 100,
            "description": "Vỏ nhựa vinyl bền đẹp, cán cầm PVC chống trơn, thiết kế ergonomic giảm mỏi tay.",
        },
        {
            "title": "Xe Đạp Địa Hình Giant Talon 3",
            "brand": "Giant",
            "category": "Thể thao & Outdoor",
            "price": "9490000.00",
            "stock": 12,
            "description": "Khung nhôm ALUXX-Grade, 21 tốc độ Shimano, phuộc SR Suntour, phanh đĩa cơ học.",
        },
        {
            "title": "Lều Cắm Trại Naturehike Cloud-Up 2",
            "brand": "Naturehike",
            "category": "Thể thao & Outdoor",
            "price": "2190000.00",
            "stock": 28,
            "description": "Cho 2 người, trọng lượng 1.79kg, chống nước 4000mm, chịu gió cấp 8, lắp dựng trong 5 phút.",
        },

        # ===== Đồ chơi & Trẻ em =====
        {
            "title": "LEGO Technic Bugatti Bolide 42151",
            "brand": "LEGO",
            "category": "Đồ chơi & Trẻ em",
            "price": "2190000.00",
            "stock": 35,
            "description": "905 chi tiết, mô hình xe đua Bugatti Bolide tỉ lệ 1:7, động cơ V16 chuyển động, dành cho 18+.",
        },
        {
            "title": "Xe Điều Khiển JJRC H98 Drone 4K",
            "brand": "JJRC",
            "category": "Đồ chơi & Trẻ em",
            "price": "1490000.00",
            "stock": 45,
            "description": "Camera 4K UHD, giữ độ cao tự động, nhào lộn 360°, pin 1800mAh bay 25 phút.",
        },
        {
            "title": "Búp Bê Barbie Signature Looks",
            "brand": "Barbie",
            "category": "Đồ chơi & Trẻ em",
            "price": "490000.00",
            "stock": 80,
            "description": "Búp bê tóc dài thắt bím, trang phục thời trang mix-and-match, phụ kiện đầy đủ.",
        },
        {
            "title": "Bộ Đồ Chơi Nhà Bếp Mini Kids",
            "brand": "Learning Resources",
            "category": "Đồ chơi & Trẻ em",
            "price": "890000.00",
            "stock": 55,
            "description": "35 chi tiết nhựa ABS an toàn, mô phỏng dụng cụ nấu ăn, phát triển trí tuệ và kỹ năng sáng tạo.",
        },
        {
            "title": "Máy Đọc Sách Kindle Paperwhite 5",
            "brand": "Amazon",
            "category": "Đồ chơi & Trẻ em",
            "price": "3990000.00",
            "stock": 40,
            "description": "Màn hình 6.8 inch không chói, 300ppi, chống nước IPX8, pin 10 tuần, bộ nhớ 8GB.",
        },

        # ===== Thực phẩm & Đồ uống =====
        {
            "title": "Cà Phê Rang Xay Trung Nguyên Legend",
            "brand": "Trung Nguyên",
            "category": "Thực phẩm & Đồ uống",
            "price": "290000.00",
            "stock": 200,
            "description": "Hỗn hợp Arabica - Robusta - Chari cao cấp, rang mộc đặc trưng, gói 500g.",
        },
        {
            "title": "Trà Ô Long Nhật Bản Ito En",
            "brand": "Ito En",
            "category": "Thực phẩm & Đồ uống",
            "price": "190000.00",
            "stock": 150,
            "description": "Trà Ô Long Nhật Bản chính gốc, chứa catechin chống oxy hóa, không đường, hộp 500ml x 6 chai.",
        },
        {
            "title": "Kẹo Socola Lindt Excellence 85% Cacao",
            "brand": "Lindt",
            "category": "Thực phẩm & Đồ uống",
            "price": "189000.00",
            "stock": 120,
            "description": "Socola đen 85% cacao từ Thụy Sĩ, vị đắng thanh tao, ít đường, giàu chất chống oxy hóa, 100g.",
        },
        {
            "title": "Mật Ong Rừng Nguyên Chất Đắk Lắk",
            "brand": "Mật Ong Rừng",
            "category": "Thực phẩm & Đồ uống",
            "price": "350000.00",
            "stock": 80,
            "description": "Mật ong rừng tự nhiên Tây Nguyên, chưa qua xử lý nhiệt, lọ thủy tinh 500g, chứng nhận OCOP.",
        },
        {
            "title": "Dầu Ô Liu Extra Virgin Bertolli",
            "brand": "Bertolli",
            "category": "Thực phẩm & Đồ uống",
            "price": "290000.00",
            "stock": 90,
            "description": "Extra virgin cold pressed từ Ý, acidity < 0.5%, giàu Omega-9, thích hợp salad và nấu ăn, chai 750ml.",
        },

        # ===== Nội thất & Trang trí =====
        {
            "title": "Ghế Sofa Góc L IKEA KIVIK",
            "brand": "IKEA",
            "category": "Nội thất & Trang trí",
            "price": "12990000.00",
            "stock": 8,
            "description": "Khung gỗ thông rừng, đệm foam mật độ cao, bọc vải Orrsta màu xám nhạt, 4-6 chỗ ngồi.",
        },
        {
            "title": "Đèn Gương LED Philips Hue",
            "brand": "Philips",
            "category": "Nội thất & Trang trí",
            "price": "1990000.00",
            "stock": 50,
            "description": "Điều chỉnh nhiệt màu 2700-6500K, kết nối Bluetooth + Zigbee, tương thích Alexa/Google Home.",
        },
        {
            "title": "Thảm Phòng Khách Ottoman Vintage 160x230cm",
            "brand": "Ottoman",
            "category": "Nội thất & Trang trí",
            "price": "2490000.00",
            "stock": 20,
            "description": "Sợi polypropylene chống mài mòn, họa tiết vintage Thổ Nhĩ Kỳ, dễ vệ sinh, không phai màu.",
        },
        {
            "title": "Bình Hoa Thủy Tinh Borosilicate Nordic",
            "brand": "HOLEX",
            "category": "Nội thất & Trang trí",
            "price": "490000.00",
            "stock": 75,
            "description": "Thủy tinh borosilicate trong suốt, thiết kế Nordic tối giản, set 3 kích thước phối nhau.",
        },
        {
            "title": "Kệ Sách Floating Wall 5 Tầng",
            "brand": "SONGMICS",
            "category": "Nội thất & Trang trí",
            "price": "890000.00",
            "stock": 40,
            "description": "Gỗ MDF phủ sơn trắng, lắp ráp dễ dàng, tải trọng 15kg/tầng, kích thước 80x25x180cm.",
        },
    ]

    category_map = ensure_categories(categories)
    created_count, skipped_count = seed_products(products, category_map)
    print(f"Seed completed. created={created_count}, skipped_existing={skipped_count}, total_input={len(products)}")


if __name__ == "__main__":
    main()
