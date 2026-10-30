# mainapp/views.py

import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse
from .models import DemandRecord

def upload_demand_excel_pandas(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        
        try:
            df = pd.read_excel(excel_file, engine='openpyxl')
            df = df.dropna(subset=['Material'])
            
            records = []
            for _, row in df.iterrows():
                records.append(
                    DemandRecord(
                        material=str(row['Material']).strip(),
                        description=str(row.get('Description', '')).strip(),
                        unit=str(row.get('Unit', '')).strip(),
                        record_type=str(row.get('RecordType', '')).strip(),
                        work_center=str(row.get('WorkCenter', '')).strip(),
                        calendar_day=pd.to_datetime(row['CalendarDay']).date(),
                        quantity=float(row.get('Quantity', 0))
                    )
                )
            
            # --- IT GOES RIGHT HERE ---
            DemandRecord.objects.bulk_create(
                records, 
                batch_size=1000, 
                ignore_conflicts=True
            )
            # --------------------------
            
            return JsonResponse({'status': 'success', 'created_count': len(records)})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return render(request, 'mainapp/upload.html')

def index_view(request):
    # Example view pulling saved records and inventory metrics
    demand_records = DemandRecord.objects.all()[:100]  # Limiting sample display
    inventory_items = Inventory.objects.all()

    context = {
        "records": demand_records,
        "inventory_count": inventory_items.count(),
    }
    
    return render(request, 'excel_thing/index.html', {'demand_records': demand_records})