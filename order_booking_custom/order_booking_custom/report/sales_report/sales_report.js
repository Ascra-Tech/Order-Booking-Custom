// Copyright (c) 2024, satya and contributors
// For license information, please see license.txt
frappe.query_reports["Sales Report"] = {
    "filters": [
        {
            "fieldname": "location",
            "label": __("Location"),
            "fieldtype": "Link",
            "options": "Branch", // Replace with the actual Doctype for location
            "default": "",
            "reqd": 0
        },
        {
            "fieldname": "sales_person",
            "label": __("Sales Person"),
            "fieldtype": "Link",
            "options": "Sales Person",
            "default": "",
            "reqd": 0
        },
        {
            "fieldname": "date_range",
            "label": __("Date Range"),
            "fieldtype": "DateRange",
            "default": [
                frappe.datetime.add_days(frappe.datetime.nowdate(), -30),
                frappe.datetime.nowdate()
            ],
            "reqd": 0
        }
    ],

    // Customize how the report behaves after rendering
    "onload": function(report) {
        // Add custom behavior, e.g., default filters, banners, or messages
        frappe.msgprint(__("Welcome to the Total Sales Report!"));
    },

    // Customize result formatting
    "formatter": function(value, row, column, data, default_formatter) {
        // Format GRAND TOTAL row differently
        if (data && data.location === "GRAND TOTAL") {
            column.bold = true;
            column.align = "right";
        }
        return default_formatter(value, row, column, data);
    },

    // After report is rendered
    "after_render": function(report) {
        frappe.show_alert({
            message: __("Report Loaded Successfully"),
            indicator: "green"
        });
    }
};
