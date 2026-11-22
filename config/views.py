from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import PollutionReport, TapWaterTest
from django.db.models import Case, When, Value, IntegerField
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.db.models import Q
import csv
from pathlib import Path
from datetime import datetime



def home(request):
    reports = PollutionReport.objects.annotate(
        priority=Case(
            When(category='waterlogging', then=Value(1)),
            When(category='water_contamination', then=Value(2)),
            When(category='river_pond_pollution', then=Value(3)),
            When(category='other', then=Value(4)),
            default=Value(5),
            output_field=IntegerField()
        )
    ).order_by('is_resolved', 'priority', '-created_at')

    high_priority_count = reports.filter(
        category='waterlogging',
        is_resolved=False
    ).count()

    return render(request, 'index.html', {
        'reports': reports,
        'high_priority_count': high_priority_count
    })


def report_pollution(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        location = request.POST.get('location', '').strip()
        category = request.POST.get('category', '')
        description = request.POST.get('description', '').strip()
        photo = request.FILES.get('photo')

        valid_categories = {
            choice[0]
            for choice in PollutionReport.CATEGORY_CHOICES
        }

        if title and location and description and category in valid_categories:
            PollutionReport.objects.create(
                title=title,
                location=location,
                category=category,
                description=description,
                photo=photo,
            )

            messages.success(
                request,
                'Pollution report submitted successfully!'
            )
            return redirect('report_pollution')

        messages.error(
            request,
            'Please fill in all required fields correctly.'
        )

    return render(request, 'report.html')

def dashboard(request):
    total_reports = PollutionReport.objects.count()

    pending_reports = PollutionReport.objects.filter(
        is_resolved=False
    ).count()

    resolved_reports = PollutionReport.objects.filter(
        is_resolved=True
    ).count()

    high_priority_reports = PollutionReport.objects.filter(
        category='waterlogging',
        is_resolved=False
    ).count()

    # Get filter values from URL
    search = request.GET.get('search', '').strip()
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')

    # Priority sorting
    reports = PollutionReport.objects.annotate(
        priority=Case(
            When(category='waterlogging', then=Value(1)),
            When(category='water_contamination', then=Value(2)),
            When(category='river_pond_pollution', then=Value(3)),
            When(category='other', then=Value(4)),
            default=Value(5),
            output_field=IntegerField()
        )
    ).order_by('is_resolved', 'priority', '-created_at')

    # Search by title or location
    if search:
        reports = reports.filter(
            Q(title__icontains=search) |
            Q(location__icontains=search)
        )

    # Category filter
    valid_categories = {
        choice[0] for choice in PollutionReport.CATEGORY_CHOICES
    }

    if category in valid_categories:
        reports = reports.filter(category=category)

    # Status filter
    if status == 'pending':
        reports = reports.filter(is_resolved=False)
    elif status == 'resolved':
        reports = reports.filter(is_resolved=True)

    # Priority filter
    if priority == 'high':
        reports = reports.filter(category='waterlogging')
    elif priority == 'medium':
        reports = reports.filter(category='water_contamination')
    elif priority == 'low':
        reports = reports.filter(
            category__in=['river_pond_pollution', 'other']
        )

    context = {
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'resolved_reports': resolved_reports,
        'high_priority_reports': high_priority_reports,
        'reports': reports,
        'search': search,
        'selected_category': category,
        'selected_status': status,
        'selected_priority': priority,
        'category_choices' : PollutionReport.CATEGORY_CHOICES,
    }

    return render(request, 'dashboard.html', context)
    

@staff_member_required
@require_POST
def resolve_report(request, report_id):

    report = get_object_or_404(
        PollutionReport,
        id=report_id
    )

    report.is_resolved = True
    report.save()

    messages.success(
        request,
        'Pollution report marked as resolved!'
    )

    return redirect('dashboard')

def water_quality(request):
    source = request.GET.get('source', '')
    state = request.GET.get('state', '')
    district = request.GET.get('district', '')
    block = request.GET.get('block', '')
    village = request.GET.get('village', '')
    history = request.GET.get('history') == '1'

    tap_report = None
    tap_alerts = []
    tap_parameter_checks = []
    tap_status = 'Data Not Available'
    tap_class = 'neutral'

    if source == 'tap_water' and district and village:
        tap_report = TapWaterTest.objects.filter(
            state__iexact=state,
            district__iexact=district,
            village__iexact=village
        ).order_by('-sample_date', '-created_at').first()

    if tap_report:
        tap_parameters = [
            {
                'name': 'pH',
                'value': tap_report.ph,
                'min': 6.5,
                'acceptable_max': 8.5,
                'permissible_max': 8.5,
                'unit': ''
            },
            {
                'name': 'TDS',
                'value': tap_report.tds,
                'min': 0,
                'acceptable_max': 500,
                'permissible_max': 2000,
                'unit': 'mg/L'
            },
            {
                'name': 'Fluoride',
                'value': tap_report.fluoride,
                'min': 0,
                'acceptable_max': 1.0,
                'permissible_max': 1.5,
                'unit': 'mg/L'
            },
            {
                'name': 'Nitrate',
                'value': tap_report.nitrate,
                'min': 0,
                'acceptable_max': 45,
                'permissible_max': 45,
                'unit': 'mg/L'
            },
            {
                'name': 'Turbidity',
                'value': tap_report.turbidity,
                'min': 0,
                'acceptable_max': 1,
                'permissible_max': 5,
                'unit': 'NTU'
            },
            {
                'name': 'Arsenic',
                'value': tap_report.arsenic,
                'min': 0,
                'acceptable_max': 0.01,
                'permissible_max': 0.01,
                'unit': 'mg/L'
            },
            {
                'name': 'Free Residual Chlorine',
                'value': tap_report.free_residual_chlorine,
                'min': 0.2,
                'acceptable_max': 1.0,
                'permissible_max': 1.0,
                'unit': 'mg/L'
            },
        ]

        has_danger = False
        has_warning = False

        for item in tap_parameters:
            value = item['value']
            status = 'Not Available'

            if value is None:
                tap_alerts.append(
                    f"{item['name']}: Test data not available."
                )

            elif item['name'] == 'Free Residual Chlorine' and value < 0.2:
                status = 'Warning'
                has_warning = True
                tap_alerts.append(
                    'WARNING: Free Residual Chlorine is below '
                    'the recommended minimum of 0.2 mg/L.'
                )

            elif value < item['min'] or value > item['permissible_max']:
                status = 'Danger'
                has_danger = True
                tap_alerts.append(
                    f"DANGER: {item['name']} value "
                    f"{value} {item['unit']} is outside "
                    f"the permissible limit."
                )

            elif value > item['acceptable_max']:
                status = 'Warning'
                has_warning = True
                tap_alerts.append(
                    f"WARNING: {item['name']} value "
                    f"{value} {item['unit']} exceeds "
                    f"the acceptable limit."
                )

            else:
                status = 'Within limit'

            tap_parameter_checks.append({
                **item,
                'status': status,
            })

        if tap_report.e_coli_detected is True:
            has_danger = True
            tap_alerts.append(
                'DANGER: E. coli detected in water.'
            )

        elif tap_report.e_coli_detected is None:
            tap_alerts.append(
                'E. coli: Test data not available.'
            )

        if tap_report.total_coliform_detected is True:
            has_danger = True
            tap_alerts.append(
                'DANGER: Total Coliform detected in water.'
            )

        elif tap_report.total_coliform_detected is None:
            tap_alerts.append(
                'Total Coliform: Test data not available.'
            )

        if has_danger:
            tap_status = 'Unsafe Indicators Detected'
            tap_class = 'danger'

        elif has_warning:
            tap_status = 'Needs Attention'
            tap_class = 'warning'

        elif (
            all(item['value'] is not None for item in tap_parameters)
            and tap_report.e_coli_detected is False
            and tap_report.total_coliform_detected is False
        ):
            tap_status = 'No Issues Found in Tested Parameters'
            tap_class = 'good'

        else:
            tap_status = 'Insufficient Data'
            tap_class = 'neutral'

    csv_file = (
        Path(__file__).resolve().parent.parent
        / 'data'
        / 'gwq_chemical_parameter_manual_cgwb_up_1961_2025.csv'
    )

    water_records = []

    if source == 'groundwater' and district and csv_file.exists():
        with open(csv_file, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)

            for record in reader:
                if record.get('District', '').strip().lower() != district.strip().lower():
                    continue

                if block and record.get('Block', '').strip().lower() != block.strip().lower():
                    continue

                if village and record.get('Village', '').strip().lower() != village.strip().lower():
                    continue

                date_text = record.get('Data Acquisition Time', '').strip()

                try:
                    record_date = datetime.strptime(
                        date_text, '%d-%m-%Y %H:%M'
                    )
                except ValueError:
                    record_date = datetime.min

                water_records.append((record_date, record))

    # Sort records by date, newest first
    water_records.sort(key=lambda item: item[0], reverse=True)

    total_records = len(water_records)

    # Keep all records for parameter analysis
    all_water_records = water_records.copy()

    if not history:
        water_records = water_records[:1]

    water_records = [
        record for date, record in water_records
    ]

    # Define water quality parameters
    parameters = [
        {
            'name': 'pH',
            'fields': ['Potential of hydrogen (pH)'],
            'min': 6.5,
            'max_acceptable': 8.5,
            'max_permissible': 8.5,
            'unit': ''
        },
        {
            'name': 'TDS',
            'fields': ['Total Dissolved solids (mg/L)'],
            'min': 0,
            'max_acceptable': 500,
            'max_permissible': 2000,
            'unit': 'mg/L'
        },
        {
            'name': 'Fluoride',
            'fields': ['Fluoride (mg/L)'],
            'min': 0,
            'max_acceptable': 1.0,
            'max_permissible': 1.5,
            'unit': 'mg/L'
        },
        {
            'name': 'Nitrate',
            'fields': ['Nitrate (mg/L)', 'Nitrate N (mgN/L)'],
            'min': 0,
            'max_acceptable': 45,
            'max_permissible': 45,
            'unit': 'mg/L'
        },
    ]

    parameter_checks = []

    # Find the latest available value for every parameter
    for item in parameters:
        found_value = None
        found_date = 'Not Available'

        for record_date, record in all_water_records:
            raw_value = ''

            for field in item['fields']:
                for key in record.keys():
                    if key.strip().lower() == field.strip().lower():
                        raw_value = record.get(key, '').strip()
                        break

                if raw_value:
                    break

            if raw_value and raw_value.lower() not in [
                'not available', '-', 'na', 'null', ''
            ]:
                try:
                    found_value = float(raw_value)
                    found_date = record.get(
                        'Data Acquisition Time', 'Not Available'
                    )
                    break
                except (ValueError, TypeError):
                    continue

        status = 'Not Available'

        if found_value is not None:
            if (
                found_value < item['min']
                or found_value > item['max_permissible']
            ):
                status = 'Danger'
            elif found_value > item['max_acceptable']:
                status = 'Warning'
            else:
                status = 'Within limit'

        parameter_checks.append({
            'name': item['name'],
            'value': found_value,
            'unit': item['unit'],
            'limit': f"{item['min']} - {item['max_acceptable']}",
            'status': status,
            'date': found_date,
        })

    # Overall water quality assessment
    available_checks = [
        item for item in parameter_checks
        if item['value'] is not None
    ]

    if any(item['status'] == 'Danger' for item in parameter_checks):
        overall_status = 'Unsafe Indicators Detected'
        overall_class = 'danger'

    elif any(item['status'] == 'Warning' for item in parameter_checks):
        overall_status = 'Needs Attention'
        overall_class = 'warning'

    elif available_checks:
        overall_status = 'No Danger Detected in Available Parameters'
        overall_class = 'good'

    else:
        overall_status = 'Insufficient Data'
        overall_class = 'neutral'

    # Generate location options for dropdowns
    district_options = set()
    block_options = set()
    village_options = set()

    if source == 'groundwater' and csv_file.exists():
        with open(csv_file, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)

            for record in reader:
                record_district = record.get('District', '').strip()
                record_block = record.get('Block', '').strip()
                record_village = record.get('Village', '').strip()

                if record_district:
                    district_options.add(record_district)

                if district and record_district.lower() == district.lower():
                    if record_block:
                        block_options.add(record_block)

                    if (
                        block
                        and record_block.lower() == block.lower()
                        and record_village
                    ):
                        village_options.add(record_village)

    elif source == 'tap_water':
        tap_locations = TapWaterTest.objects.filter(
            state__iexact=state
        )

        district_options.update(
            tap_locations.exclude(district='')
            .values_list('district', flat=True)
            .distinct()
        )

        if district:
            district_locations = tap_locations.filter(
                district__iexact=district
            )

            block_options.update(
                district_locations.exclude(block='')
                .values_list('block', flat=True)
                .distinct()
            )

            village_locations = district_locations

            if block:
                village_locations = village_locations.filter(
                    block__iexact=block
                )

            village_options.update(
                village_locations.exclude(village='')
                .values_list('village', flat=True)
                .distinct()
            )

    district_options = sorted(district_options, key=str.lower)
    block_options = sorted(block_options, key=str.lower)
    village_options = sorted(village_options, key=str.lower)   

    context = {
        'source': source,
        'state': state,
        'district': district,
        'block': block,
        'village': village,
        'water_records': water_records,
        'total_records': total_records,
        'history': history,
        'parameter_checks': parameter_checks,
        'overall_status': overall_status,
        'overall_class': overall_class,
        'tap_report' : tap_report,
        'tap_alerts' : tap_alerts,
        'tap_status' : tap_status,
        'tap_parameter_checks': tap_parameter_checks,
        'tap_class': tap_class,
        'district_options': district_options,
        'block_options': block_options,
        'village_options': village_options,
    }

    return render(request, 'water_quality.html', context)
 