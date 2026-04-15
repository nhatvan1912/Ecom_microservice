"""
Initialization script for Recommender AI Service
Fetches real products from product-service and populates the recommender database
"""

import json
import os
import urllib.request
import urllib.error
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Dict
import sys

# Import from app
sys.path.insert(0, os.path.dirname(__file__))

DB_URL = os.getenv(
    "DB_URL",
    "mysql+pymysql://root:123456@db:3306/recommender_db",
)
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")

# Initialize database connection
engine = create_engine(DB_URL, pool_pre_ping=True)


def ensure_database_exists(db_url: str):
    """Create database if it doesn't exist"""
    from sqlalchemy.engine import make_url
    
    url = make_url(db_url)
    db_name = url.database
    if not db_name:
        return

    server_engine = create_engine(url.set(database="mysql"), pool_pre_ping=True)
    with server_engine.begin() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    server_engine.dispose()


def ensure_recommender_schema():
    """Create required tables if they don't exist"""
    with engine.begin() as conn:
        # Create user preferences table
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS recommender_user_preferences (
                    customer_id INT PRIMARY KEY,
                    viewed_product_ids TEXT NOT NULL,
                    viewed_product_counts TEXT NULL,
                    purchased_product_counts TEXT NULL,
                    updated_at DATETIME NULL
                )
                """
            )
        )
        
        # Create recommendation events table
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS recommendation_events (
                    id VARCHAR(36) PRIMARY KEY,
                    customer_id INT NOT NULL,
                    viewed_product_ids TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_customer (customer_id),
                    INDEX idx_created (created_at)
                )
                """
            )
        )
        
        # Create knowledge vectors table
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS recommender_knowledge_vectors (
                    id VARCHAR(128) PRIMARY KEY,
                    entity_type VARCHAR(32) NOT NULL,
                    entity_id VARCHAR(64) NOT NULL,
                    vector_json LONGTEXT NOT NULL,
                    metadata_json LONGTEXT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_entity (entity_type, entity_id),
                    INDEX idx_updated (updated_at)
                )
                """
            )
        )


def fetch_products_from_service() -> List[Dict]:
    """Fetch all products from product-service"""
    print("🛒 Fetching products from product-service...")
    try:
        with urllib.request.urlopen(f"{PRODUCT_SERVICE_URL}/api/products/", timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            
            # Handle both paginated and direct list responses
            if isinstance(data, dict) and "results" in data:
                products = data.get("results", [])
            elif isinstance(data, list):
                products = data
            else:
                products = []
            
            print(f"✓ Fetched {len(products)} products from product-service")
            return products
    except (urllib.error.URLError, ValueError, json.JSONDecodeError, OSError) as e:
        print(f"✗ Error fetching products: {e}")
        print("⚠️  Using default product pool as fallback...")
        return get_default_products()


def get_default_products() -> List[Dict]:
    """Return default products if service is unavailable"""
    return [
        {
            "id": 1,
            "title": "iPhone 15 Pro Max",
            "brand": "Apple",
            "description": "Smartphone cao cấp với chip A17 Pro và camera 48MP",
            "category": "Điện thoại & Phụ kiện",
            "price": 28990000
        },
        {
            "id": 2,
            "title": "MacBook Air M3",
            "brand": "Apple",
            "description": "Laptop siêu mỏng chip M3 hiệu năng cao",
            "category": "Laptop & Máy tính",
            "price": 32990000
        },
        {
            "id": 3,
            "title": "Nike Air Force 1",
            "brand": "Nike",
            "description": "Giày sneaker huyền thoại đế Air unit",
            "category": "Thời trang Nam",
            "price": 2490000
        },
        {
            "id": 4,
            "title": "Nồi Chiên Không Dầu Philips",
            "brand": "Philips",
            "description": "Nấu ăn lành mạnh giảm 90% dầu mỡ",
            "category": "Đồ gia dụng",
            "price": 2590000
        },
        {
            "id": 5,
            "title": "Serum Vitamin C La Roche-Posay",
            "brand": "La Roche-Posay",
            "description": "Vitamin C 10% làm sáng da và đều màu da hiệu quả",
            "category": "Sức khỏe & Làm đẹp",
            "price": 890000
        },
        {
            "id": 6,
            "title": "Adidas Ultraboost 23",
            "brand": "Adidas",
            "description": "Giày chạy bộ đế BOOST đàn hồi năng lượng",
            "category": "Thể thao & Outdoor",
            "price": 3990000
        },
    ]


def create_knowledge_vectors(products: List[Dict]):
    """Create knowledge vectors for products in the database"""
    from app import (
        encode_text_embedding,
        upsert_knowledge_vector,
        _build_text_from_product
    )
    
    source = "unknown"
    print("\n🧠 Creating knowledge vectors for products...")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        for product in products:
            product_id = product.get("id") or product.get("product_id")
            if product_id is None:
                continue
            
            # Build text representation of the product
            product_text = _build_text_from_product(product)
            
            # Generate embedding vector
            vector, source = encode_text_embedding(product_text)
            
            # Store in knowledge base
            upsert_knowledge_vector(
                db=db,
                entity_type="product",
                entity_id=str(product_id),
                vector=vector,
                metadata={
                    "product_id": product_id,
                    "title": product.get("title", ""),
                    "brand": product.get("brand", ""),
                    "category": product.get("category", ""),
                    "price": float(product.get("price", 0)),
                },
            )
        
        db.commit()
        print(f"✓ Created knowledge vectors for {len(products)} products using {source} model")
        return source
    finally:
        db.close()


def create_sample_customer_preferences(products: List[Dict]):
    """Create sample customer preferences to demonstrate the system"""
    print("\n👥 Initializing sample customer preferences...")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        from app import UserPreferenceRow, _dump_count_map
        
        # Sample customer profiles to create realistic data
        sample_customers = [
            {
                "customer_id": 1,
                "name": "Tech Enthusiast",
                "viewed": [1, 5, 2],  # Python, ML, Clean Code
                "viewed_counts": {1: 3, 5: 2, 2: 1},
                "purchased": [1],  # Purchased Python
                "purchased_counts": {1: 1},
            },
            {
                "customer_id": 2,
                "name": "Business Reader",
                "viewed": [3, 6],  # Business, Productivity
                "viewed_counts": {3: 2, 6: 1},
                "purchased": [3],  # Purchased Business
                "purchased_counts": {3: 1},
            },
            {
                "customer_id": 3,
                "name": "Fiction Lover",
                "viewed": [4],  # Mystery
                "viewed_counts": {4: 2},
                "purchased": [4],  # Purchased Mystery
                "purchased_counts": {4: 1},
            },
            {
                "customer_id": 4,
                "name": "Mixed Reader",
                "viewed": [1, 3, 5, 6],  # Various
                "viewed_counts": {1: 2, 3: 1, 5: 3, 6: 1},
                "purchased": [1, 5],  # Tech products
                "purchased_counts": {1: 1, 5: 1},
            },
            {
                "customer_id": 5,
                "name": "Data Scientist",
                "viewed": [1, 5, 2],  # Python, ML, Code
                "viewed_counts": {1: 4, 5: 3, 2: 2},
                "purchased": [1, 5, 2],  # All tech products
                "purchased_counts": {1: 1, 5: 1, 2: 1},
            },
        ]
        
        for customer in sample_customers:
            # Check if customer preference already exists
            existing = db.query(UserPreferenceRow).filter(
                UserPreferenceRow.customer_id == customer["customer_id"]
            ).first()
            
            if not existing:
                new_pref = UserPreferenceRow(
                    customer_id=customer["customer_id"],
                    viewed_product_ids=json.dumps(customer["viewed"]),
                    viewed_product_counts=_dump_count_map(customer["viewed_counts"]),
                    purchased_product_counts=_dump_count_map(customer["purchased_counts"]),
                    updated_at=datetime.utcnow(),
                )
                db.add(new_pref)
                print(f"  ✓ Created preference for Customer {customer['customer_id']} ({customer['name']})")
        
        db.commit()
        print(f"✓ Initialized {len(sample_customers)} sample customer preferences")
    finally:
        db.close()


def print_stats():
    """Print statistics about the initialized recommender system"""
    print("\n📊 Recommender System Statistics:")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        from app import UserPreferenceRow, KnowledgeVectorRow, RecommendationEventRow
        
        user_count = db.query(UserPreferenceRow).count()
        product_vectors = db.query(KnowledgeVectorRow).filter(
            KnowledgeVectorRow.entity_type == "product"
        ).count()
        recommendation_events = db.query(RecommendationEventRow).count()
        
        print(f"  • Customer profiles: {user_count}")
        print(f"  • Product vectors: {product_vectors}")
        print(f"  • Recommendation events: {recommendation_events}")
        print("\n✅ Recommender AI system is ready!")
    finally:
        db.close()


def main():
    """Main initialization function"""
    print("\n" + "="*60)
    print("🚀 Initializing Recommender AI Service")
    print("="*60)
    
    try:
        # Ensure database exists
        ensure_database_exists(DB_URL)
        print("✓ Database created/verified")
        
        # Create schema
        ensure_recommender_schema()
        print("✓ Schema created/verified")
        
        # Fetch products
        products = fetch_products_from_service()
        
        # Create knowledge vectors
        create_knowledge_vectors(products)
        
        # Create sample customer preferences
        create_sample_customer_preferences(products)
        
        # Print statistics
        print_stats()
        
    except Exception as e:
        print(f"✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
