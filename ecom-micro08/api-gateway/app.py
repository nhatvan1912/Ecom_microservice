import os
import httpx
from typing import Optional
from fastapi import FastAPI, Request, Response, HTTPException, Form, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import PlainTextResponse

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


async def _fetch_service(path: str):
    """Try configured PRODUCT_SERVICE_URL first, then common localhost fallbacks.
    This helps when running the API gateway locally (not in Docker) while
    product-service is running in Docker (host port 8003) or locally on 8000.
    """
    candidates = [f"{PRODUCT_SERVICE_URL}{path}", f"http://localhost:8003{path}", f"http://localhost:8000{path}"]
    last_exc = None
    async with httpx.AsyncClient(timeout=5) as client:
        for url in candidates:
            try:
                resp = await client.get(url)
                return resp
            except Exception as e:
                last_exc = e
    if last_exc:
        raise last_exc
    return None

async def get_current_user(request: Request):
    user = request.session.get("user")
    return user

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user: Optional[dict] = Depends(get_current_user)):
    featured_products = []
    try:
        # use the fetch helper which falls back to localhost when needed
        resp = await _fetch_service("/api/products/")
        if resp and resp.status_code == 200:
            all_products = resp.json()
            # Provide a few view-specific lists expected by templates
            featured_products = all_products[:8]
            recommended_books = all_products[:4]
            newest_books = all_products[:6]
    except Exception:
        recommended_books = []
        featured_products = []
        newest_books = []

    # Provide both 'featured_products' and 'featured_books' keys for template compatibility
    return templates.TemplateResponse(request, "home.html", {"user": user, "featured_products": featured_products, "featured_books": featured_products, "recommended_books": recommended_books, "newest_books": newest_books})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, msg: Optional[str] = None):
    return templates.TemplateResponse(request, "login.html", {"msg": msg})

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
                return templates.TemplateResponse(request, "login.html", {"msg": "Sai tài khoản hoặc mật khẩu"})
        except Exception as e:
            return templates.TemplateResponse(request, "login.html", {"msg": f"Lỗi hệ thống: {str(e)}"})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, msg: Optional[str] = None):
    return templates.TemplateResponse(request, "register.html", {"msg": msg})

@app.post("/register")
async def register(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...),
    password2: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...)
):
    if password != password2:
        return templates.TemplateResponse(request, "register.html", {"msg": "Mật khẩu xác nhận không khớp!"})
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            # Register customer via customer service
            resp = await client.post(f"{CUSTOMER_SERVICE_URL}/api/customers/", json={
                "username": username,
                "password": password,
                "name": name,
                "email": email,
                "phone_number": phone_number
            })
            if resp.status_code == 201:
                return RedirectResponse(url="/login?msg=Đăng ký thành công, mời bạn đăng nhập", status_code=303)
            else:
                error_msg = resp.text
                return templates.TemplateResponse(request, "register.html", {"msg": f"Đăng ký thất bại: {error_msg}"})
        except Exception as e:
            return templates.TemplateResponse(request, "register.html", {"msg": f"Lỗi hệ thống: {str(e)}"})


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/products", response_class=HTMLResponse)
async def products_page(request: Request, user: Optional[dict] = Depends(get_current_user)):
    products = []
    try:
        resp = await _fetch_service("/api/products/")
        if resp and resp.status_code == 200:
            products = resp.json()
    except Exception:
        pass
    # Provide safe defaults for template variables that may be missing
    categories = []
    search_query = dict(request.query_params or {})
    total_products = len(products or [])
    page = int(request.query_params.get('page', 1) if request.query_params.get('page', '1').isdigit() else 1)
    total_pages = 1
    has_prev = page > 1
    has_next = False
    page_url_base = "/products?"

    return templates.TemplateResponse(
        request,
        "products.html",
        {
            "user": user,
            "products": products,
            "categories": categories,
            "search_query": search_query,
            "total_products": total_products,
            "page": page,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "page_url_base": page_url_base,
        },
    )

@app.get("/products/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int, user: Optional[dict] = Depends(get_current_user)):
    product = None
    try:
        resp = await _fetch_service(f"/api/products/{product_id}/")
        if resp and resp.status_code == 200:
            product = resp.json()
    except Exception:
        pass
    
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
        
    return templates.TemplateResponse(request, "product_detail.html", {"user": user, "product": product})


@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")

    user_orders = []
    try:
        # try to fetch orders for this user from order service
        resp = await _fetch_service(f"/api/orders/?customer_id={user.get('id')}")
        if resp and resp.status_code == 200:
            user_orders = resp.json()
    except Exception:
        user_orders = []

    return templates.TemplateResponse(request, "account.html", {"user": user, "user_orders": user_orders})


@app.get("/account/addresses", response_class=HTMLResponse)
async def account_addresses(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")

    addresses = []
    try:
        # customer service may expose addresses; fall back to empty list
        # common endpoints tried: /api/customers/{id}/addresses/ or /api/addresses/?customer_id=
        resp = await _fetch_service(f"/api/customers/{user.get('id')}/addresses/")
        if resp and resp.status_code == 200:
            addresses = resp.json()
        else:
            resp2 = await _fetch_service(f"/api/addresses/?customer_id={user.get('id')}")
            if resp2 and resp2.status_code == 200:
                addresses = resp2.json()
    except Exception:
        addresses = []

    return templates.TemplateResponse(request, "account_addresses.html", {"user": user, "addresses": addresses})

@app.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user: return RedirectResponse(url="/login")
    cart = {"items": []}
    message = request.query_params.get('msg')
    user_id = user.get('id')
    # Try several endpoints: prefer cart lookup by customer id, then common localhost fallbacks,
    # finally try listing carts and pick the user's cart if present.
    candidates = [
        f"{CART_SERVICE_URL}/api/carts/{user_id}/",
        f"http://localhost:8002/api/carts/{user_id}/",
        f"http://localhost:8000/api/carts/{user_id}/",
        f"{CART_SERVICE_URL}/api/carts/",
        f"http://localhost:8002/api/carts/",
        f"http://localhost:8000/api/carts/",
    ]
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # If session has last_cart_id, try it first
            last_cart_id = request.session.get('last_cart_id')
            if last_cart_id:
                try:
                    resp = await client.get(f"{CART_SERVICE_URL}/api/carts/{last_cart_id}/", headers={"Authorization": f"Bearer {request.session.get('access_token')}"})
                    print(f"cart_page: GET /api/carts/{{last_cart_id}}/ -> {resp.status_code} {getattr(resp, 'text', '')}")
                    if resp.status_code == 200:
                        cart = resp.json()
                        if not cart.get('items'):
                            message = (message or '') + " (LỖI: Giỏ hàng rỗng từ backend, kiểm tra lại cart-service!)"
                        return templates.TemplateResponse(request, "cart.html", {"user": user, "cart": cart, "items": cart.get('items', []), "total": cart.get('total', 0), "msg": message})
                except Exception as e:
                    print(f"cart_page: exception {e}")
            for url in candidates:
                try:
                    resp = await client.get(url, headers={"Authorization": f"Bearer {request.session.get('access_token')}"})
                    print(f"cart_page: GET {url} -> {resp.status_code} {getattr(resp, 'text', '')}")
                except Exception as e:
                    print(f"cart_page: exception {e}")
                    continue
                if resp.status_code != 200:
                    continue
                data = resp.json()
                # If the endpoint returned a list, find cart by customer_id
                if isinstance(data, list):
                    found = None
                    for c in data:
                        if c.get('customer_id') == user_id:
                            found = c
                            break
                    cart = found or (data[0] if data else {"items": []})
                else:
                    cart = data
                if not cart.get('items'):
                    message = (message or '') + " (LỖI: Giỏ hàng rỗng từ backend, kiểm tra lại cart-service!)"
                break
    except Exception as e:
        print(f"cart_page: exception {e}")
    items = cart.get("items") if isinstance(cart, dict) else []
    total = cart.get("total", 0) if isinstance(cart, dict) else 0
    return templates.TemplateResponse(request, "cart.html", {"user": user, "cart": cart, "items": items, "total": total, "msg": message})


@app.post("/products/{product_id}/add-to-cart")
async def add_to_cart(request: Request, product_id: int, user: Optional[dict] = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")

    access_token = request.session.get("access_token")
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    form = await request.form()
    try:
        qty = int(form.get('quantity', 1))
    except Exception:
        qty = 1

    payload = {"product_id": product_id, "quantity": qty}
    bases = [CART_SERVICE_URL, "http://localhost:8002", "http://localhost:8000"]
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            for base in bases:
                # 1) Try posting to customer's cart endpoint using base
                try:
                    url1 = f"{base}/api/carts/{user.get('id')}/"
                    print(f"add_to_cart: TRY POST {url1}")
                    resp = await client.post(url1, json=payload, headers=headers)
                    print(f"add_to_cart: POST {url1} -> {resp.status_code} {getattr(resp, 'text', '')}")
                    if resp.status_code in (200, 201):
                        # Try to fetch cart id for this user and store in session
                        try:
                            get_cart = await client.get(f"{base}/api/carts/{user.get('id')}/")
                            if get_cart.status_code == 200:
                                cart_data = get_cart.json()
                                cart_id = cart_data.get('id') if isinstance(cart_data, dict) else None
                                if cart_id:
                                    request.session['last_cart_id'] = cart_id
                        except Exception:
                            pass
                        return RedirectResponse(url="/cart?msg=added", status_code=303)
                except Exception as e:
                    print(f"add_to_cart: error POST {url1} -> {e}")

                # 2) Try creating a cart then adding item via base
                try:
                    url_create = f"{base}/api/carts/"
                    print(f"add_to_cart: TRY POST {url_create} (create)")
                    resp_create = await client.post(url_create, json={"customer_id": user.get('id')}, headers=headers)
                    print(f"add_to_cart: POST {url_create} -> {getattr(resp_create, 'status_code', 'ERR')} {getattr(resp_create, 'text', '')}")
                    if getattr(resp_create, 'status_code', None) == 201:
                        created = resp_create.json()
                        cart_id = created.get('id') or created.get('pk')
                        if cart_id:
                            url_add = f"{base}/api/carts/{cart_id}/"
                            print(f"add_to_cart: TRY POST {url_add} (add item)")
                            resp_add = await client.post(url_add, json=payload, headers=headers)
                            print(f"add_to_cart: POST {url_add} -> {resp_add.status_code} {getattr(resp_add, 'text', '')}")
                            if resp_add.status_code in (200, 201):
                                # we have cart_id from created above
                                try:
                                    request.session['last_cart_id'] = cart_id
                                except Exception:
                                    pass
                                return RedirectResponse(url="/cart?msg=added", status_code=303)
                except Exception as e:
                    print(f"add_to_cart: error create/add via {base} -> {e}")

                # 3) Try posting to /api/carts/me/ on base
                try:
                    url_me = f"{base}/api/carts/me/"
                    print(f"add_to_cart: TRY POST {url_me}")
                    resp_me = await client.post(url_me, json=payload, headers=headers)
                    print(f"add_to_cart: POST {url_me} -> {getattr(resp_me, 'status_code', 'ERR')} {getattr(resp_me, 'text', '')}")
                    if getattr(resp_me, 'status_code', None) in (200, 201):
                        try:
                            get_cart = await client.get(f"{base}/api/carts/{user.get('id')}/")
                            if get_cart.status_code == 200:
                                cart_data = get_cart.json()
                                cart_id = cart_data.get('id') if isinstance(cart_data, dict) else None
                                if cart_id:
                                    request.session['last_cart_id'] = cart_id
                        except Exception:
                            pass
                        return RedirectResponse(url="/cart?msg=added", status_code=303)
                except Exception as e:
                    print(f"add_to_cart: error POST {url_me} -> {e}")

            # If none succeeded, redirect to product page with error
            return RedirectResponse(url=f"/products/{product_id}?err=cart_failed", status_code=303)
    except Exception as e:
        print(f"add_to_cart: exception {e}")
        return RedirectResponse(url=f"/products/{product_id}?err=cart_exception", status_code=303)


@app.get("/products/{product_id}/add-to-cart")
async def add_to_cart_get(request: Request, product_id: int):
    # If a user navigates to this URL via GET, redirect back to product detail.
    return RedirectResponse(url=f"/products/{product_id}", status_code=303)


@app.get("/products/{product_id}/review")
async def review_get(request: Request, product_id: int):
    # Redirect review GET to the product detail page (form is on product detail)
    return RedirectResponse(url=f"/products/{product_id}", status_code=303)

@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_page(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user: return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "chatbot.html", {"user": user})

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
@app.get("/admin/reviews", response_class=HTMLResponse)
async def admin_reviews(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user or user.get("role") != "staff": return RedirectResponse(url="/login")
    reviews = []
    try:
        resp = await _fetch_service(f"/api/products/{0}/reviews/")
        # If we need all reviews, try to fetch from a different endpoint
        # For now, just fetch from product service
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{PRODUCT_SERVICE_URL}/api/products/")
            if resp and resp.status_code == 200:
                products = resp.json()
                all_reviews = []
                for product in products:
                    try:
                        resp2 = await client.get(f"{PRODUCT_SERVICE_URL}/api/products/{product['id']}/reviews/")
                        if resp2.status_code == 200:
                            reviews_data = resp2.json()
                            if isinstance(reviews_data, list):
                                for review in reviews_data:
                                    review['product_title'] = product.get('title', 'Unknown')
                                    all_reviews.append(review)
                    except:
                        pass
                reviews = all_reviews
    except Exception as e:
        print(f"admin_reviews error: {e}")
    return templates.TemplateResponse(request, "admin_reviews.html", {"user": user, "reviews": reviews})

@app.get("/admin/carts", response_class=HTMLResponse)
async def admin_carts(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user or user.get("role") != "staff": return RedirectResponse(url="/login")
    carts = []
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{CART_SERVICE_URL}/api/carts/")
            if resp.status_code == 200:
                carts = resp.json()
                if isinstance(carts, dict) and 'items' in carts:
                    carts = [carts]
    except Exception as e:
        print(f"admin_carts error: {e}")
    return templates.TemplateResponse(request, "admin_carts.html", {"user": user, "carts": carts})

@app.get("/admin/categories", response_class=HTMLResponse)
async def admin_categories(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user or user.get("role") != "staff": return RedirectResponse(url="/login")
    categories = []
    try:
        resp = await _fetch_service("/api/categories/")
        if resp and resp.status_code == 200:
            categories = resp.json()
    except Exception:
        pass
    return templates.TemplateResponse(request, "admin_categories.html", {"user": user, "categories": categories})

@app.get("/admin/orders", response_class=HTMLResponse)
async def admin_orders(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user or user.get("role") != "staff": return RedirectResponse(url="/login")
    orders = []
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{ORDER_SERVICE_URL}/api/orders/")
            if resp.status_code == 200:
                orders = resp.json()
    except Exception:
        pass
    return templates.TemplateResponse(request, "admin_orders.html", {"user": user, "orders": orders})

@app.get("/admin/customers", response_class=HTMLResponse)
async def admin_customers(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user or user.get("role") != "staff": return RedirectResponse(url="/login")
    customers = []
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{CUSTOMER_SERVICE_URL}/api/customers/")
            if resp.status_code == 200:
                customers = resp.json()
    except Exception:
        pass
    return templates.TemplateResponse(request, "admin_customers.html", {"user": user, "customers": customers})

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user or user.get("role") != "staff": return RedirectResponse(url="/login")
    
    # Fetch statistics
    stats = {"product_count": 0, "order_count": 0, "review_count": 0}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # Get product count
            try:
                resp = await client.get(f"{PRODUCT_SERVICE_URL}/api/products/")
                if resp.status_code == 200:
                    products = resp.json()
                    stats['product_count'] = len(products) if isinstance(products, list) else 1
            except:
                pass
            
            # Get order count
            try:
                resp = await client.get(f"{ORDER_SERVICE_URL}/api/orders/")
                if resp.status_code == 200:
                    orders = resp.json()
                    stats['order_count'] = len(orders) if isinstance(orders, list) else 1
            except:
                pass
            
            # Get review count
            try:
                resp = await client.get(f"{PRODUCT_SERVICE_URL}/api/products/")
                if resp.status_code == 200:
                    products = resp.json()
                    if isinstance(products, list):
                        review_count = 0
                        for product in products:
                            try:
                                resp2 = await client.get(f"{PRODUCT_SERVICE_URL}/api/products/{product.get('id', 0)}/reviews/")
                                if resp2.status_code == 200:
                                    reviews = resp2.json()
                                    review_count += len(reviews) if isinstance(reviews, list) else 0
                            except:
                                pass
                        stats['review_count'] = review_count
            except:
                pass
    except Exception as e:
        print(f"admin_dashboard error: {e}")
    
    return templates.TemplateResponse(request, "admin.html", {"user": user, "stats": stats})

@app.get("/manager", response_class=HTMLResponse)
async def manager_dashboard(request: Request, user: Optional[dict] = Depends(get_current_user)):
    if not user or user.get("role") != "manager": return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "manager.html", {"user": user})

@app.get("/health")
def health():
    return {"status": "ok", "service": "api-gateway"}


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    # Render a friendly HTML page for 404s instead of JSON
    if exc.status_code == 404:
        try:
            return templates.TemplateResponse("404.html", {"request": request, "user": request.session.get("user")})
        except Exception:
            return PlainTextResponse("Not Found", status_code=404)
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)
