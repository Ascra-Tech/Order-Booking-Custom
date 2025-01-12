

// Copyright (c) 2024, satya and contributors
// For license information, please see license.txt

frappe.query_reports["Location Wise Sales Report"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "salesperson",
            "label": __("Salesperson"),
            "fieldtype": "Link",
            "options": "Sales Person",
            "reqd": 0
        },
        {
            "fieldname": "dealer_name",
            "label": __("Dealer Name"),
            "fieldtype": "Data",
            "reqd": 0
        },
        {
            "fieldname": "segment",
            "label": __("Segment"),
            "fieldtype": "Link",
            "options": "Item Group",
            "reqd": 0
        }
    ]
};
