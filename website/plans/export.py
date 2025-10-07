import io
from ..models import Plan

def export_xml_single(plan: Plan):
    xml_content = f"<plan id='{plan.id}' year='{plan.year}' name_org='{plan.name_org}' okpo='{plan.okpo}'/>"
    file_stream = io.BytesIO()
    file_stream.write(xml_content.encode("utf-8"))
    file_stream.seek(0)
    filename = f"plan_{plan.id}.xml"
    return file_stream, "application/xml", filename
    
def export_xlsx_single(plan: Plan):
    from openpyxl import Workbook
    
    wb = Workbook()
    if "Sheet" in wb.sheetnames:
        wb.remove(wb["Sheet"])
    
    title_xlsx(wb, plan)

    usage_xlsx(wb, plan)
    derections_xlsx(wb, plan)
    events_xlsx(wb, plan)

    file_stream = io.BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)
    filename = f"{plan.okpo}_{plan.year}.xlsx"
    return file_stream, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename

def export_pdf_single(plan: Plan):
    pass

def title_xlsx(wb, plan):
    from openpyxl.utils import get_column_letter
    from openpyxl.styles import Font, Alignment
    
    ws_title = wb.create_sheet("Титульный лист", 0)

    for col in range(1, 10):
        ws_title.column_dimensions[get_column_letter(col)].width = 20
    for row in range(1, 40):
        ws_title.row_dimensions[row].height = 25

    bold_font = Font(name="Times New Roman", size=12, bold=True)
    regular_font = Font(name="Times New Roman", size=12)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    right = Alignment(horizontal="right", vertical="center", wrap_text=True)

    ws_title.merge_cells("B4:D8")
    cell = ws_title["B4"]
    cell.value = (
        "СОГЛАСОВАНО:\n"
        "Департамент по энергоэффективности\n"
        "Госстандарта\n"
        "\n"
        "\n"
        "_________________________\n"
        "«___» ____________ 20__ г."
    )
    cell.font = regular_font
    cell.alignment = left

    ministrystr = "Министерство (концерн, государственный комитет)"
    if plan.organization.ministry != None:
        ministrystr = plan.organization.ministry

    ws_title.merge_cells("F4:H8")
    cell = ws_title["F4"]
    cell.value = (
        "УТВЕРЖДАЮ\n"
        f"{ministrystr}\n\n"
        "\n"
        "_________________________\n"
        "«___» ____________ 20__ г."
    )
    cell.font = regular_font
    cell.alignment = right

    ws_title.merge_cells("B12:H12")
    ws_title["B12"].value = "ПЛАН МЕРОПРИЯТИЙ ПО ЭНЕРГОСБЕРЕЖЕНИЮ"
    ws_title["B12"].font = bold_font
    ws_title["B12"].alignment = center

    ws_title.merge_cells("B13:H13")
    ws_title["B13"].value = f"{plan.name_org}"
    ws_title["B13"].font = bold_font
    ws_title["B13"].alignment = center

    ws_title.merge_cells("B14:H14")
    ws_title["B14"].value = f"на {plan.year} год"
    ws_title["B14"].font = bold_font
    ws_title["B14"].alignment = center

    # Целевые показатели
    ws_title.merge_cells("B20:D20")
    ws_title["B20"].value = "Целевые показатели: показатель энергосбрежения:"
    ws_title["B20"].font = regular_font
    ws_title["B20"].alignment = left

    ws_title.merge_cells("E20:H23")
    ws_title["E20"].value = (
        f"показатель энергосбережения - {plan.energy_saving}%\n"
        f"(задание по экономии ТЭР - {plan.share_fuel} т у.т.);\n"
        f"доля местных ТЭР в КПТ - {plan.saving_fuel}%;\n"
        f"доля местных ТЭР в КПТ - {plan.share_energy}%."
    )
    ws_title["E20"].font = regular_font
    ws_title["E20"].alignment = left

    ws_title.page_setup.orientation = ws_title.ORIENTATION_LANDSCAPE
    ws_title.page_setup.paperSize = ws_title.PAPERSIZE_A4
    ws_title.page_setup.fitToWidth = 1
    ws_title.page_setup.fitToHeight = 1

    return ws_title

def signatures_indicators_xlsx(ws, start_row, plan):
    from openpyxl.styles import Font, Alignment

    bold_font = Font(name="Times New Roman", size=11, bold=True)
    regular_font = Font(name="Times New Roman", size=11)
    left = Alignment(horizontal="left", vertical="top", wrap_text=True)

    def set_cell(ws, row, col_start, col_end, text, font, row_height=20):
        """
        Устанавливает текст в объединённой ячейке
        row_height - высота строки в пунктах
        """
        ws.merge_cells(start_row=row, start_column=col_start, end_row=row, end_column=col_end)
        cell = ws.cell(row=row, column=col_start)
        cell.value = text
        cell.font = font
        cell.alignment = left
        ws.row_dimensions[row].height = row_height


    set_cell(ws, start_row+6, 1, 2, "от Департамента по энергоэффективности Госстандарта", bold_font, row_height=20)
    set_cell(ws, start_row+7, 1, 2, 
        "Отдел анализа и прогнозирования развития энергосбережения\n"
        "_________________________\n"
        "«___» ____________ 20__ г.",
        regular_font, row_height=60
    )

    set_cell(ws, start_row+9, 1, 2, 
        "Начальник Минского городского управления\n"
        "по назору за рациональным использованием ТЭР\n"
        "_________________________\n"
        "«___» ____________ 20__ г.",
        regular_font, row_height=60
    )


    set_cell(ws, start_row+6, 4, 7, f"от {plan.name_org}", bold_font, row_height=45)
    set_cell(ws, start_row+7, 4, 7, 
        "________________________________________________\n"
        "________________________________________________\n"
        "«___» ____________ 20__ г.",
        regular_font, row_height=60
    )
    ministry_name = plan.organization.ministry
    ministrytext = f"от {ministry_name if ministry_name else 'Министерство (концерн, государственный комитет)'}"
    set_cell(ws, start_row+8, 4, 7, f"{ministrytext}", bold_font, row_height=45)
    set_cell(ws, start_row+9, 4, 7, 
        "________________________________________________\n"
        "________________________________________________\n"
        "«___» ____________ 20__ г.",
        regular_font, row_height=60
    )

    set_cell(ws, start_row+10, 4, 7, "от Минского городского исполнительного комитета", bold_font, row_height=45)
    set_cell(ws, start_row+11, 4, 7, 
        "________________________________________________\n"
        "«___» ____________ 20__ г.",
        regular_font, row_height=60
    )
    
def usage_xlsx(wb, plan):
    from openpyxl.styles import Font, Alignment, Border, Side
    
    ws = wb.create_sheet("Часть 1")
    
    bold_font = Font(name="Times New Roman", size=11, bold=True)
    regular_font = Font(name="Times New Roman", size=11)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )
    
    ws.merge_cells("A1:G1")
    ws["A1"].value = "Часть 1."
    ws["A1"].font = bold_font
    ws["A1"].alignment = center
    
    ws.merge_cells("A2:G2")
    ws["A2"].value = "1. Показатели использования топливно-энергетических ресурсов"
    ws["A2"].font = bold_font
    ws["A2"].alignment = center

    headers = [
        "№ п/п", 
        "Основные показатели по использованию ТЭР", 
        "Единица измерения", 
        f"{plan.year-1} г. отчет", 
        f"{plan.year} г. отчет", 
        f"{plan.year+1} г. отчет", 
        "Изменение ТЭР прогнозного года к предыдущему (увеличение +, снижение -)"
    ]
    ws.append(headers)
    
    column_widths = {
        "A": 6,    # № п/п
        "B": 60,   # Основные показатели
        "C": 18,   # Ед. изм.
        "D": 15,   # Предыдущий год
        "E": 15,   # Текущий год
        "F": 15,   # Прогноз
        "G": 20,   # Изменение
    }
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width
    
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=3, column=col)
        cell.font = bold_font
        cell.alignment = center
        cell.border = thin_border
    
    previous_group = None
    row_index = 3

    for usage in sorted(plan.indicators_usage, key=lambda u: (u.indicator.Group, u.indicator.RowN)):
        group_value = usage.indicator.Group if usage.indicator.Group != previous_group else ""
        previous_group = usage.indicator.Group
        
        row = [
            group_value, 
            usage.indicator.name if usage.indicator.name else "-",
            usage.indicator.unit.name,
            (usage.QYearPrev or 0),
            (usage.QYearCurr or 0),
            (usage.QYearNext or 0),
            (usage.QYearNext or 0) - (usage.QYearCurr or 0),
        ]
        ws.append(row)

        row_index += 1
        for col in range(1, len(row)+1):
            cell = ws.cell(row=row_index, column=col)
            if group_value:
                cell.font = bold_font
            else:
                cell.font = regular_font
            
            cell.alignment = center if col != 2 else left
            cell.border = thin_border
            cell.number_format = '0.00' 
    
    signatures_indicators_xlsx(ws, row_index + 1, plan)

    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    return ws

def derections_xlsx(wb, plan):
    from openpyxl.styles import Font, Alignment, Border, Side
    
    ws = wb.create_sheet("Часть 2")
    
    bold_font = Font(name="Times New Roman", size=11, bold=True)
    regular_font = Font(name="Times New Roman", size=11)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )
    
    ws.merge_cells("A1:E1")
    ws["A1"].value = "Часть 2."
    ws["A1"].font = bold_font
    ws["A1"].alignment = center
    
    ws.merge_cells("A2:E2")
    ws["A2"].value = f"2. Мероприятия по реализации основных направлений энергосбережения на {plan.year} год"
    ws["A2"].font = bold_font
    ws["A2"].alignment = center

    headers = [
        "№ п/п", 
        "Код основных направлений энергосбережения в соответствии с формой 4-энерго-сбережение (Госстандарт)", 
        "Наименование направлений в соответствии с формой 4-энергосбережения (Госстандарт)", 
        "Условно-годовой экономический эффект, т у.т.", 
        f"Ожидаемая экономия ТЭР от внедрения мероприятий в {plan.year} г., т у.т.", 
    ]
    ws.append(headers)
    
    column_widths = {
        "A": 6,    # № п/п
        "B": 30,   # Код
        "C": 60,   # Наименование
        "D": 15,   # Условно-годовой экономический эффект
        "E": 20,   # Ожидаемая экономия ТЭР
    }
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width
    
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=3, column=col)
        cell.font = bold_font
        cell.alignment = center
        cell.border = thin_border
    
    row_index = 3 

    for idx, measure in enumerate(sorted(plan.econ_measures, key=lambda u: u.direction.code), start=1):
        row_index += 1
        row = [
            idx, 
            measure.direction.code,
            measure.direction.name,
            float(measure.year_econ or 0),
            float(measure.estim_econ or 0),
        ]
        ws.append(row)

        for col in range(1, len(row)+1):
            cell = ws.cell(row=row_index, column=col)
            cell.font = regular_font
            cell.alignment = center if col not in [3] else left
            cell.border = thin_border
            cell.number_format = '0.00' 

    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0

    return ws

def signatures_events_xlsx(ws, start_row, plan):
    from openpyxl.styles import Font, Alignment

    bold_font = Font(name="Times New Roman", size=11, bold=True)
    regular_font = Font(name="Times New Roman", size=11)
    left = Alignment(horizontal="left", vertical="top", wrap_text=True)

    def set_cell(ws, row, col_start, col_end, text, font, row_height=20):
        """
        Устанавливает текст в объединённой ячейке
        row_height - высота строки в пунктах
        """
        ws.merge_cells(start_row=row, start_column=col_start, end_row=row, end_column=col_end)
        cell = ws.cell(row=row, column=col_start)
        cell.value = text
        cell.font = font
        cell.alignment = left
        ws.row_dimensions[row].height = row_height


    set_cell(ws, start_row+6, 2, 4, "от Департамента по энергоэффективности Госстандарта", bold_font, row_height=20)
    set_cell(ws, start_row+7, 2, 4, 
        "Производственно-техническое управление\n"
        "_________________________\n"
        "«___» ____________ 20__ г.",
        regular_font, row_height=60
    )

    set_cell(ws, start_row+9, 2, 4, 
        "Управление экономики и финансов\n"
        "_________________________\n"
        "«___» ____________ 20__ г.",
        regular_font, row_height=60
    )


    set_cell(ws, start_row+11, 2, 4, 
        "Начальник Минского городского управления\n"
        "по наздору за рациональным использованием ТЭР\n"
        "_________________________\n"
        "«___» ____________ 20__ г.",
        regular_font, row_height=60
    )

    set_cell(ws, start_row+6, 6, 11, f"от {plan.name_org}", bold_font, row_height=45)
    set_cell(ws, start_row+7, 6, 11, 
        "________________________________________________\n"
        "________________________________________________\n"
        "«___» ____________ 20__ г.",
        regular_font, row_height=60
    )

    ministry_name = plan.organization.ministry
    ministrytext = f"от {ministry_name if ministry_name else 'Министерство (концерн, государственный комитет)'}"
    set_cell(ws, start_row+8, 6, 11, f"{ministrytext}", bold_font, row_height=45)
    set_cell(ws, start_row+9, 6, 11, 
        "________________________________________________\n"
        "________________________________________________\n"
        "«___» ____________ 20__ г.",
        regular_font, row_height=60
    )

    set_cell(ws, start_row+10, 6, 11, "от Минского городского исполнительного комитета", bold_font, row_height=45)
    set_cell(ws, start_row+11, 6, 11, 
        "________________________________________________\n"
        "«___» ____________ 20__ г.",
        regular_font, row_height=60
    )

def events_xlsx(wb, plan):
    from openpyxl.styles import Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from ..models import Plan, EconMeasure, EconExec
    from sqlalchemy.orm import joinedload
    from ..views import get_cumulative_econ_metrics

    ws = wb.create_sheet("Часть 3")

    bold_font = Font(name="Times New Roman", size=11, bold=True)
    regular_font = Font(name="Times New Roman", size=11)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    vertical_text = Alignment(horizontal="center", vertical="center", textRotation=90, wrap_text=True)
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    ws.merge_cells("A1:R1")
    ws["A1"].value = "Часть 3."
    ws["A1"].font = bold_font
    ws["A1"].alignment = center

    ws.merge_cells("A2:R2")
    ws["A2"].value = "3. Мероприятия по увеличению использования местных топливно-энергетических ресурсов"
    ws["A2"].font = bold_font
    ws["A2"].alignment = center

    ws.merge_cells("A3:A5"); ws["A3"].value = "№ п/п"
    ws.merge_cells("B3:B5"); ws["B3"].value = "Код основных направлений энергосбережения"
    ws.merge_cells("C3:C5"); ws["C3"].value = "Наименование мероприятий, работ"
    ws.merge_cells("D3:D5"); ws["D3"].value = "Единицы измерения"
    ws.merge_cells("E3:E5"); ws["E3"].value = "Объем внедрения, ед."
    ws.merge_cells("F3:G3"); ws["F3"].value = "Условно-годовой экономический эффект"
    ws.merge_cells("F4:F5"); ws["F4"].value = "т у.т."
    ws.merge_cells("G4:G5"); ws["G4"].value = "руб."
    ws.merge_cells("H3:H5"); ws["H3"].value = "Ожидаемый срок внедрения мероприятия, квартал"
    ws.merge_cells("I3:I5"); ws["I3"].value = "Ожидаемый экономический эффект от внедрения мероприятия в текущем году, т у.т."
    ws.merge_cells("J3:J5"); ws["J3"].value = "Срок окупаемости, лет"
    ws.merge_cells("K3:K5"); ws["K3"].value = "Объем финансирования, руб."
    ws.merge_cells("L3:R3"); ws["L3"].value = "в том числе по источникам финансирования, руб."
    ws.merge_cells("L4:O4"); ws["L4"].value = "бюджетные"
    ws["L5"].value = "республиканский бюджет"
    ws["M5"].value = "областной (городской) бюджет"
    ws["N5"].value = "местный бюджет"
    ws["O5"].value = "другие"
    ws.merge_cells("P4:P5"); ws["P4"].value = "собственные средства организации"
    ws.merge_cells("Q4:Q5"); ws["Q4"].value = "кредиты банков, займы"
    ws.merge_cells("R4:R5"); ws["R4"].value = "иные"

    for row in ws.iter_rows(min_row=3, max_row=5, min_col=1, max_col=18):
        for cell in row:
            if not cell.value:
                continue
            if cell.coordinate in ("B3", "D3", "E3", "J3", "K3", "H3", "I3", "L5", "M5", "N5", "O5", "P4", "Q4", "R4"):
                cell.alignment = vertical_text
            else:
                cell.alignment = center
            cell.font = bold_font

    ws.row_dimensions[3].height = 55

    row_index = 6
    for col in range(1, 19):
        cell = ws.cell(row=row_index, column=col, value=col)
        cell.alignment = center
        cell.font = bold_font

    local_econ_execes = (EconExec.query
        .join(EconMeasure)
        .join(Plan)
        .filter(Plan.id == plan.id, EconExec.is_local == True)
        .options(joinedload(EconExec.econ_measures).joinedload(EconMeasure.plan))
        .all()
    )

    non_local_econ_execes = (EconExec.query
        .join(EconMeasure)
        .join(Plan)
        .filter(Plan.id == plan.id, EconExec.is_local == False)
        .options(joinedload(EconExec.econ_measures).joinedload(EconMeasure.plan))
        .all()
    )

    

    def add_section(title, execs, start_number=1):
        nonlocal row_index
        row_index += 1
        ws.merge_cells(start_row=row_index, start_column=1, end_row=row_index, end_column=18)
        ws.cell(row=row_index, column=1, value=title).font = bold_font
        ws.cell(row=row_index, column=1).alignment = center
        sum_cols = [5, 6, 7, 9, 11, 12, 13, 14, 15, 16, 17, 18]
        sums = {col: 0 for col in sum_cols}
        for idx, econ in enumerate(execs, start=start_number):
            row_index += 1
            row = [
                idx,
                econ.econ_measures.direction.code if econ.econ_measures and econ.econ_measures.direction else "",
                econ.name if hasattr(econ, "name") else "",
                econ.econ_measures.direction.unit.name if econ.econ_measures and econ.econ_measures.direction and econ.econ_measures.direction.unit else "",
                econ.Volume if hasattr(econ, "Volume") else 0,
                econ.EffTut if hasattr(econ, "EffTut") else 0,
                econ.EffRub if hasattr(econ, "EffRub") else 0,
                econ.ExpectedQuarter if hasattr(econ, "ExpectedQuarter") else 0,
                econ.EffCurrYear if hasattr(econ, "EffCurrYear") else 0,
                econ.Payback if hasattr(econ, "Payback") else 0,
                econ.VolumeFin if hasattr(econ, "VolumeFin") else 0,
                econ.BudgetState if hasattr(econ, "BudgetState") else 0,
                econ.BudgetRep if hasattr(econ, "BudgetRep") else 0,
                econ.BudgetLoc if hasattr(econ, "BudgetLoc") else 0,
                econ.BudgetOther if hasattr(econ, "BudgetOther") else 0,
                econ.MoneyOwn if hasattr(econ, "MoneyOwn") else 0,
                econ.MoneyLoan if hasattr(econ, "MoneyLoan") else 0,
                econ.MoneyOther if hasattr(econ, "MoneyOther") else 0
            ]
            for col in sum_cols:
                try:
                    sums[col] += float(row[col-1])
                except (TypeError, ValueError):
                    pass
            ws.append(row)
            for col_idx in range(1, 19):
                cell = ws.cell(row=row_index, column=col_idx)
                cell.alignment = left if col_idx == 3 else center
                cell.font = regular_font
        row_index += 1
        ws.cell(row=row_index, column=3, value="ИТОГО по разделу:").alignment = left
        for col in sum_cols:
            cell = ws.cell(row=row_index, column=col, value=sums[col])
            cell.alignment = center
            cell.font = regular_font
            cell.number_format = '0.00'
        return start_number + len(execs)

    next_number = add_section("Раздел 2.1 Мероприятия по экономии ТЭР (первоначальная ред.)", non_local_econ_execes, 1)
    add_section("Раздел 3.1. Мероприятия по увеличению использования местных ТЭР (первоначальная ред.)", local_econ_execes, next_number)

    row_index += 2
    ws.cell(row=row_index, column=3, value="Всего:").font = bold_font
    ws.cell(row=row_index, column=3).alignment = left
    sum_cols = [5, 6, 7, 9, 11, 12, 13, 14, 15, 16, 17, 18]
    total_sums = {col: 0 for col in sum_cols}
    for row in ws.iter_rows(min_row=6, max_row=row_index, min_col=3, max_col=18):
        if row[0].value == "ИТОГО по разделу:":
            for col in sum_cols:
                val = ws.cell(row=row[0].row, column=col).value
                try:
                    total_sums[col] += float(val)
                except (TypeError, ValueError):
                    pass
    for col in sum_cols:
        cell = ws.cell(row=row_index, column=col, value=total_sums[col])
        cell.alignment = center
        cell.font = bold_font
        cell.number_format = '0.00'

    quarters = [
        ("Январь–Март", "jan_mar"),
        ("Январь–Июнь", "jan_jun"),
        ("Январь–Сентябрь", "jan_sep"),
        ("Январь–Декабрь", "jan_dec")
    ]
    local_totals = get_cumulative_econ_metrics(plan.id, True)
    non_local_totals = get_cumulative_econ_metrics(plan.id, False)
    total_metrics = {
        'jan_mar_eff': local_totals['jan_mar']['eff_curr_year'] + non_local_totals['jan_mar']['eff_curr_year'],
        'jan_mar_vol': local_totals['jan_mar']['volume_fin'] + non_local_totals['jan_mar']['volume_fin'],
        'jan_jun_eff': local_totals['jan_jun']['eff_curr_year'] + non_local_totals['jan_jun']['eff_curr_year'],
        'jan_jun_vol': local_totals['jan_jun']['volume_fin'] + non_local_totals['jan_jun']['volume_fin'],
        'jan_sep_eff': local_totals['jan_sep']['eff_curr_year'] + non_local_totals['jan_sep']['eff_curr_year'],
        'jan_sep_vol': local_totals['jan_sep']['volume_fin'] + non_local_totals['jan_sep']['volume_fin'],
        'jan_dec_eff': local_totals['jan_dec']['eff_curr_year'] + non_local_totals['jan_dec']['eff_curr_year'],
        'jan_dec_vol': local_totals['jan_dec']['volume_fin'] + non_local_totals['jan_dec']['volume_fin']
    }

    for q_label, q_key in quarters:
        row_index += 1
        ws.cell(row=row_index, column=3, value=q_label).font = regular_font
        ws.cell(row=row_index, column=3).alignment = left
        for col in range(3, 19):
            c = ws.cell(row=row_index, column=col)
            c.alignment = left
        ws.cell(row=row_index, column=9, value=total_metrics[f"{q_key}_eff"]).number_format = '0.00'
        ws.cell(row=row_index, column=11, value=total_metrics[f"{q_key}_vol"]).number_format = '0.00'

    widths = [6, 12, 40, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11]
    for i, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = width

    for row in ws.iter_rows(min_row=3, max_row=row_index, min_col=1, max_col=18):
        for cell in row:
            cell.border = thin_border


    signatures_events_xlsx(ws, row_index + 1, plan)

    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0

    return ws
