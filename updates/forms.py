from django import forms

from .models import Comment, Log, Notice, Person


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            else:
                css_class = 'form-control'
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_class} {css_class}'.strip()
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['rows'] = 4


class LogForm(StyledModelForm):
    class Meta:
        model = Log
        fields = ['author_name', 'work_done', 'progress', 'issue', 'status']
        widgets = {
            'author_name': forms.TextInput(attrs={'autocomplete': 'name', 'class': 'remember-name'}),
            'work_done': forms.Textarea(attrs={'rows': 4}),
            'progress': forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 100, 'step': 5, 'data-range-output': 'progress-label'}),
            'issue': forms.Textarea(attrs={'rows': 3, 'placeholder': 'ถ้าไม่มี ปล่อยว่างได้'}),
            'status': forms.RadioSelect,
        }


class CommentForm(StyledModelForm):
    class Meta:
        model = Comment
        fields = ['author_name', 'message']
        widgets = {
            'author_name': forms.TextInput(attrs={'autocomplete': 'name', 'class': 'remember-name'}),
            'message': forms.Textarea(attrs={'rows': 3}),
        }


class PersonForm(StyledModelForm):
    class Meta:
        model = Person
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'autocomplete': 'name'})}


class NoticeForm(StyledModelForm):
    class Meta:
        model = Notice
        fields = ['title', 'content', 'recipient', 'deadline', 'task_status']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }


class PresidentLoginForm(forms.Form):
    password = forms.CharField(
        label='รหัสผ่านประธานสี',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )