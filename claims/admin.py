from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import CustomUser, Program, Tuntutan

# 1. Pendaftaran Pengguna (CustomUser)
@admin.register(CustomUser)
class CustomUserAdmin(ImportExportModelAdmin): # Ini dah betul
    list_display = ['username', 'email', 'no_ic', 'sektor', 'peranan', 'is_staff']
    search_fields = ['username', 'no_ic', 'email']
    list_filter = ['peranan', 'is_staff', 'is_superuser']

# 2. Pendaftaran Program
@admin.register(Program)
class ProgramAdmin(ImportExportModelAdmin): # Ini dah betul
    list_display = ('id', 'nama_event', 'sektor', 'unit', 'os21000_a1', 'status_pelaksanaan')
    list_filter = ('sektor', 'status_pelaksanaan')
    search_fields = ('nama_event', 'unit')

# 3. Pendaftaran Tuntutan (KINI DENGAN IMPORT-EXPORT)
@admin.register(Tuntutan)
class TuntutanAdmin(ImportExportModelAdmin): # <--- TUKAR DARI admin.ModelAdmin KE ImportExportModelAdmin
    list_display = [
        'tarikh_mohon', 
        'nama_manual', 
        'program', 
        'jumlah_tuntut', 
        'status',
        'papar_pecahan_ringkas'
    ]
    
    list_filter = ['status', 'jenis_pemohon', 'tarikh_mohon', 'program__sektor']
    search_fields = ['nama_manual', 'ic_manual', 'keterangan']
    ordering = ['-tarikh_mohon']
    
    fieldsets = (
        ('Maklumat Pemohon', {
            'fields': ('user', 'jenis_pemohon', 'nama_manual', 'ic_manual', 'sektor_manual')
        }),
        ('Butiran Program & Mapping', {
            'description': "Data ditarik secara auto daripada perancangan PTDM",
            'fields': ('program', 'kod_aktiviti_auto', 'keterangan')
        }),
        ('Pecahan Elaun (Kod Akaun)', {
            'description': "Sila semak amaun bagi setiap kod akaun 211XX",
            'fields': (
                ('e21101', 'e21102'), 
                ('e21103', 'e21104'),
                ('e21105', 'e21106'),
                ('e21199',),
                'jumlah_tuntut',
            )
        }),
        ('Kelulusan & Admin', {
            'fields': ('status', 'ulasan_admin')
        }),
    )

    def papar_pecahan_ringkas(self, obj):
        ada_nilai = []
        if obj.e21101 > 0: ada_nilai.append("21101")
        if obj.e21102 > 0: ada_nilai.append("21102")
        if obj.e21103 > 0: ada_nilai.append("21103")
        if obj.e21104 > 0: ada_nilai.append("21104")
        if obj.e21105 > 0: ada_nilai.append("21105")
        if obj.e21106 > 0: ada_nilai.append("21106")
        if obj.e21199 > 0: ada_nilai.append("21199")
        return ", ".join(ada_nilai) if ada_nilai else "Tiada Data"
    
    papar_pecahan_ringkas.short_description = "Kod Akaun Terlibat"