import os
import django
import csv

# 1. SETUP DJANGO
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myclaim_system.settings')
django.setup()

from claims.models import Program

def clean_num(value):
    """Menukar nilai kepada nombor perpuluhan bersih"""
    if value is None or str(value).strip() in ["", "-"]:
        return 0.0
    val = str(value).replace('RM', '').replace(',', '').strip()
    try:
        return float(val)
    except:
        return 0.0

def run_sync():
    file_path = 'GENERATE FORM STATUS PERBELANJAAN - GABUNG-DATA-BELANJA.csv'
    
    if not os.path.exists(file_path):
        print(f"RALAT: Fail {file_path} tidak dijumpai!")
        return

    count = 0
    print("Memulakan penyelarasan Master Data (270 Rekod)...")

    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            nama_program = row.get('Nama Program', '').strip()
            if not nama_program:
                continue
            
            # Gunakan update_or_create: Jika nama dah ada, dia update. Jika tak ada, dia buat baru.
            program, created = Program.objects.update_or_create(
                nama_event=nama_program,
                defaults={
                    'sektor': row.get('Sektor', '').strip(),
                    'unit': row.get('Unit', '').strip(),
                    'jenis_tugas': row.get('Tugas', '').strip(),
                    'peruntukan': row.get('Peruntukan', '').strip(),
                    'bilangan_peserta': int(clean_num(row.get('Bilangan\nPeserta'))),
                    'pegawai_bertanggungjawab': row.get('Nama Pegawai Bertanggungjawab', '').strip(),
                    'gred_pegawai': row.get('Gred Pegawai', '').strip(),
                    'status_pelaksanaan': row.get('Status Pelaksanaan', 'belum').lower(),
                    'justifikasi': row.get('JUSTIFIKASI BELUM BERMULA/DIPINDA/DIBATALKAN', ''),
                    
                    # Anggaran (A1 - A4)
                    'os21000_a1': clean_num(row.get('0S21000 (a1)')),
                    'os24000_a2': clean_rm(row.get('OS24000 (a2)')), # Handle possible RM
                    'os27000_a3': clean_num(row.get('OS27000 (a3)')),
                    'os29000_a4': clean_num(row.get('OS29000 (a4)')),
                    
                    # Komitmen (B1 - B4)
                    'os21000_b1': clean_num(row.get('0S21000 (b1)')),
                    'os24000_b2': clean_num(row.get('OS24000 (b2)')),
                    'os27000_b3': clean_num(row.get('OS27000 (b3)')),
                    'os29000_b4': clean_num(row.get('OS29000 (b4)')),
                }
            )
            count += 1
            if count % 50 == 0:
                print(f"✓ Berjaya selaraskan {count} program...")

    print(f"\nSIAP! Sebanyak {count} program kini 100% sama dengan fail Master Excel.")

def clean_rm(value):
    # Fungsi tambahan untuk handle RM yang mungkin terselit
    return clean_num(value)

if __name__ == "__main__":
    run_sync()