import csv
import decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from claims.models import Tuntutan, Program
from django.utils.dateparse import parse_datetime
from django.utils import timezone  # PENTING: Import ini untuk selesaikan ralat pertama
from django.db.models import Q

User = get_user_model()

class Command(BaseCommand):
    help = 'Migrasi data permohonan lama ke sistem baru'

    def handle(self, *args, **options):
        # Nama fail CSV awak
        file_path = 'data pengguna.csv' 
        
        count_success = 0
        count_skip = 0

        self.stdout.write(self.style.NOTICE(f"Memulakan migrasi dari: {file_path}"))

        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Bersihkan data nama & IC
                    nama_penuh = str(row.get('Nama Penuh / Nama Organisasi') or '').strip().upper()
                    ic_raw = str(row.get('Kad Pengenalan / No. Syarikat') or '').strip()
                    ic_no = ic_raw.replace('-', '').replace(' ', '')
                    
                    if not nama_penuh or not ic_no:
                        continue # Skip kalau baris kosong

                    nama_prog_lama = str(row.get('Nama Program') or '').strip()
                    
                    # 1. Cari User dlm SSO
                    user_obj = User.objects.filter(no_ic=ic_no).first()

                    # 2. Cari padanan dlm 270 Program
                    prog_obj = Program.objects.filter(nama_event__iexact=nama_prog_lama).first()
                    
                    if not prog_obj:
                        prog_obj, _ = Program.objects.get_or_create(
                            nama_event="DATA MIGRASI - PROGRAM TIADA DALAM LIST",
                            defaults={'sektor': row.get('Sektor/Pejabat', 'MIGRASI')}
                        )

                    # 3. CUCI DATA AMAUN (Selesaikan ralat ValidationError)
                    def clean_decimal(val):
                        if not val: return 0.0
                        # Buang simbol pelik like RM, pembuka kata, koma
                        cleaned = str(val).replace('RM', '').replace(',', '').replace('"', '').replace('“', '').replace('”', '').strip()
                        try:
                            return float(cleaned)
                        except:
                            return 0.0

                    amaun = clean_decimal(row.get('Jumlah Tuntutan (RM)'))

                    # 4. Check Duplicate Tuntutan
                    exists = Tuntutan.objects.filter(
                        ic_manual=ic_no, 
                        program=prog_obj, 
                        jumlah_tuntut=amaun
                    ).exists()

                    if exists:
                        count_skip += 1
                        continue

                    # 5. Simpan ke Database
                    try:
                        Tuntutan.objects.create(
                            user=user_obj,
                            program=prog_obj,
                            jenis_pemohon=str(row.get('Jenis Permohonan', 'individu')).lower(),
                            nama_manual=nama_penuh,
                            ic_manual=ic_no,
                            sektor_manual=row.get('Sektor/Pejabat', 'MIGRASI'),
                            e21101=clean_decimal(row.get('Elaun 21101')),
                            e21102=clean_decimal(row.get('Elaun 21102')),
                            e21103=clean_decimal(row.get('Elaun 21103')),
                            e21104=clean_decimal(row.get('Elaun 21104')),
                            e21105=clean_decimal(row.get('Elaun 21105')),
                            e21106=clean_decimal(row.get('Elaun 21106')),
                            e21199=clean_decimal(row.get('Elaun 21199')),
                            jumlah_tuntut=amaun,
                            jumlah_diluluskan=amaun,
                            status='lulus',
                            tarikh_mohon=timezone.now() # Gunakan tarikh sekarang untuk data migrasi
                        )
                        count_success += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Gagal simpan {nama_penuh}: {e}"))

            self.stdout.write(self.style.SUCCESS(f"Selesai! {count_success} berjaya, {count_skip} skip."))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Fail tidak dijumpai: {file_path}"))