# catalog/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth.forms import UserCreationForm


class CombinedProfileForm(forms.ModelForm):
    old_password = forms.CharField(label='Старий пароль', widget=forms.PasswordInput(), required=False)
    new_password = forms.CharField(label='Новий пароль', widget=forms.PasswordInput(), required=False)

    phone = forms.CharField(label='Номер телефону', max_length=15, required=False)
    gender = forms.ChoiceField(label='Стать', choices=[('male', 'Чоловіча'), ('female', 'Жіноча')], required=False)

    first_name = forms.CharField(label='Ім’я', required=False)
    last_name = forms.CharField(label='Прізвище', required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        user = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        # заповнюємо поля з профілю, якщо існує
        if hasattr(user, 'userprofile'):
            self.fields['phone'].initial = user.userprofile.phone
            self.fields['gender'].initial = user.userprofile.gender

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Оновлюємо профіль
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get('phone')
            profile.gender = self.cleaned_data.get('gender')
            profile.save()
        return user

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=False, label="Ім’я")
    last_name = forms.CharField(required=False, label="Прізвище")
    phone = forms.CharField(required=False, label='Номер телефону')
    gender = forms.ChoiceField(
        required=False,
        label='Стать',
        choices=[('male', 'Чоловіча'), ('female', 'Жіноча')]
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

    def save(self, commit=True):
        user = super().save(commit=commit)
        phone = self.cleaned_data.get('phone')
        gender = self.cleaned_data.get('gender')

        if commit:
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            user_profile.phone = phone
            user_profile.gender = gender
            user_profile.save()
        return user

# catalog/forms.py
from django import forms
from .models import Rating

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'comment']
        labels = {
            'rating': 'Оцінка (1–5)',
            'comment': 'Ваш коментар'
        }
