from django.urls import path
from . import views

urlpatterns = [
    path('wallet',                              views.WalletView.as_view(),         name='wallet'),
    path('wallet/add',                          views.AddCurrencyView.as_view(),    name='wallet-add'),
    path('wallet/spend',                        views.SpendCurrencyView.as_view(),  name='wallet-spend'),
    path('inventory',                           views.InventoryView.as_view(),      name='inventory'),
    path('inventory/<uuid:inventory_id>/consume', views.ConsumeItemView.as_view(), name='inventory-consume'),
    path('catalog',                             views.CatalogView.as_view(),        name='catalog'),
    path('catalog/<str:item_id>/purchase',      views.PurchaseItemView.as_view(),   name='purchase'),
    path('transactions',                        views.TransactionListView.as_view(), name='transactions'),
    path('daily-reward',                        views.DailyRewardView.as_view(),    name='daily-reward'),
]
