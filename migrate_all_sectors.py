import os
import django
import csv

# 1. SETUP DJANGO
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myclaim_system.settings')
django.setup()

from claims.models import Program

def clean_rm(value):
    """Menukar 'RM1,200.50' atau '-' kepada float 1200.5"""
    if not value or str(value).strip() == "-": return 0.0
    val = str(value).replace('RM', '').replace(',', '').strip()
    try:
        return float(val)
    except:
        return 0.0

def get_col(row, keywords):
    """Mencari nama kolum berdasarkan kata kunci (elak ralat trailing spaces)"""
    for key in row.keys():
        for k in keywords:
            if k.lower() in key.lower():
                return key
    return None

def run_mega_migration():
    # Senarai fail yang anda berikan
    files = [
        'Status Perbelanjaan SPK - STATUS PERBELANJAAN.csv',
        'Status Perbelanjaan SPKN - STATUS PERBELANJAAN.csv',
        'Status Perbelanjaan SDP - STATUS PERBELANJAAN.csv',
        'Status Perbelanjaan SP - STATUS PERBELANJAAN.csv',
        'Status Perbelanjaan SSJK - STATUS PERBELANJAAN.csv',
        'Status Perbelanjaan SDTM - STATUS PERBELANJAAN.csv',
        'Status Perbelanjaan SPHEMK - STATUS PERBELANJAAN.csv',
        'Status Perbelanjaan SPIP - STATUS PERBELANJAAN.csv'
    ]
    
    total_updated = 0

    for f in files:
        if not os.path.exists(f):
            print(f"SKIPPED: Fail {f} tidak dijumpai.")
            continue
            
        print(f"Memproses Sektor: {f.split(' ')[2]}...")
        
        with open(f, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Cari Nama Program (keyword handling)
                col_nama = get_col(row, ['Nama Program'])
                if not col_nama or not row[col_nama]: continue
                
                nama = row[col_nama].strip()
                
                # Cari program sedia ada atau cipta baru
                program, created = Program.objects.get_or_create(
                    nama_event=nama,
                    defaults={'sektor': row.get('Sektor', '').strip()}
                )
                
                # Kemaskini Detail Pegawai & Justifikasi
                program.unit = row.get('Unit', program.unit)
                program.jenis_tugas = row.get('Tugas', program.jenis_tugas)
                program.peruntukan = row.get('Peruntukan', program.peruntukan)
                program.pegawai_bertanggungjawab = row.get('Nama Pegawai Bertanggungjawab', program.pegawai_bertanggungjawab)
                program.gred_pegawai = row.get('Gred Pegawai', program.gred_pegawai)
                program.status_pelaksanaan = row.get('Status Pelaksanaan', 'selesai').lower()
                
                col_jus = get_col(row, ['JUSTIFIKASI'])
                if col_jus: program.justifikasi = row[col_jus]

                # Kemaskini Bajet OS (A1 - A4)
                program.os21000_a1 = clean_rm(row.get('0S21000 (a1)') or row.get('OS21000 (a1)'))
                program.os24000_a2 = clean_rm(row.get('OS24000 (a2)'))
                program.os27000_a3 = clean_rm(row.get('OS27000 (a3)'))
                program.os29000_a4 = clean_rm(row.get('OS29000 (a4)'))
                
                # Kemaskini Komitmen OS (B1 - B4)
                program.os21000_b1 = clean_rm(row.get('0S21000 (b1)') or row.get('0S21000 (b)') or row.get('OS21000 (b)'))
                program.os24000_b2 = clean_rm(row.get('OS24000 (b2)') or row.get('OS24000 (b)'))
                program.os27000_b3 = clean_rm(row.get('OS27000 (b3)') or row.get('OS27000 (b)'))
                program.os29000_b4 = clean_rm(row.get('OS29000 (b4)') or row.get('OS29000 (b)'))
                
                program.save()
                total_updated += 1

    print(f"\nTAHNIAH! {total_updated} Rekod Program bagi SEMUA SEKTOR berjaya dikemaskini!")

if __name__ == "__main__":
    run_mega_migration()