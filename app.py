from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import os

app = Flask(__name__)

# ---------------- DATABASE ----------------

def get_db():
    return sqlite3.connect("database.db")

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_no TEXT,
        customer_name TEXT,
        place TEXT,
        phone TEXT,
        date TEXT,
        total REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bill_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_id INTEGER,
        description TEXT,
        net_weight REAL,
        touch REAL,
        wastage REAL,
        labour REAL,
        silver REAL,
        amount REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES ----------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bills')
def bills():
    conn = get_db()
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()
    cur.execute("SELECT * FROM bills ORDER BY id DESC")

    data = cur.fetchall()

    conn.close()

    return render_template('bills.html', bills=data)

# ---------------- SAVE BILL ----------------

@app.route('/save_bill', methods=['POST'])
def save_bill():

    data = request.json

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO bills (customer_name, place, phone, date, total)
    VALUES (?, ?, ?, ?, ?)
    """, (
        data['customer_name'],
        data['place'],
        data['phone'],
        data['date'],
        data['total']
    ))

    bill_id = cur.lastrowid
    bill_no = f"BILL-{bill_id:04d}"

    cur.execute(
        "UPDATE bills SET bill_no=? WHERE id=?",
        (bill_no, bill_id)
    )

    for item in data['items']:

        cur.execute("""
        INSERT INTO bill_items
        (bill_id, description, net_weight, touch,
         wastage, labour, silver, amount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bill_id,
            item['description'],
            item['net_weight'],
            item['touch'],
            item['wastage'],
            item['labour'],
            item['silver'],
            item['amount']
        ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "bill_no": bill_no
    })

# ---------------- PDF GENERATION ----------------

@app.route('/generate_pdf/<bill_no>')
def generate_pdf(bill_no):

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM bills WHERE bill_no=?",
        (bill_no,)
    )

    bill = cur.fetchone()

    if not bill:
        return "Bill not found", 404

    cur.execute(
        "SELECT * FROM bill_items WHERE bill_id=?",
        (bill['id'],)
    )

    items = cur.fetchall()

    conn.close()

    file_path = os.path.join("/tmp", f"{bill_no}.pdf")

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(f"<b>Invoice:</b> {bill_no}", styles['Title'])
    )

    elements.append(
        Spacer(1, 10)
    )

    elements.append(
        Paragraph(f"<b>Customer:</b> {bill['customer_name']}", styles['Normal'])
    )

    elements.append(
        Paragraph(f"<b>Place:</b> {bill['place']}", styles['Normal'])
    )

    elements.append(
        Paragraph(f"<b>Phone:</b> {bill['phone']}", styles['Normal'])
    )

    elements.append(
        Paragraph(f"<b>Date:</b> {bill['date']}", styles['Normal'])
    )

    elements.append(
        Spacer(1, 20)
    )

    table_data = [[
        "Description",
        "Net",
        "Touch",
        "Waste",
        "Labour",
        "Silver",
        "Amount"
    ]]

    for item in items:

        table_data.append([
            item['description'],
            item['net_weight'],
            item['touch'],
            item['wastage'],
            item['labour'],
            item['silver'],
            item['amount']
        ])

    table = Table(table_data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#007bff")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),

        ('GRID', (0,0), (-1,-1), 1, colors.black),

        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),

        ('ALIGN', (0,0), (-1,-1), 'CENTER'),

        ('BOTTOMPADDING', (0,0), (-1,0), 10),

        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
    ]))

    elements.append(table)

    elements.append(
        Spacer(1, 20)
    )

    elements.append(
        Paragraph(
            f"<b>Total Amount:</b> {bill['total']}",
            styles['Heading2']
        )
    )

    doc.build(elements)

    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"{bill_no}.pdf"
    )

# ---------------- RUN ----------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)