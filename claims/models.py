from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum
from django.apps import apps

# 1. Model Pengguna (CustomUser)
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'Pegawai Biasa'),
        ('ptdm', 'PTDM (Data Management)'),
        ('peneraju', 'Peneraju Sektor'),
        ('kewangan', 'Unit Kewangan'),
        ('kns', 'Ketua Nazir Sekolah'),
    ]
    
    no_ic = models.CharField(max_length=12, unique=True, null=True, blank=True)
    peranan = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    sektor = models.CharField(max_length=100, null=True, blank=True) 
    gred = models.CharField(max_length=20, null=True, blank=True) 
    gambar = models.ImageField(upload_to='profile_pics/', default='default.png', null=True, blank=True)
    profile_picture_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.username

# 2. Model Program (VERSI PTDM LENGKAP)
class Program(models.Model):
    SEKTOR_CHOICES = [
        ('SP', 'SEKTOR PENGURUSAN'), ('SDP', 'SEKTOR DASAR DAN PERANCANGAN'),
        ('SSJK', 'SEKTOR STANDARD DAN JAMINAN KUALITI'), ('SDTM', 'SEKTOR DATA DAN TEKNOLOGI MAKLUMAT'),
        ('SPKN', 'SEKTOR PEMBANGUNAN KOMPETENSI NAZIR'), ('SPK', 'SEKTOR PENAZIRAN KURIKULUM'),
        ('SPIP', 'SEKTOR PENAZIRAN INSTITUSI PENDIDIKAN'), ('SPHEMK', 'SEKTOR PENAZIRAN HAL EHWAL MURID DAN KOKURIKULUM'),
        ('JN_PERLIS', 'JN NEGERI PERLIS'), ('JN_KEDAH', 'JN NEGERI KEDAH'), ('JN_PP', 'JN NEGERI PULAU PINANG'), 
        ('JN_PERAK', 'JN NEGERI PERAK'), ('JN_KELANTAN', 'JN NEGERI KELANTAN'), ('JN_TERENGGANU', 'JN NEGERI TERENGGANU'),
        ('JN_PAHANG', 'JN NEGERI PAHANG'), ('JN_SELANGOR', 'JN NEGERI SELANGOR'), ('JN_MELAKA', 'JN NEGERI MELAKA'), 
        ('JN_NS', 'JN NEGERI NEGERI SEMBILAN'), ('JN_JOHOR', 'JN NEGERI JOHOR'), ('JN_WPKL', 'JN WILAYAH PERSEKUTUAN KUALA LUMPUR'),
        ('JN_SABAH', 'JN NEGERI SABAH'), ('JN_SARAWAK', 'JN NEGERI SARAWAK'), ('JN_TAWAU', 'JN CAWANGAN TAWAU, SABAH'), 
        ('JN_KENINGAU', 'JN CAWANGAN KENINGAU, SABAH'), ('JN_SANDAKAN', 'JN CAWANGAN SANDAKAN, SABAH'), 
        ('JN_MIRI', 'JN CAWANGAN MIRI, SARAWAK'), ('JN_SIBU', 'JN CAWANGAN SIBU, SARAWAK'), ('JN_BINTULU', 'JN CAWANGAN BINTULU, SARAWAK'),
    ]
    
    STATUS_PELAKSANAAN = [
        ('belum', 'Belum Bermula'), ('berjalan', 'Sedang Berjalan'),
        ('selesai', 'Selesai'), ('pinda', 'Dipinda'), ('batal', 'Dibatalkan'),
    ]

    nama_event = models.CharField(max_length=255)
    jenis_tugas = models.CharField(max_length=100, default='', blank=True) 
    sektor = models.CharField(max_length=50, choices=SEKTOR_CHOICES)
    unit = models.CharField(max_length=100)
    peruntukan = models.CharField(max_length=255, default='', blank=True)
    kod_aktiviti = models.CharField(max_length=50, default='', blank=True)
    bilangan_peserta = models.IntegerField(default=0)
    tarikh_mula = models.DateField(null=True, blank=True)
    tarikh_tamat = models.DateField(null=True, blank=True)
    pegawai_bertanggungjawab = models.CharField(max_length=255, default='-')
    gred_pegawai = models.CharField(max_length=20, default='-')
    status_pelaksanaan = models.CharField(max_length=20, choices=STATUS_PELAKSANAAN, default='belum')
    justifikasi = models.TextField(blank=True, null=True)

    # Field Anggaran (A)
    os21000_a1 = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    os24000_a2 = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    os27000_a3 = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    os29000_a4 = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Field Komitmen Manual (B)
    os21000_b1 = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    os24000_b2 = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    os27000_b3 = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    os29000_b4 = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    @property
    def total_anggaran(self):
        return self.os21000_a1 + self.os24000_a2 + self.os27000_a3 + self.os29000_a4

    @property
    def total_komitmen(self):
        return self.os21000_b1 + self.os24000_b2 + self.os27000_b3 + self.os29000_b4

    # LOGIK BAKI AUTOMATIK (A - [B manual + Tuntutan Sah])
    @property
    def baki_os21(self):
        # Panggil model guna string untuk elak circular import error
        # TUKAR 'claims' kepada nama app anda jika berbeza
        Tuntutan = apps.get_model('claims', 'Tuntutan') 
        
        total_lulus = Tuntutan.objects.filter(program=self, status='lulus').aggregate(
            total=Sum('e21101') + Sum('e21102') + Sum('e21103') + Sum('e21104') + Sum('e21105') + Sum('e21106') + Sum('e21199')
        )['total'] or 0
        return self.os21000_a1 - (self.os21000_b1 + total_lulus)

    @property
    def baki_os24(self):
        return self.os24000_a2 - self.os24000_b2

    @property
    def baki_os27(self):
        return self.os27000_a3 - self.os27000_b3

    @property
    def baki_os29(self):
        return self.os29000_a4 - self.os29000_b4

    @property
    def total_baki(self):
        return self.baki_os21 + self.baki_os24 + self.baki_os27 + self.baki_os29

    def __str__(self):
        return f"{self.nama_event} ({self.sektor})"

# 3. Model Tuntutan
class Tuntutan(models.Model):
    JENIS_CHOICES = [('individu', 'Individu'), ('organisasi', 'Organisasi')]
    STATUS_CHOICES = [
        ('proses', 'Dalam Proses'), ('disokong', 'Disokong Peneraju'),
        ('lulus', 'Lulus'), ('reject', 'Ditolak'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE) 
    tarikh_mohon = models.DateTimeField(auto_now_add=True)  
    jenis_pemohon = models.CharField(max_length=20, choices=JENIS_CHOICES, default='individu')
    nama_manual = models.CharField(max_length=255)           
    ic_manual = models.CharField(max_length=50)               
    sektor_manual = models.CharField(max_length=100, blank=True) 
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True)
    kod_aktiviti_auto = models.CharField(max_length=20, blank=True)
    e21101 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    e21102 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    e21103 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    e21104 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    e21105 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    e21106 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    e21199 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    keterangan = models.TextField(blank=True) 
    jumlah_tuntut = models.DecimalField(max_digits=10, decimal_places=2) 
    
    jumlah_diluluskan = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proses')
    ulasan_admin = models.TextField(blank=True, null=True)

    @property
    def helper_full_name(self):
        return f"{self.nama_manual} ({self.ic_manual})"

    def __str__(self):
        return f"{self.nama_manual} - {self.tarikh_mohon.strftime('%d/%m/%Y')}"