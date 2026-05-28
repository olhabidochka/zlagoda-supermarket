from django.template.loader import render_to_string
from django.http import HttpResponse
import datetime


def generate_html_report(title, headers, data, report_type=''):
    now = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    html = render_to_string('supermarket/report_print.html', {
        'title': title,
        'headers': headers,
        'data': data,
        'generated_at': now,
        'report_type': report_type,
    })
    return html
