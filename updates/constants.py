DEPARTMENTS = {
    'stan': {'name': 'แสตน', 'color': '#1F6F8B'},
    'kabuan': {'name': 'ขบวน', 'color': '#C2570C'},
    'sport': {'name': 'กีฬา', 'color': '#2E7D32'},
}

DEPARTMENT_CHOICES = [(slug, data['name']) for slug, data in DEPARTMENTS.items()]