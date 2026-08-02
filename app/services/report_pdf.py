from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from .finance import summarize


BLUE = colors.HexColor("#153E52")
TEAL = colors.HexColor("#16A085")
LIGHT = colors.HexColor("#EEF4F6")
GRAY = colors.HexColor("#60727C")


def _money(value):
    text = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {text}"


def _date(value):
    return value.strftime("%d/%m/%Y")


def _table(data, widths, header=True, font_size=8):
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CCD9DE")),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, LIGHT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    table.setStyle(TableStyle(commands))
    return table


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D8E2E6"))
    canvas.line(15 * mm, 11 * mm, landscape(A4)[0] - 15 * mm, 11 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRAY)
    canvas.drawString(15 * mm, 7 * mm, "Rota Positiva")
    canvas.drawRightString(landscape(A4)[0] - 15 * mm, 7 * mm, f"Página {doc.page}")
    canvas.restoreState()


def build_report(records, start, end):
    stream = BytesIO()
    doc = SimpleDocTemplate(
        stream, pagesize=landscape(A4), rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=14 * mm, bottomMargin=16 * mm,
        title="Relatório Financeiro - Rota Positiva", author="Rota Positiva",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleCustom", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20,
        leading=24, textColor=BLUE, alignment=TA_CENTER, spaceAfter=4,
    )
    subtitle = ParagraphStyle(
        "Subtitle", parent=styles["Normal"], fontSize=9, textColor=GRAY,
        alignment=TA_CENTER, spaceAfter=12,
    )
    heading = ParagraphStyle(
        "HeadingCustom", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, textColor=BLUE, spaceBefore=8, spaceAfter=6,
    )
    normal = ParagraphStyle("Body", parent=styles["Normal"], fontSize=8, leading=10)
    summary = summarize(records)
    generated = datetime.now().astimezone().strftime("%d/%m/%Y às %H:%M")

    story = [
        Paragraph("Relatório Financeiro", title),
        Paragraph(f"Período de {_date(start)} a {_date(end)} | Gerado em {generated}", subtitle),
    ]
    cards = [
        ["Faturamento", "Despesas", "Lucro líquido", "Quilômetros"],
        [_money(summary["revenue"]), _money(summary["expenses"]),
         _money(summary["profit"]), f'{float(summary["kilometers"]):,.2f} km'.replace(",", "X").replace(".", ",").replace("X", ".")],
        ["Ganho médio/km", "Custo médio/km", "Dias registrados", "Período"],
        [_money(summary["gross_per_km"]), _money(summary["cost_per_km"]),
         str(len(records)), f"{_date(start)} - {_date(end)}"],
    ]
    summary_table = _table(cards, [63 * mm] * 4, header=False, font_size=9)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 2), (-1, 2), TEAL), ("TEXTCOLOR", (0, 2), (-1, 2), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story += [summary_table, Spacer(1, 4 * mm), Paragraph("Despesas por categoria", heading)]
    category_rows = [["Categoria", "Total", "% das despesas"]]
    for name, value in summary["by_category"].items():
        percent = (value / summary["expenses"] * 100) if summary["expenses"] else 0
        category_rows.append([name, _money(value), f"{float(percent):.1f}%".replace(".", ",")])
    if len(category_rows) == 1:
        category_rows.append(["Nenhuma despesa no período", _money(0), "0,0%"])
    story += [_table(category_rows, [110 * mm, 70 * mm, 70 * mm], font_size=8)]

    story += [Paragraph("Registros diários", heading)]
    daily_rows = [["Data", "Faturamento", "Km", "Despesas", "Lucro", "Ganho/km", "Custo/km", "Observações"]]
    for record in records:
        daily_rows.append([
            _date(record.date), _money(record.gross_revenue), f"{float(record.kilometers):.2f}",
            _money(record.total_expenses), _money(record.net_profit), _money(record.gross_per_km),
            _money(record.cost_per_km), Paragraph(escape(record.notes or "-"), normal),
        ])
    if len(daily_rows) == 1:
        daily_rows.append(["Nenhum registro", "-", "-", "-", "-", "-", "-", "-"])
    story += [_table(daily_rows, [20*mm, 30*mm, 20*mm, 30*mm, 30*mm, 28*mm, 28*mm, 60*mm], font_size=7)]

    story += [PageBreak(), Paragraph("Detalhamento das despesas", heading)]
    expense_rows = [["Data", "Categoria", "Descrição", "Valor"]]
    for record in records:
        for expense in record.expenses:
            expense_rows.append([
                _date(record.date), expense.category.name,
                Paragraph(escape(expense.description), normal), _money(expense.amount),
            ])
    if len(expense_rows) == 1:
        expense_rows.append(["-", "-", "Nenhuma despesa no período", _money(0)])
    story += [_table(expense_rows, [35*mm, 65*mm, 120*mm, 35*mm], font_size=8)]

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    stream.seek(0)
    return stream
