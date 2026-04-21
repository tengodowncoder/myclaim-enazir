from django import forms
from .models import CustomUser

class PendaftaranForm(forms.ModelForm):
    # 1. Definisi pilihan sektor yang selari dengan Admin & PTDM
    SEKTOR_CHOICES = [
        ('', '-- Pilih Sektor --'),
        ('SPK', 'SPK'),
        ('SPIP', 'SPIP'),
        ('SPHEMK', 'SPHEMK'),
        ('SDTM', 'SDTM'),
        ('SSJK', 'SSJK'),
        ('SP', 'SP'),
        ('SDP', 'SDP'),
        ('SPKN', 'SPKN'),
    ]

    # 2. Field tambahan manual untuk password & pengesahan
    password = forms.CharField(
        label="Kata Laluan",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Gunakan No. IC sebagai password awal'})
    )
    confirm_password = forms.CharField(
        label="Sahkan Kata Laluan",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ulang semula password'})
    )

    # 3. Tukar field sektor kepada ChoiceField (Dropdown)
    sektor = forms.ChoiceField(
        choices=SEKTOR_CHOICES, 
        label='Sektor / Pejabat',
        widget=forms.Select(attrs={'class': 'form-select shadow-sm'})
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'no_ic', 'sektor']
        
        labels = {
            'username': 'ID Pengguna',
            'first_name': 'Nama Depan',
            'last_name': 'Nama Keluarga',
            'email': 'Emel Rasmi (@moe.gov.my)',
            'no_ic': 'No. Kad Pengenalan',
        }
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: azmi90'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Mohamad Azmi'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Bin Ali'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'mesti berakhir dengan @moe.gov.my'}),
            'no_ic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: 900101141234'}),
        }

    # 4. Logik Pengesahan (Email MOE & Password Match)
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")

        # Polis Emel: Hanya @moe.gov.my
        if email and not email.endswith('@moe.gov.my'):
            self.add_error('email', "Maaf! Hanya emel @moe.gov.my sahaja dibenarkan.")
        
        # Pastikan Password Padan
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Ralat! Kata laluan yang dimasukkan tidak sepadan.")
        
        return cleaned_data