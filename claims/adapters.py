from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    
    def pre_social_login(self, request, sociallogin):
        """
        Dijalankan setiap kali user login.
        Memastikan nama dan gambar sentiasa sync dengan akaun Google terkini.
        """
        user = sociallogin.user
        data = sociallogin.account.extra_data
        
        # 1. Sentiasa tarik gambar terbaru dari Google
        picture_url = data.get('picture')
        if picture_url:
            user.profile_picture_url = picture_url
            
        # 2. Sentiasa tarik nama penuh terbaru dari Google
        full_name = data.get('name')
        if full_name:
            user.first_name = full_name
            
        # Simpan perubahan jika user sudah wujud dalam database
        if user.id:
            user.save()

    def populate_user(self, request, sociallogin, data):
        """
        Dijalankan hanya semasa pendaftaran kali pertama (User baru).
        Menetapkan username unik berdasarkan emel.
        """
        user = super().populate_user(request, sociallogin, data)
        extra_data = sociallogin.account.extra_data
        
        # Set username dari emel (contoh: ali@moe.gov.my -> ali)
        email = extra_data.get('email')
        if email:
            new_username = email.split('@')[0]
            
            # Check kalau username dah wujud untuk elak IntegrityError
            if User.objects.filter(username=new_username).exists():
                import uuid
                new_username = f"{new_username}_{uuid.uuid4().hex[:4]}"
            
            user.username = new_username

        # Set Nama Penuh awal untuk user baru
        full_name = extra_data.get('name')
        if full_name:
            user.first_name = full_name

        return user