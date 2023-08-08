from django import template

register = template.Library()

@register.filter(name="add_class")
def add_class(field, cls):
    return field.as_widget(attrs={"class": cls})

@register.filter(name='dict_get')
def dict_get(d, k):
    return d[k]