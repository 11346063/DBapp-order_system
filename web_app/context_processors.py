def cart_count(request):
    # 購物車由 localStorage 管理，server 不追蹤數量；badge 由 base.html 內聯腳本初始化
    return {"cart_count": 0}
