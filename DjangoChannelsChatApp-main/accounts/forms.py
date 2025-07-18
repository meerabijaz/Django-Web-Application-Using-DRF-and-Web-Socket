from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class RegisterForm(UserCreationForm):
    security_question = forms.ChoiceField(
        choices=Profile.SECURITY_QUESTIONS,
        label="Security Question",
        help_text="Choose a security question for password recovery"
    )
    security_answer = forms.CharField(
        max_length=100,
        label="Security Answer",
        help_text="Provide an answer to your security question"
    )
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'security_question', 'security_answer')
    
    def clean_security_answer(self):
        answer = self.cleaned_data.get('security_answer')
        if answer:
            return answer.lower().strip()
        return answer

class AnswerAuthForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Username",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your username'})
    )
    security_answer = forms.CharField(
        max_length=100,
        label="Security Answer",
        widget=forms.TextInput(attrs={'placeholder': 'Answer your security question'})
    )
    
    def clean_security_answer(self):
        answer = self.cleaned_data.get('security_answer')
        if answer:
            return answer.lower().strip()
        return answer
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        security_answer = cleaned_data.get('security_answer')
        
        if username and security_answer:
            try:
                user = User.objects.get(username=username)
                profile = Profile.objects.get(user=user)
                if profile.security_answer.lower().strip() != security_answer:
                    raise forms.ValidationError("Invalid security answer.")
            except User.DoesNotExist:
                raise forms.ValidationError("Username not found.")
            except Profile.DoesNotExist:
                raise forms.ValidationError("User profile not found.")
        
        return cleaned_data

class ResetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter new password'}),
        min_length=8
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data 