import os
import django
import csv
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myclaim_system.settings')
django.setup()

from claims.models import Program

def clean_num(value):
    if value is None or str(value).strip() in ["", "-", "0"]:
        return 0.0
    val = str(value).replace('RM', '').replace(',', '').strip()
    try:
        return float(val)
    except:
        return 0.0

def parse_date(date_str):
    if not date_str or str(date_str).strip() in ["", "-"]:
        return None
    try:
        return datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
    except ValueError:
        try:
            return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
        except:
            return None

def run_reset():
    file_path = 'GENERATE FORM STATUS PERBELANJAAN - GABUNG-DATA-BELANJA.csv'
    
    if not os.path.exists(file_path):
        print(f"RALAT: Fail {file_path} tidak dijumpai!")
        return

    # 1. PADAM SEMUA DATA (OPERASI CUCI HABIS)
    print("--- MEMULAKAN PROSES PEMBERSIHAN ---")
    bilangan_lama = Program.objects.count()
    print(f"Dijumpai {bilangan_lama} rekod lama dlm database.")
    
    Program.objects.all().delete() 
    print("SEMUA rekod lama (termasuk 'Tuntutan Manual') telah DIPADAM.")

    # 2. IMPORT DATA BARU DARI EXCEL
    print(f"Sedang membaca fail: {file_path}")

    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        col_justifikasi = next((h for h in reader.fieldnames if 'JUSTIFIKASI' in h.upper()), None)
        
        count = 0
        for row in reader:
            nama = row.get('Nama Program', '').strip()
            if not nama:
                continue

            status_raw = row.get('Status Pelaksanaan', '').strip().lower()
            status_final = 'belum'
            if 'selesai' in status_raw: status_final = 'selesai'
            elif 'pinda' in status_raw: status_final = 'pinda'
            elif 'batal' in status_raw: status_final = 'batal'
            elif 'berjalan' in status_raw: status_final = 'berjalan'
            
            Program.objects.create(
                nama_event=nama,
                sektor=row.get('Sektor', '').strip(),
                unit=row.get('Unit', '').strip(),
                jenis_tugas=row.get('Tugas', '').strip(),
                peruntukan=row.get('Peruntukan', '').strip(),
                bilangan_peserta=int(clean_num(row.get('Bilangan\nPeserta')) or 0),
                tarikh_mula=parse_date(row.get('Tarikh Mula') or row.get('TARIKH MULA')),
                tarikh_tamat=parse_date(row.get('Tarikh Tamat') or row.get('TARIKH TAMAT')),
                justifikasi=row.get(col_justifikasi, '').strip() if col_justifikasi else '',
                pegawai_bertanggungjawab=row.get('Nama Pegawai Bertanggungjawab', '').strip(),
                gred_pegawai=row.get('Gred Pegawai', '').strip(),
                status_pelaksanaan=status_final,
                os21000_a1=clean_num(row.get('OS21000 (a1)') or row.get('0S21000 (a1)')),
                os24000_a2=clean_num(row.get('OS24000 (a2)')),
                os27000_a3=clean_num(row.get('OS27000 (a3)')),
                os29000_a4=clean_num(row.get('OS29000 (a4)')),
                os21000_b1=clean_num(row.get('OS21000 (b1)') or row.get('0S21000 (b1)')),
                os24000_b2=clean_num(row.get('OS24000 (b2)')),
                os27000_b3=clean_num(row.get('OS27000 (b3)')),
                os29000_b4=clean_num(row.get('OS29000 (b4)')),
            )
            count += 1

    print(f"IMPORT BERJAYA! {count} rekod baru telah dimasukkan.")
    print(f"JUMLAH TERKINI DLM DATABASE: {Program.objects.count()}")

if __name__ == "__main__":
    run_reset()