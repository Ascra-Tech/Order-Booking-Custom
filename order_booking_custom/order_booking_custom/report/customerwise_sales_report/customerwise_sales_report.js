// Copyright (c) 2024, Satya and contributors
// For license information, please see license.txt

frappe.query_reports["CUSTOMERWISE SALES REPORT"] = {
    "filters": [
        {
            "fieldname": "location",
            "label": __("Location"),
            "fieldtype": "Link",
            "options": "Branch",
        },
        {
            "fieldname": "sales_person",
            "label": __("Sales Person"),
            "fieldtype": "Link",
            "options": "Sales Person",
        },
        {
            "fieldname": "party_name",
            "label": __("Party Name"),
            "fieldtype": "Link",
            "options": "Customer",
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.nowdate(), -30)
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.nowdate()
        }
    ]
};
