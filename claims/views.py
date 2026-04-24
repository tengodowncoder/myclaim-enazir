import csv
import json
from datetime import datetime
from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, FloatField
from django.db.models.functions import ExtractMonth, Coalesce
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.db.models import ProtectedError
from xhtml2pdf import pisa

from .forms import PendaftaranForm
from .models import Tuntutan, Program, CustomUser 

# ==========================================
# BAHAGIAN 1: PENGURUSAN ASAS & PROFIL
# ==========================================

# 1. Laman Utama
def home(request):
    return render(request, 'home.html')

# 2. Log Keluar Sistem
def keluar_sistem(request):
    logout(request)
    return redirect('home')

# 3. Dashboard Peribadi (Pegawai)
@login_required
def dashboard(request):
    # --- 1. HALA TUJU MENGIKUT PERANAN ---
    # Logik redirect KNS dkt sini tadi DAH DIBUANG supaya KNS boleh nampak Dashboard Utama
    
    # --- 2. LOGIK ASAL UNTUK PEGAWAI BIASA ---
    if not request.user.sektor:
        return redirect('pilih_sektor')
    
    # Sekarang, sesiapa pun (termasuk KNS) akan nampak tuntutan peribadi mereka dkt sini
    tuntutan_saya = Tuntutan.objects.filter(user=request.user).order_by('-tarikh_mohon')
    total_lulus = tuntutan_saya.filter(status='lulus').aggregate(Sum('jumlah_diluluskan'))['jumlah_diluluskan__sum'] or 0
    count_proses = tuntutan_saya.filter(status='proses').count()
    count_reject = tuntutan_saya.filter(status='reject').count()
    
    return render(request, 'dashboard.html', {
        'total_lulus': total_lulus,
        'count_proses': count_proses,
        'count_reject': count_reject,
        'tuntutan_saya': tuntutan_saya 
    })
# 4. Tetapkan Sektor/Unit (Pendaftaran Pertama)
@login_required
def tetapkan_sektor(request):
    if request.user.sektor:
        return redirect('dashboard')
    if request.method == 'POST':
        sektor_dipilih = request.POST.get('sektor')
        if sektor_dipilih:
            user = request.user
            user.sektor = sektor_dipilih
            user.save()
            messages.success(request, f"Profil dikemaskini. Sektor/Unit: {sektor_dipilih}")
            return redirect('dashboard')
    konteks = {'senarai_sektor': Program.SEKTOR_CHOICES}
    return render(request, 'pilih_sektor.html', konteks)

# 5. Kemaskini Profil User
@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        user.sektor = request.POST.get('sektor')
        user.gred = request.POST.get('gred')
        if request.FILES.get('gambar'):
            user.gambar = request.FILES.get('gambar')
        user.save()
        messages.success(request, 'Profil berjaya dikemas kini!')
        return redirect('profile')
    return render(request, 'profile.html')

# ==========================================
# BAHAGIAN 2: PENGURUSAN TUNTUTAN (PEGAWAI)
# ==========================================

# 6. Borang Permohonan Tuntutan Baru
@login_required
def tuntut(request):
    if request.method == 'POST':
        program_id = request.POST.get('program')
        program_obj = get_object_or_404(Program, id=program_id) if program_id else None
        
        status_semak = str(program_obj.status_pelaksanaan).lower() if program_obj else ""
        if status_semak in ['selesai', 'batal']:
            messages.error(request, f"RALAT: Program ini berstatus {status_semak.upper()}. Tuntutan tidak dibenarkan.")
            return redirect('tuntut')

        Tuntutan.objects.create(
            user=request.user,
            program=program_obj,
            sektor_manual=program_obj.sektor if program_obj else "",
            jenis_pemohon=request.POST.get('jenis_pemohon'),
            nama_manual=request.POST.get('nama_manual', ''),
            ic_manual=request.POST.get('ic_manual', ''),
            keterangan=request.POST.get('keterangan', ''),
            jumlah_tuntut=request.POST.get('jumlah_tuntut') or 0,
            status='proses'
        )
        messages.success(request, "Tuntutan berjaya dihantar!")
        return redirect('dashboard')

    senarai_program = Program.objects.all().exclude(
        Q(nama_event__icontains="Tuntutan Manual") | 
        Q(status_pelaksanaan__iexact="selesai") | 
        Q(status_pelaksanaan__iexact="batal")
    ).order_by('-id')
    
    return render(request, 'tuntut.html', {'senarai_program': senarai_program})

# 7. Kemaskini (Edit) Tuntutan Sedia Ada
@login_required
def edit_tuntutan(request, pk):
    tuntutan = get_object_or_404(Tuntutan, pk=pk, user=request.user)
    if request.method == 'POST':
        tuntutan.jumlah_tuntut = request.POST.get('jumlah_tuntut') or 0
        tuntutan.keterangan = request.POST.get('keterangan', '')
        program_id = request.POST.get('program')
        if program_id:
            tuntutan.program = get_object_or_404(Program, id=program_id)
        tuntutan.status = 'proses'
        tuntutan.save()
        messages.success(request, "Tuntutan berjaya dikemaskini!")
        return redirect('dashboard')

    senarai_program = Program.objects.all().exclude(
        Q(nama_event__icontains="Tuntutan Manual") | 
        Q(status_pelaksanaan__iexact="selesai") | 
        Q(status_pelaksanaan__iexact="batal")
    ).order_by('-id')

    if tuntutan.program:
        program_asal = Program.objects.filter(id=tuntutan.program.id)
        senarai_program = (program_asal | senarai_program).distinct()

    return render(request, 'tuntut.html', {'edit_mode': True, 't': tuntutan, 'senarai_program': senarai_program})

# 8. Padam Tuntutan (Oleh Pegawai)
@login_required
def padam_tuntutan(request, pk):
    tuntutan = get_object_or_404(Tuntutan, pk=pk, user=request.user)
    if tuntutan.status != 'lulus':
        tuntutan.delete()
        messages.success(request, "Rekod tuntutan telah dipadam.")
    else:
        messages.error(request, "Tuntutan yang telah lulus tidak boleh dipadam.")
    return redirect('dashboard')

# --- FUNGSI BARU DITAMBAH DI BAWAH ---

def tolak_tuntutan(request, pk):
    if request.method == 'POST':
        from .models import Tuntutan
        tuntutan = Tuntutan.objects.get(pk=pk)
        ulasan = request.POST.get('ulasan') # Ambil dari modal
        
        tuntutan.status = 'reject'
        tuntutan.ulasan_admin = ulasan # Pastikan field ni ada dlm model
        tuntutan.save()
        
        messages.warning(request, f"Tuntutan {tuntutan.nama_manual} telah ditolak.")
        return redirect('admin_dashboard')
    return redirect('admin_dashboard')


# ==========================================
# BAHAGIAN 3: PENGURUSAN ADMIN (MOD HYBRID)
# ==========================================

# 9. Dashboard Admin (Kewangan / KNS / PTDM)
@login_required
def admin_dashboard(request):
    # KUNCI: Import F dan DecimalField untuk pengiraan matematik database
    from django.db.models import Sum, Count, Q, FloatField, F, DecimalField
    from django.db.models.functions import Coalesce, ExtractMonth
    from django.contrib import messages

    # --- 1. SEMAKAN AKSES ---
    peranan_dibenarkan = ['kewangan', 'ptdm', 'kns']
    if request.user.peranan not in peranan_dibenarkan and not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Akses disekat.")
        return redirect('dashboard')

    is_kns = (request.user.peranan == 'kns')

    # --- 2. DATA TUNTUTAN ---
    semua_tuntutan = Tuntutan.objects.filter(status='proses').order_by('-tarikh_mohon')
    rekod_selesai = Tuntutan.objects.filter(status__in=['lulus', 'reject']).order_by('-tarikh_mohon')
    bilangan_baru = semua_tuntutan.count()
    total_rm_selesai = Tuntutan.objects.filter(status='lulus').aggregate(total=Sum('jumlah_diluluskan'))['total'] or 0

    # --- 3. DATA IKUT PROGRAM (FORMULA DAMAI: PTDM + KEWANGAN) ---
    ikut_program = Program.objects.annotate(
        bil_tuntut=Count('tuntutan', distinct=True),
        
        # Tuntutan Live: Ambil semua jumlah_tuntut (Align dengan PTDM)
        tuntutan_live=Coalesce(
            Sum('tuntutan__jumlah_tuntut'), 
            0.0, 
            output_field=FloatField()
        ),
        
        # Tuntutan Sah: Hanya yang dah lulus (Align dengan Kewangan)
        tuntutan_sah=Coalesce(
            Sum('tuntutan__jumlah_diluluskan', filter=Q(tuntutan__status='lulus')), 
            0.0, 
            output_field=FloatField()
        ),
        
        # Komitmen: Dari field os21000_b1
        komitmen_val=Coalesce(F('os21000_b1'), 0.0, output_field=FloatField()),
        
        # BAKI BARU: Anggaran (A1) - [Komitmen (B1) + Sah (Lulus)]
        baki_val=Coalesce(
            F('os21000_a1') - (
                F('os21000_b1') + 
                Coalesce(Sum('tuntutan__jumlah_diluluskan', filter=Q(tuntutan__status='lulus')), 0.0, output_field=FloatField())
            ), 0.0, output_field=FloatField()
        )
    ).order_by('-tuntutan_live')

    # --- 4. DATA CARTA ---
    chart_labels = [s[0] for s in Program.SEKTOR_CHOICES]
    chart_data = [float(Tuntutan.objects.filter(program__sektor=s, status='lulus').aggregate(total=Sum('jumlah_diluluskan'))['total'] or 0) for s in chart_labels]
    
    # Trend Bulanan
    trend_list = [0] * 12
    bulanan_qs = Tuntutan.objects.filter(status='lulus').annotate(month=ExtractMonth('tarikh_mohon')).values('month').annotate(total=Sum('jumlah_diluluskan'))
    for item in bulanan_qs:
        if item['month']:
            trend_list[item['month']-1] = float(item['total'] or 0)

    context = {
        'semua_tuntutan': semua_tuntutan,
        'rekod_selesai': rekod_selesai,
        'bilangan': bilangan_baru,
        'total_rm': float(total_rm_selesai),
        'ikut_program': ikut_program,
        'is_kns': is_kns,
        'chart_labels_sektor': chart_labels,
        'chart_data_sektor': chart_data,
        'chart_data_bulanan': trend_list,
        'sektor_choices': Program.SEKTOR_CHOICES,
    }
    return render(request, 'admin_dashboard.html', context)

# 9b. Dashboard KNS (Portal Pemerhatian)
@login_required
def kns_dashboard(request):
    from django.db.models import Sum, Count, Q, FloatField, F
    from django.db.models.functions import Coalesce

    # Semakan akses KNS sahaja
    if request.user.peranan != 'kns' and not request.user.is_superuser:
        messages.error(request, "Akses Portal Pemerhatian disekat.")
        return redirect('dashboard')

    # --- 1. DATA IKUT SEKTOR (RINGKASAN SUM UP) ---
    ringkasan_sektor = []
    # Ambil senarai sektor unik dari pilihan yang ada dlm model Program
    senarai_sektor = [s[0] for s in Program.SEKTOR_CHOICES]

    for sektor_nama in senarai_sektor:
        # Tapis semua program di bawah sektor ini
        program_sektor = Program.objects.filter(sektor=sektor_nama)
        
        if program_sektor.exists():
            # Kira Bilangan Program & Jumlah Anggaran/Komitmen (Direct dari table Program)
            bil_program = program_sektor.count()
            
            data_program = program_sektor.aggregate(
                total_a=Coalesce(Sum('os21000_a1'), 0.0, output_field=FloatField()),
                total_b=Coalesce(Sum('os21000_b1'), 0.0, output_field=FloatField())
            )
            
            # Kira Tuntutan Sah (Hanya yang berstatus 'lulus') dari table Tuntutan
            total_sah = Tuntutan.objects.filter(
                program__sektor=sektor_nama, 
                status='lulus'
            ).aggregate(
                total=Coalesce(Sum('jumlah_diluluskan'), 0.0, output_field=FloatField())
            )['total']

            anggaran = data_program['total_a']
            komitmen = data_program['total_b']
            
            # Formula Baki: Anggaran - (Komitmen + Tuntutan Sah)
            baki = anggaran - (komitmen + total_sah)

            # Masukkan ke dalam list untuk dihantar ke HTML
            ringkasan_sektor.append({
                'sektor': sektor_nama,
                'bil_prog': bil_program,
                'total_anggaran': anggaran,
                'total_komitmen': komitmen,
                'total_sah': total_sah,
                'baki_sektor': baki
            })

    # --- 2. DATA IKUT PROGRAM (DETAIL UNTUK JADUAL BAWAH) ---
    ikut_program = Program.objects.annotate(
        bil_tuntut=Count('tuntutan', distinct=True),
        # Tuntutan Live (Apa yang PTDM nampak/input)
        tuntutan_live=Coalesce(Sum('tuntutan__jumlah_tuntut'), 0.0, output_field=FloatField()),
        # Tuntutan Sah (Apa yang Kewangan dah luluskan)
        tuntutan_sah=Coalesce(Sum('tuntutan__jumlah_diluluskan', filter=Q(tuntutan__status='lulus')), 0.0, output_field=FloatField()),
        # Komitmen (Nilai dari field B1)
        komitmen_val=Coalesce(F('os21000_b1'), 0.0, output_field=FloatField()),
        # Baki Program: A1 - (B1 + Lulus)
        baki_val=Coalesce(
            F('os21000_a1') - (
                F('os21000_b1') + 
                Coalesce(Sum('tuntutan__jumlah_diluluskan', filter=Q(tuntutan__status='lulus')), 0.0, output_field=FloatField())
            ), 0.0, output_field=FloatField()
        )
    ).order_by('-tuntutan_live')

    # Kira total RM keseluruhan yang dah lulus dlm sistem
    total_rm_selesai = Tuntutan.objects.filter(status='lulus').aggregate(total=Sum('jumlah_diluluskan'))['total'] or 0

    context = {
        'ringkasan_sektor': ringkasan_sektor,
        'ikut_program': ikut_program,
        'total_rm': float(total_rm_selesai),
    }
    return render(request, 'kns_dashboard.html', context)

# 10. API Senarai Peserta (Popup Modal)
@login_required
def senarai_peserta_json(request, program_id):
    peserta_qs = Tuntutan.objects.filter(program_id=program_id)
    peserta_list = []
    for p in peserta_qs:
        peserta_list.append({
            'nama_manual': str(p.nama_manual or "").strip().upper(),
            'ic_manual': str(p.ic_manual or "-"),
            'sektor_manual': str(p.sektor_manual or "-"),
            'jumlah_tuntut': float(p.jumlah_tuntut or 0),
            # TAMBAH LINE DI BAWAH NI:
            'jumlah_diluluskan': float(p.jumlah_diluluskan or 0),
        })
    return JsonResponse({'peserta': peserta_list}, safe=False)

# 11. Kemaskini Status (Lulus / Tolak)
@login_required
def kemaskini_status(request, pk, tindakan):
    tuntutan = get_object_or_404(Tuntutan, pk=pk)
    if tindakan == 'lulus':
        tuntutan.status = 'lulus'
        tuntutan.jumlah_diluluskan = request.POST.get('amaun_lulus')
    elif tindakan == 'tolak':
        tuntutan.status = 'reject'
    tuntutan.save()
    return redirect('admin_dashboard')

# 12. Padam Tuntutan (Oleh Admin)
@login_required
def admin_padam_tuntutan(request, pk):
    get_object_or_404(Tuntutan, pk=pk).delete()
    return redirect('admin_dashboard')

# ==========================================
# BAHAGIAN 4: PELAPORAN & EKSPORT
# ==========================================

# 13. Jana PDF Tuntutan
@login_required
def jana_pdf(request, pk):
    tuntutan = get_object_or_404(Tuntutan, pk=pk)
    template = get_template('cetak_tuntutan.html')
    
    # KEMASKINI DI SINI: Tambah 'user': request.user
    context = {
        't': tuntutan,
        'user': request.user  # Supaya template kenal siapa user yang tgh login
    }
    
    html = template.render(context)
    result = BytesIO()
    pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    return HttpResponse(result.getvalue(), content_type='application/pdf')

# 14. Eksport Data Ke Excel (CSV)
@login_required
def export_tuntutan_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Laporan_Tuntutan.csv"'
    writer = csv.writer(response)
    writer.writerow(['Tarikh', 'Nama', 'No. KP', 'Sektor', 'Program', 'Amaun (RM)', 'Status'])
    for t in Tuntutan.objects.all().order_by('-tarikh_mohon'):
        writer.writerow([
            t.tarikh_mohon.strftime('%d/%m/%Y'), 
            t.nama_manual, 
            t.ic_manual, 
            t.sektor_manual, 
            t.program.nama_event if t.program else "-",
            t.jumlah_tuntut, 
            t.status
        ])
    return response

# ==========================================
# BAHAGIAN 5: PENGURUSAN PTDM (PLANNING)
# ==========================================

# 15. Dashboard PTDM
@login_required
def ptdm_dashboard(request):
    from django.db.models import Sum, Q, FloatField
    from django.db.models.functions import Coalesce

    if request.user.peranan != 'ptdm' and not request.user.is_superuser:
        return redirect('dashboard')
    
    # Ambil data dari URL (GET parameters)
    status_filter = request.GET.get('status', '').strip() 
    search_query = request.GET.get('search', '').strip()
    sektor_filter = request.GET.get('sektor', '').strip()

    # 1. KEKALKAN: Base Query untuk statistik (Supaya nombor card tak jadi 0 bila filter)
    stats_base = Program.objects.all()

    # 2. KEKALKAN: Query utama dengan tuntutan_live (100% ASAL)
    semua_planning = Program.objects.annotate(
        tuntutan_live=Coalesce(Sum('tuntutan__jumlah_tuntut'), 0.0, output_field=FloatField())
    ).order_by('-id')
    
    # --- LOGIC FILTER TAMBAHAN DARI CARD (Hanya tapis table) ---
    if status_filter:
        semua_planning = semua_planning.filter(status_pelaksanaan__iexact=status_filter)

    # 3. KEKALKAN: LOGIC SEARCH & SEKTOR ASAL
    if search_query:
        semua_planning = semua_planning.filter(Q(nama_event__icontains=search_query) | Q(pegawai_bertanggungjawab__icontains=search_query))
    if sektor_filter:
        semua_planning = semua_planning.filter(sektor__iexact=sektor_filter)
    
    # 4. CONTEXT: Gunakan stats_base untuk Card supaya nombor sentiasa ada
    context = {
        'semua_planning': semua_planning,
        'total_planning': stats_base.count(),
        'total_selesai': stats_base.filter(status_pelaksanaan__icontains='selesai').count(),
        'total_pinda': stats_base.filter(status_pelaksanaan__icontains='pinda').count(),
        'total_batal': stats_base.filter(status_pelaksanaan__icontains='batal').count(),
        'total_bajet': stats_base.aggregate(Sum('os21000_a1'))['os21000_a1__sum'] or 0,
        'total_pegawai': stats_base.values('pegawai_bertanggungjawab').distinct().count(),
        'sektor_list': Program.SEKTOR_CHOICES,
    }
    return render(request, 'ptdm_dashboard.html', context)

# 16. PTDM Tambah Program Baru
@login_required
def ptdm_tambah_event(request):
    if request.method == 'POST':
        status_raw = request.POST.get('status', 'belum')
        Program.objects.create(
            nama_event=request.POST.get('nama_event'),
            jenis_tugas=request.POST.get('jenis_tugas'),
            sektor=request.POST.get('sektor'),
            unit=request.POST.get('unit'),
            peruntukan=request.POST.get('peruntukan'),
            kod_aktiviti=request.POST.get('kod_aktiviti'),
            bilangan_peserta=request.POST.get('bil_peserta') or 0,
            tarikh_mula=request.POST.get('tarikh_mula') or None,
            tarikh_tamat=request.POST.get('tarikh_tamat') or None,
            pegawai_bertanggungjawab=request.POST.get('nama_pegawai'),
            gred_pegawai=request.POST.get('gred_pegawai'),
            justifikasi=request.POST.get('justifikasi'),
            status_pelaksanaan=status_raw.lower() if status_raw else 'belum',
            os21000_a1=request.POST.get('a1') or 0,
            os24000_a2=request.POST.get('a2') or 0,
            os27000_a3=request.POST.get('a3') or 0,
            os29000_a4=request.POST.get('a4') or 0,
            os21000_b1=request.POST.get('b1') or 0,
            os24000_b2=request.POST.get('b2') or 0,
            os27000_b3=request.POST.get('b3') or 0,
            os29000_b4=request.POST.get('b4') or 0,
        )
        messages.success(request, "Program baru berjaya diterbitkan!")
        return redirect('ptdm_dashboard')
    return render(request, 'ptdm_form.html', {'edit_mode': False, 'sektor_list': Program.SEKTOR_CHOICES})

# 17. PTDM Edit Program
@login_required
def ptdm_edit_event(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        status_raw = request.POST.get('status', program.status_pelaksanaan)
        program.nama_event = request.POST.get('nama_event')
        program.sektor = request.POST.get('sektor')
        program.status_pelaksanaan = status_raw.lower() if status_raw else 'belum'
        program.os21000_a1 = request.POST.get('a1') or 0
        program.save()
        messages.success(request, "Rekod program telah dikemaskini!")
        return redirect('ptdm_dashboard')
    return render(request, 'ptdm_form.html', {'program': program, 'edit_mode': True, 'sektor_list': Program.SEKTOR_CHOICES})

# 18. PTDM Padam Program
@login_required
def ptdm_padam_event(request, pk):
    # Ambil object program atau keluar 404 kalau tak wujud
    program = get_object_or_404(Program, pk=pk)
    
    try:
        # Cuba padam
        program.delete()
        messages.success(request, "Program berjaya dipadam!")
    except ProtectedError:
        # Jika ada 'lock' (ProtectedError), tangkap error tu dan bagi amaran cantik
        messages.error(request, (
            "RALAT: Program ini tidak boleh dipadam! "
            "Sebab: Terdapat rekod tuntutan yang telah berdaftar di bawah program ini. "
            "Sila padam tuntutan-tuntutan berkaitan terlebih dahulu."
        ))
    
    # Redirect balik ke dashboard, tak perlu refresh manual atau tutup tab
    return redirect('ptdm_dashboard')

# ==========================================
# BAHAGIAN 6: PENGURUSAN SUPERUSER (IT)
# ==========================================

# 19. Urus Pengguna (Senarai Semua)
@login_required
def urus_pengguna(request):
    if not request.user.is_superuser: return redirect('dashboard')
    semua_user = CustomUser.objects.all().order_by('username')
    return render(request, 'urus_pengguna.html', {'semua_user': semua_user})

# 20. Kemaskini Peranan (Role) User
@login_required
def kemaskini_peranan(request, user_id):
    # 1. Bodyguard: Hanya Superuser boleh tukar role
    if not request.user.is_superuser:
        return redirect('admin_dashboard')

    # 2. Guna CustomUser (ikut model kau)
    from .models import CustomUser 
    target_user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        peranan_baru = request.POST.get('peranan')
        target_user.peranan = peranan_baru
        
        # 3. Agihan Kunci Pintu (is_staff & is_superuser)
        if peranan_baru == 'admin':
            target_user.is_superuser = True
            target_user.is_staff = True
        elif peranan_baru == 'kewangan' or peranan_baru == 'kns' or peranan_baru == 'ptdm':
            # Role pengurusan perlukan is_staff untuk akses dashboard
            target_user.is_superuser = False
            target_user.is_staff = True
        else: 
            # User biasa tiada akses dashboard admin
            target_user.is_superuser = False
            target_user.is_staff = False
            
        target_user.save()
        
    return redirect('urus_pengguna')

# 21. Padam Pengguna
@login_required
def padam_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if not user.is_superuser: user.delete()
    return redirect('urus_pengguna')

# 22. Admin Reset Password
@login_required
def admin_reset_password(request, user_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    messages.info(request, f"Fungsi reset password untuk User ID {user_id} sedia digunakan.")
    return redirect('urus_pengguna')