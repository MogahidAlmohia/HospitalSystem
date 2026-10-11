from django.urls import path

from . import views


app_name = "inventory"


urlpatterns = [
    # Dashboard
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    # Categories
    path(
        "categories/",
        views.category_list,
        name="category_list",
    ),
    path(
        "categories/add/",
        views.category_create,
        name="category_create",
    ),
    path(
        "categories/<int:pk>/edit/",
        views.category_edit,
        name="category_edit",
    ),

    # Units
    path(
        "units/",
        views.unit_list,
        name="unit_list",
    ),
    path(
        "units/add/",
        views.unit_create,
        name="unit_create",
    ),
    path(
        "units/<int:pk>/edit/",
        views.unit_edit,
        name="unit_edit",
    ),

    # Suppliers
    path(
        "suppliers/",
        views.supplier_list,
        name="supplier_list",
    ),
    path(
        "suppliers/add/",
        views.supplier_create,
        name="supplier_create",
    ),
    path(
        "suppliers/<int:pk>/edit/",
        views.supplier_edit,
        name="supplier_edit",
    ),

    # Items
    path(
        "items/",
        views.item_list,
        name="item_list",
    ),
    path(
        "items/add/",
        views.item_create,
        name="item_create",
    ),
    path(
        "items/<int:pk>/edit/",
        views.item_edit,
        name="item_edit",
    ),

    # Warehouses
    path(
        "warehouses/",
        views.warehouse_list,
        name="warehouse_list",
    ),
    path(
        "warehouses/add/",
        views.warehouse_create,
        name="warehouse_create",
    ),
    path(
        "warehouses/<int:pk>/edit/",
        views.warehouse_edit,
        name="warehouse_edit",
    ),

    # Storage locations
    path(
        "locations/",
        views.location_list,
        name="location_list",
    ),
    path(
        "locations/add/",
        views.location_create,
        name="location_create",
    ),
    path(
        "locations/<int:pk>/edit/",
        views.location_edit,
        name="location_edit",
    ),

    # Stock
    path(
        "stock/",
        views.stock_list,
        name="stock_list",
    ),

    # Stock movements
    path(
        "receive/",
        views.receive,
        name="receive",
    ),
    path(
        "issue/",
        views.issue,
        name="issue",
    ),
    path(
        "return/",
        views.return_stock_view,
        name="return",
    ),
    path(
        "adjustment/",
        views.adjustment,
        name="adjustment",
    ),

    # Transfers
    path(
        "transfers/",
        views.transfer_list,
        name="transfer_list",
    ),
    path(
        "transfers/add/",
        views.transfer_create,
        name="transfer_create",
    ),
    path(
        "transfers/<int:pk>/approve/",
        views.transfer_approve,
        name="transfer_approve",
    ),
    path(
        "transfers/<int:pk>/complete/",
        views.transfer_complete,
        name="transfer_complete",
    ),

    # Audit / movement log
    path(
        "movements/",
        views.movement_list,
        name="movement_list",
    ),
]


# ============================================================
# PURCHASE WORKFLOW
# ============================================================

urlpatterns += [
    path(
        "purchases/",
        views.purchase_list,
        name="purchase_list",
    ),
    path(
        "purchases/create/",
        views.purchase_create,
        name="purchase_create",
    ),
    path(
        "purchases/<int:pk>/",
        views.purchase_detail,
        name="purchase_detail",
    ),
    path(
        "purchases/<int:purchase_id>/items/create/",
        views.purchase_item_create,
        name="purchase_item_create",
    ),
    path(
        "purchases/<int:pk>/order/",
        views.purchase_order,
        name="purchase_order",
    ),
]


# ============================================================
# PURCHASE RECEIVING
# ============================================================

urlpatterns += [
    path(
        "purchases/items/<int:purchase_item_id>/receive/",
        views.purchase_item_receive,
        name="purchase_item_receive",
    ),
]

# Inventory expiry reports
urlpatterns += [
    path("expired/", views.expired_list, name="expired_list"),
    path("expiring/", views.expiring_list, name="expiring_list"),
]
urlpatterns += [
    path("stock-value/", views.stock_value_report, name="stock_value_report"),
]
urlpatterns += [
    path("stock-summary/", views.stock_summary_report, name="stock_summary_report"),
]
