from django.urls import path

from . import views, views_cadets, views_days, views_stats

urlpatterns = [
    path("", views.home, name="home"),
    path("kirish/", views.LoginView.as_view(), name="login"),
    path("chiqish/", views.LogoutView.as_view(), name="logout"),
    path("parol/", views.PasswordChangeView.as_view(), name="password_change"),
    # Kursantlar bazasi (6-bosqich)
    path("kursantlar/", views_cadets.cadet_list, name="cadet_list"),
    path("kursantlar/qoshish/", views_cadets.cadet_create, name="cadet_create"),
    path("kursantlar/qisqa-ism/", views_cadets.short_name_preview, name="cadet_short_name"),
    path("kursantlar/import/", views_cadets.cadet_import, name="cadet_import"),
    path("kursantlar/import/shablon.xlsx", views_cadets.cadet_import_template, name="cadet_import_template"),
    path("kursantlar/<int:pk>/", views_cadets.cadet_detail, name="cadet_detail"),
    path("kursantlar/<int:pk>/tahrirlash/", views_cadets.cadet_edit, name="cadet_edit"),
    path("kursantlar/<int:pk>/faolsizlantirish/", views_cadets.cadet_deactivate, name="cadet_deactivate"),
    path("kursantlar/<int:pk>/faollashtirish/", views_cadets.cadet_activate, name="cadet_activate"),
    path("kursantlar/<int:pk>/ozod-qilish/", views_cadets.cadet_exempt, name="cadet_exempt"),
    path("kursantlar/<int:pk>/naryadga-qaytarish/", views_cadets.cadet_unexempt, name="cadet_unexempt"),
    path("mening-tarixim/", views_cadets.my_card, name="my_card"),
    # Haftalar, sutka, sababli holatlar (7-bosqich)
    path("haftalar/", views_days.week_list, name="week_list"),
    path("haftalar/ochish/", views_days.week_open, name="week_open"),
    path("haftalar/korinish/", views_days.week_preview, name="week_preview"),
    path("sutkalar/", views_days.approved_days, name="approved_days"),
    path("sutka/<str:date>/", views_days.day_detail, name="day_detail"),
    path("sutka/<str:date>/tuzish/", views_days.day_generate, name="day_generate"),
    path("sutka/<str:date>/almashtirish/<int:slot_id>/", views_days.day_replace, name="day_replace"),
    path("sutka/<str:date>/lavozim/<int:post_id>/", views_days.day_swap, name="day_swap"),
    path("sutka/<str:date>/tasdiqlash/", views_days.day_approve, name="day_approve"),
    path("sutka/<str:date>/bekor-qilish/", views_days.day_reopen, name="day_reopen"),
    path("sutka/<str:date>/jurnal/", views_days.day_log, name="day_log"),
    path("sutka/<str:date>/ochirish/", views_days.day_delete, name="day_delete"),
    path("sutka/<str:date>/pdf/", views_days.day_pdf, name="day_pdf"),
    path("sutka/<str:date>/chop-etish/", views_days.day_print, name="day_print"),
    path("hafta/<str:start>/pdf/", views_days.week_pdf, name="week_pdf"),
    path("sababli/", views_days.absence_list, name="absence_list"),
    path("sababli/<int:pk>/tugatish/", views_days.absence_end, name="absence_end"),
    path("sababli/<int:pk>/ochirish/", views_days.absence_delete, name="absence_delete"),
    # Statistika va adolat (9-bosqich)
    path("statistika/", views_stats.stats_page, name="stats"),
    path("statistika/excel/", views_stats.stats_excel, name="stats_excel"),
]
