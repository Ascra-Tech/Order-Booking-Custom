// Copyright (c) 2024, satya and contributors
// For license information, please see license.txt

frappe.query_reports["Location Wise Sales Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "salesperson",
            label: __("Sales Person"),
            fieldtype: "Link",
            options: "Sales Person",
            reqd: 0
        },
        {
            fieldname: "dealer_name",
            label: __("Dealer Name"),
            fieldtype: "Data",
            reqd: 0
        },
        {
            fieldname: "segment",
            label: __("Segment"),
            fieldtype: "Link",
            options: "Item Group",
            reqd: 0
        }
    ],
    get_datatable_options(options) {
        return Object.assign(options, {
            checkboxColumn: true,
            events: {
                onCheckRow: function (data) {
                    if (!data) return;
                    const row_name = data[2].content; // Dealer Name or Row Name
                    const raw_data = frappe.query_report.chart.data;
                    const new_datasets = raw_data.datasets;
                    const element_found = new_datasets.some((element, index, array) => {
                        if (element.name == row_name) {
                            array.splice(index, 1); // Remove if already exists
                            return true;
                        }
                        return false;
                    });

                    // Check the correct index based on tree_type or report filters
                    const slice_at = 3; // Customize if needed based on filters

                    // If the row is not already found, add it to the chart data
                    if (!element_found) {
                        new_datasets.push({
                            name: row_name,
                            values: data.slice(slice_at, data.length - 1).map((column) => column.content),
                        });
                    }

                    // Create new chart data
                    const new_data = {
                        labels: raw_data.labels, // X-axis labels (Dealer Names)
                        datasets: new_datasets, // Updated datasets
                    };

                    // Define the chart options
                    const new_options = Object.assign({}, frappe.query_report.chart_options, {
                        data: new_data,
                    });

                    // Render the updated chart
                    frappe.query_report.render_chart(new_options);

                    // Store the updated chart data
                    frappe.query_report.raw_chart_data = new_data;
                },
            },
        });
    },

    // When the report is loaded, generate the chart data with Dealer Name as X-axis and Invoice Amount as Y-axis
    onload: function (report) {
        const data = report.data || [];
        const labels = data.map(row => row.dealer_name); // Dealer names for X-axis
        const invoice_amounts = data.map(row => row.inv_amount); // Invoice amounts for Y-axis

        // Chart data structure
        const chart_data = {
            labels: labels,
            datasets: [{
                name: __("Invoice Amount"),
                values: invoice_amounts, // Values to plot on the Y-axis
            }],
        };

        // Chart options (e.g., axis titles)
        const chart_options = {
            type: "bar", // Bar chart
            axisOptions: {
                xAxis: {
                    title: __("Dealer Name"),
                },
                yAxis: {
                    title: __("Invoice Amount"),
                    isNumeric: true, // Ensure the Y-axis is numeric
                },
            },
        };

        // Assign chart data and options to the report's chart
        report.chart.update({
            data: chart_data,
            options: chart_options,
        });
    },
};
