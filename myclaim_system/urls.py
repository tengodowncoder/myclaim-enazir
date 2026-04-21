from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from claims import views 

urlpatterns = [
    # --- 1. ADMIN ASAL DJANGO ---
    path('admin/', admin.site.urls), 
    
    # --- 2. GOOGLE AUTH (PINTU MASUK UTAMA) ---
    path('accounts/', include('allauth.urls')), 

    # --- 3. LAMAN UTAMA & LOGOUT ---
    path('', views.home, name='home'),
    path('logout/', views.keluar_sistem, name='logout'),
    
    # --- 4. PROFIL & PILIHAN SEKTOR ---
    path('profile/', views.profile_view, name='profile'),
    path('pilih-sektor/', views.tetapkan_sektor, name='pilih_sektor'),

    # --- 5. DASHBOARD & TUNTUTAN (USER) ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tuntut/', views.tuntut, name='tuntut'),
    path('edit-tuntutan/<int:pk>/', views.edit_tuntutan, name='edit_tuntutan'), 
    path('tuntutan/padam/<int:pk>/', views.padam_tuntutan, name='padam_tuntutan'), 
    path('cetak/<int:pk>/', views.jana_pdf, name='jana_pdf'),

    # --- 6. MODUL PENGURUSAN (ADMIN / KEWANGAN / KNS) ---
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('kns/dashboard/', views.kns_dashboard, name='kns_dashboard'), 
    path('kemaskini/<int:pk>/<str:tindakan>/', views.kemaskini_status, name='kemaskini_status'),
    
    # --- BARIS BARU YANG DITAMBAH UNTUK FUNGSI TOLAK ---
    path('tolak/<int:pk>/', views.tolak_tuntutan, name='tolak_tuntutan'),
    
    path('admin-dashboard/export/', views.export_tuntutan_csv, name='export_tuntutan_csv'),
    path('api/peserta/<int:program_id>/', views.senarai_peserta_json, name='api_peserta'),
    
    # URL UNTUK PADAM TUNTUTAN (GUNA DI DASHBOARD ADMIN UNTUK CUCI DATA UJIAN)
    path('admin-dashboard/padam/<int:pk>/', views.admin_padam_tuntutan, name='admin_padam_tuntutan'),

    # --- 7. PENGURUSAN PENGGUNA ---
    path('admin-dashboard/urus-pengguna/', views.urus_pengguna, name='urus_pengguna'),
    path('admin-dashboard/kemaskini-peranan/<int:user_id>/', views.kemaskini_peranan, name='kemaskini_peranan'),
    path('admin-dashboard/reset-password/<int:user_id>/', views.admin_reset_password, name='admin_reset_password'),
    path('admin-dashboard/padam-user/<int:user_id>/', views.padam_user, name='padam_user'),

    # --- 8. MODUL PTDM (PLANNING & EVENT) ---
    path('ptdm-dashboard/', views.ptdm_dashboard, name='ptdm_dashboard'),
    path('ptdm-dashboard/tambah/', views.ptdm_tambah_event, name='ptdm_tambah_event'),
    path('ptdm-dashboard/edit/<int:pk>/', views.ptdm_edit_event, name='ptdm_edit_event'),
    path('ptdm-dashboard/padam/<int:pk>/', views.ptdm_padam_event, name='ptdm_padam_event'),
]

# UNTUK PAPARAN GAMBAR (MEDIA)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)