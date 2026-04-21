import os
import django
import csv
import uuid
from datetime import datetime

# 1. SETUP DJANGO ENVIRONMENT
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myclaim_system.settings')
django.setup()

from claims.models import CustomUser, Program, Tuntutan

def clean_float(value):
    """Menukar string (contoh: '1,200.50' atau '-') kepada float (1200.5 atau 0.0)"""
    if not value:
        return 0.0
    
    val_str = str(value).replace(',', '').strip()
    
    # Jika nilai adalah sengkang atau bukan nombor, pulangkan 0.0
    if val_str == "-" or val_str == "":
        return 0.0
        
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def convert_date(date_str):
    """Menukar format Timestamp ke YYYY-MM-DD"""
    if not date_str:
        return None
    try:
        clean_date = date_str.split()[0]
        return datetime.strptime(clean_date, '%d/%m/%Y').strftime('%Y-%m-%d')
    except Exception:
        return None

def run_migration():
    file_path = 'DATABASE MYCLAIM@JN - WebAppForm.csv'
    
    if not os.path.exists(file_path):
        print(f"RALAT: Fail {file_path} tidak dijumpai!")
        return

    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        count = 0
        
        print("Memulakan proses migrasi (Versi Anti-Crash + IC Priority)...")
        
        for row in reader:
            # --- 1. PENGURUSAN USER (VERSI BARU - CARI GUNA IC) ---
            ic_number = row['Kad Pengenalan / No. Syarikat'].strip()
            email = row['Email'].strip().lower()
            nama_program = row['Nama Program'].strip()
            
            # Cari user guna No. IC (Sebab IC mesti unik)
            user = CustomUser.objects.filter(no_ic=ic_number).first()
            
            # Jika IC tak jumpa, cari pula guna Emel (Double check)
            if not user:
                user = CustomUser.objects.filter(email=email).first()

            # Jika masih tak jumpa, baru buat user baru
            if not user:
                base_username = email.split('@')[0]
                username = base_username
                # Pastikan username tidak bertindih
                if CustomUser.objects.filter(username=username).exists():
                    username = f"{base_username}_{uuid.uuid4().hex[:4]}"
                
                user = CustomUser.objects.create(
                    email=email,
                    username=username,
                    first_name=row['Nama Penuh / Nama Organisasi'],
                    no_ic=ic_number,
                    sektor=row['Sektor/Pejabat'],
                    peranan='user'
                )

            # --- 2. PENGURUSAN PROGRAM ---
            program, created = Program.objects.get_or_create(
                nama_event=nama_program,
                defaults={
                    'sektor': row['Sektor/Pejabat'],
                    'unit': row['Peneraju Program'],
                    'os21000_a1': clean_float(row['Kod Aktiviti']), 
                    'status_pelaksanaan': 'selesai'
                }
            )

            # --- 3. SIMPAN TUNTUTAN ---
            Tuntutan.objects.create(
                user=user,
                program=program,
                jenis_pemohon=row['Jenis Permohonan'],
                nama_manual=row['Nama Penuh / Nama Organisasi'],
                ic_manual=ic_number,
                sektor_manual=row['Sektor/Pejabat'],
                kod_aktiviti_auto=row['Kod Aktiviti'],
                tarikh_mohon=convert_date(row['Timestamp']),
                
                # Pecahan Elaun
                e21101=clean_float(row['Elaun 21101']),
                e21102=clean_float(row['Elaun 21102']),
                e21103=clean_float(row['Elaun 21103']),
                e21104=clean_float(row['Elaun 21104']),
                e21105=clean_float(row['Elaun 21105']),
                e21106=clean_float(row['Elaun 21106']),
                e21199=clean_float(row['Elaun 21199']),
                
                jumlah_tuntut=clean_float(row['Jumlah Tuntutan (RM)']),
                status='lulus',
                keterangan="Migrasi data dari WebAppForm (Lama)"
            )
            
            count += 1
            if count % 50 == 0:
                print(f"✓ Berjaya proses {count} rekod...")

    print(f"\nSELESAI! {count} rekod berjaya dipindahkan.")

if __name__ == "__main__":
    run_migration()