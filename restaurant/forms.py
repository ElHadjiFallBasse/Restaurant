from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div
from .models import Order, OrderItem, Reservation, Customer, MenuItem, Table

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['table', 'customer', 'notes']
        widgets = {
            'table': forms.Select(attrs={'class': 'form-select'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('table', css_class='col-md-6'),
                Column('customer', css_class='col-md-6'),
            ),
            'notes',
            Submit('submit', 'Créer la commande', css_class='btn btn-primary')
        )
        
        # Filtrer les tables disponibles
        self.fields['table'].queryset = Table.objects.filter(is_available=True)
        self.fields['customer'].empty_label = "Client anonyme"

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'special_instructions']
        widgets = {
            'menu_item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['menu_item'].queryset = MenuItem.objects.filter(is_available=True)

# Formset pour les articles de commande
OrderItemFormSet = inlineformset_factory(
    Order, 
    OrderItem, 
    form=OrderItemForm,
    extra=1,
    can_delete=True
)

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['customer', 'table', 'date', 'time', 'party_size', 'special_requests']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'table': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'party_size': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('customer', css_class='col-md-6'),
                Column('table', css_class='col-md-6'),
            ),
            Row(
                Column('date', css_class='col-md-4'),
                Column('time', css_class='col-md-4'),
                Column('party_size', css_class='col-md-4'),
            ),
            'special_requests',
            Submit('submit', 'Créer la réservation', css_class='btn btn-primary')
        )

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'date_of_birth']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
            ),
            Row(
                Column('email', css_class='col-md-6'),
                Column('phone', css_class='col-md-6'),
            ),
            'address',
            'date_of_birth',
            Submit('submit', 'Enregistrer', css_class='btn btn-primary')
        )

class MenuItemSearchForm(forms.Form):
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un plat...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Category
        self.fields['category'].queryset = Category.objects.all()

class OrderFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'Tous les statuts')] + list(Order.STATUS_CHOICES)
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Row(
                Column('status', css_class='col-md-6'),
                Column('date', css_class='col-md-6'),
            ),
            Submit('submit', 'Filtrer', css_class='btn btn-outline-primary')
        )