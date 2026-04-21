import os
import django

# 1. Setup persekitaran Django
# Ganti 'myclaim_system' dengan nama folder projek anda jika berbeza
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myclaim_system.settings') 
django.setup()

from claims.models import Program

def masukkan_data():
    data_program = [
        ('BPM', 'SEWAAN KPICT', '010504'),
        ('BPM', 'PENYELENGGARAAN KPICT', '010507'),
        ('BPK', 'KURIKULUM PERSEKOLAHAN 2027', '040307'),
        ('BPK', 'PLAN', '062305'),
        ('BPPDP', 'STEM', '062310'),
        ('BPPDP', 'KBAT', '062304'),
        ('BPSH', 'MBMMBI', '060306'),
        ('BKEW', 'GCPC', '040407'),
        ('BPG', 'TS25', '062201'),
        ('BPG', 'LDP', '050202'),
        ('IAB', 'PENGURUSAN LATIHAN', '050302'),
        ('BSKK', 'PPDAS', '062301'),
        ('BPM', 'MAKmur', '020101'),
        ('BPSP', 'PPPPC', '062306'),
        ('BPSH', 'PEKPS', '062302'),
        ('JN', 'DSA', '040401'),
        ('BSKK', 'PERPADUAN', '062301'),
        ('BPSM', 'PENGURUSAN', '040401'),
        ('IPGM', 'MBMMBI', '060306'),
        ('JN', 'INISIATIF #59 DSA', '040401'),
    ]

    print("--- Memulakan Proses Tambah Program ---")
    count = 0
    for sek, nama, kod in data_program:
        obj, created = Program.objects.get_or_create(
            sektor=sek,
            nama_program=nama,
            kod_aktiviti=kod
        )
        if created:
            print(f"✅ Berjaya: {nama} ({sek})")
            count += 1
        else:
            print(f"⚠️ Langkau: {nama} sudah wujud.")
    
    print(f"--- Selesai! {count} program baru ditambah. ---")

if __name__ == "__main__":
    masukkan_data()