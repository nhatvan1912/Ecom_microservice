import os
import httpx
from typing import Optional
from fastapi import FastAPI, Request, Response, HTTPException, Form, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="API Gateway")

# Setup session middleware
app.add_middleware(SessionMiddleware, secret_key="ecom_secret_key_change_me")

# Templates and Static files
templates = Jinja2Templates(directory="templates")
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Service URLs from environment
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://customer-service:8000")
STAFF_SERVICE_URL = os.getenv("STAFF_SERVICE_URL", "http://staff-service:8000")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", "http://cart-service:8000")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")
SHIPPING_SERVICE_URL = os.getenv("SHIPPING_SERVICE_URL", "http://shipping-service:8000")
MANAGER_SERVICE_URL = os.getenv("MANAGER_SERVICE_URL", "http://manager-service:8000")
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog-service:8000")
COMMENT_RATE_SERVICE_URL = os.getenv("COMMENT_RATE_SERVICE_URL", "http://comment-rate-service:8000")
RECOMMENDER_SERVICE_URL = os.getenv("RECOMMENDER_SERVICE_URL", "http://recommender-ai-service:8000")
CHATBOT_SERVICE_URL = os.getenv("CHATBOT_SERVICE_URL", "http://chatbot-service:8000")

async def get_current_user(request: Request):
    user = request.session.get("user")
    return user

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user: Optional[dict] = Depends(get_current_user)):
    featured_products = []
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{PRODUCT_SERVICE_URL}/api/products/")
            if resp.status_code == 200:
                featured_products = resp.json()[:8] # Show first 8
    except Exception:
        pass
    
    return templates.TemplateResponse("home.html", {"request": request, "user": user, "featured_products": featured_products})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, msg: Optional[str] = None):
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(f"{AUTH_SERVICE_URL}/auth/login", json={"username": username, "password": password})
            if resp.status_code == 200:
                data = resp.json()
                request.session["user"] = data["user"]
                request.session["access_token"] = data["access_token"]
                
                role = data["user"].get("role")
                if role == "manager":
                    return RedirectResponse(url="/manager", status_code=303)
                elif role == "staff":
                    return RedirectResponse(url="/admin", status_code=303)
                return RedirectResponse(url="/", status_code=303)
            else:
                return templates.TemplateResponse("login.html", {"request": request, "msg": "Sai tài khoản hoặc mật khẩu"})
        except Exception as e:
            return templates.TemplateResponse("login.html", {"request": request, "msg": f"Lỗi hệ thống: {str(e)}"})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, msg: Optional[str] = None):
    return templates.TemplateResponse("register.html", {"request": request, "msg": msg})

@app.post("/register")
async def register(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...), 
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...)
):
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            # Register customer via customer service
            resp = await client.post(f"{CUSTOMER_SERVICE_URL}/api/customers/", json={
                "username": username,
                "password": password,
                "full_name": full_name,
                "email": email,
                "phone": phone
            })
            if resp.status_code == 201:
                return RedirectResponse(url="/login?msg=Đăng ký thành công, mời bạn đăng nhập", status_code=303)
            else:
                error_msg = resp.text
                return templates.TemplateResponse("register.html", {"request": request, "msg": f"Đăng ký thất bại: {error_msg}"})
        except Exception as e:
            return templates.TemplateResponse("register.html", {"request": request, "msg": f"Lỗi hệ thống: {str(e)}"})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/products", response_class=HTMLResponse)
async def products_page(request: Request, user: Optional[dict] = Depends(get_current_user)):
    products = []
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{PRODUCT_SERVICE_URL}/api/products/")
            if resp.status_code == 200:
                products = resp.json()
    except Exception:
        pass
    return templates.TemplateResponse("products.html", {"request": request, "user": user, "products": products})

@app.get("/products/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int, user: Optional[dict] = Depends(get_current_user)):
    product = None
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{PRODUCT_SERVICE_URL}/api/products/{product_id}/")
            if resp.status_code == 200:
                product = resp.json()
    except Exception:
        pass
    
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
        
    return templates.TemplateResponse("product_detail.html", {"request": request, "user": user, "product": product})

@app.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user: return RedirectResponse(url="/login")
    cart = {"items": []}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{CART_SERVICE_URL}/api/carts/me/", headers={"Authorization": f"Bearer {request.session.get('access_token')}"})
            if resp.status_code == 200:
                cart = resp.json()
    except Exception:
        pass
    return templates.TemplateResponse("cart.html", {"request": request, "user": user, "cart": cart})

@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user: return RedirectResponse(url="/login")
    return templates.TemplateResponse("chatbot.html", {"request": request, "user": user})

@app.post("/api/ai/chat")
async def ai_chat(request: Request, payload: dict):
    user = request.session.get("user")
    if not user: raise HTTPException(status_code=401)
    
    session_id = request.session.get("chat_session_id")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{CHATBOT_SERVICE_URL}/api/chatbot/chat", json={
            "customer_id": user["id"],
            "message": payload.get("message"),
            "session_id": session_id,
        })
        if resp.status_code == 200:
            data = resp.json()
            request.session["chat_session_id"] = data.get("session_id")
            return data
        return {"answer": "Lỗi kết nối chatbot service"}

# Admin routes
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user or user.role != "staff": return RedirectResponse(url="/login")
    return templates.TemplateResponse("admin.html", {"request": request, "user": user})

@app.get("/manager", response_class=HTMLResponse)
async def manager_dashboard(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user or user.role != "manager": return RedirectResponse(url="/login")
    return templates.TemplateResponse("manager.html", {"request": request, "user": user})

@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway"}
