import frappe

def execute(filters=None):
    columns, data = [], []

    # Get report columns
    columns = get_columns()

    # Fetch data from database
    report_data = get_report_data(filters)

    # Add 'Grand Total' row at the end
    if report_data:
        grand_total = calculate_grand_total(report_data)
        report_data.append(grand_total)

    # Return columns and data
    data = report_data
    return columns, data


def get_columns():
    """Defines report columns."""
    return [
        {"label": "Location", "fieldtype": "Data", "width": 150},
        {"label": "Actual Quantities", "fieldtype": "Float", "width": 150},
        {"label": "Unit Quantities", "fieldtype": "Float", "width": 150},
        {"label": "Rejects", "fieldtype": "Float", "width": 100},
        {"label": "INV Amounts", "fieldtype": "Currency", "width": 150},
        {"label": "Collection", "fieldtype": "Currency", "width": 150},
    ]


def get_report_data(filters):
    """Fetches report data from Sales Order tables."""
    conditions = "WHERE so.docstatus = 1"

    # Add filters if available
    if filters.get("location"):
        conditions += " AND soi.branch = %(location)s"
    if filters.get("sales_person"):
        conditions += " AND soi.sales_person = %(sales_person)s"

    query = """
        SELECT
            soi.branch AS location,
            SUM(soi.qty) AS actual_qty,
            SUM(CASE WHEN soi.custom_status != 'Cancelled' THEN soi.qty ELSE 0 END) AS unit_qty,
            SUM(CASE WHEN soi.custom_status = 'Cancelled' THEN soi.qty ELSE 0 END) AS rejects,
            SUM(soi.amount) AS inv_amount,
            SUM(soi.amount) AS collection
        FROM
            `tabSales Order` AS so
        JOIN
            `tabSales Order Item` AS soi ON so.name = soi.parent 
        {conditions}
        GROUP BY soi.branch
        ORDER BY soi.branch
    """.format(conditions=conditions)

    return frappe.db.sql(query, filters, as_dict=True)


def calculate_grand_total(data):
    """Calculates the grand total row."""
    grand_total = {
        "location": "GRAND TOTAL",
        "actual_qty": sum(row["actual_qty"] for row in data),
        "unit_qty": sum(row["unit_qty"] for row in data),
        "rejects": sum(row["rejects"] for row in data),
        "inv_amount": sum(row["inv_amount"] for row in data),
        "collection": sum(row["collection"] for row in data),
    }
    return grand_total
