# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import sqlite3
from CheckmarxPythonSDK.CxPortalSoapApiSDK import get_pivot_data
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name

db = sqlite3.connect(":memory:")
db.execute("""CREATE TABLE IF NOT EXISTS results (TEAM_NAME VARCHAR, PROJECT_NAME VARCHAR, QUERY_NAME VARCHAR, 
RESULT_SEVERITY INTEGER, RESULT_QUANTITY INTEGER, PRIMARY KEY (TEAM_NAME, PROJECT_NAME, QUERY_NAME) )""")


def get_data_by_api_and_write_to_db():
    # Get Past Month pivot data
    pivot_data = get_pivot_data(
        pivot_view_client_type="LastMonthProjectScans", include_not_exploitable=True, range_type="PAST_MONTH",
        date_from="2023-06-01-0-0-0", date_to="2023-06-30-0-0-0"
    )

    for row in pivot_data.PivotTable.Rows.CxPivotRow:
        value = row["Data"]["anyType"]
        team_name = value[0]
        project_name = value[1]
        query_name = value[2]
        if query_name == "No Results":
            continue
        scan_date = value[4]
        scan_time = value[5]
        result_severity = value[3]
        result_quantity = value[6]
        with db:
            db.execute("""INSERT INTO results (TEAM_NAME, PROJECT_NAME, QUERY_NAME, RESULT_SEVERITY, RESULT_QUANTITY) 
            VALUES (?,?,?,?,?) ON CONFLICT (TEAM_NAME, PROJECT_NAME, QUERY_NAME) DO UPDATE SET RESULT_QUANTITY = ?""",
                       (team_name, project_name, query_name, result_severity, result_quantity, result_quantity))


def create_xlsx_file():
    """
    create xlsx file based on the data, and following the same layout as the data analysis template.
    :return:
    """
    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook('Pivot.xlsx')
    worksheet = workbook.add_worksheet()
    worksheet.set_default_row(20)

    title_format = workbook.add_format({'align': 'left', 'locked': True, 'text_wrap': True, 'border': 1, 'bg_color': '#F0F0F0',
                                        'border_color': '#A0A0A0'})
    worksheet.merge_range('A1:A2', '')

    high_severity = "3"
    medium_severity = "2"
    low_severity = "1"
    info_severity = "0"
    sql_count = "SELECT COUNT(DISTINCT QUERY_NAME) FROM results WHERE RESULT_SEVERITY = {severity}"
    sql_query = "SELECT DISTINCT QUERY_NAME FROM results WHERE RESULT_SEVERITY = {severity} ORDER BY QUERY_NAME ASC"
    query_dict = {}
    with db:
        number_of_high = db.execute(sql_count.format(severity=high_severity)).fetchone()[0]
        number_of_medium = db.execute(sql_count.format(severity=medium_severity)).fetchone()[0]
        number_of_low = db.execute(sql_count.format(severity=low_severity)).fetchone()[0]
        number_of_info = db.execute(sql_count.format(severity=info_severity)).fetchone()[0]

        high_column_index_start = 1
        high_column_index_end = number_of_high
        high_total_column_index = high_column_index_end + 1
        worksheet.merge_range(0, high_column_index_start, 0, high_column_index_end, 'High', title_format)
        worksheet.merge_range(0, high_total_column_index, 1, high_total_column_index, 'High Total', title_format)
        current_high_column_index = high_column_index_start
        for row in db.execute(sql_query.format(severity=high_severity)):
            worksheet.write(1, current_high_column_index, row[0], title_format)
            query_dict.update({row[0]: current_high_column_index})
            current_high_column_index += 1

        medium_column_index_start = high_total_column_index + 1
        medium_column_index_end = medium_column_index_start + number_of_medium - 1
        medium_total_column_index = medium_column_index_end + 1
        worksheet.merge_range(0, medium_column_index_start, 0, medium_column_index_end, 'Medium', title_format)
        worksheet.merge_range(0, medium_total_column_index, 1, medium_total_column_index, 'Medium Total', title_format)
        current_medium_column_index = medium_column_index_start
        for row in db.execute(sql_query.format(severity=medium_severity)):
            worksheet.write(1, current_medium_column_index, row[0], title_format)
            query_dict.update({row[0]: current_medium_column_index})
            current_medium_column_index += 1

        low_column_index_start = medium_total_column_index + 1
        low_column_index_end = low_column_index_start + number_of_low - 1
        low_total_column_index = low_column_index_end + 1
        worksheet.merge_range(0, low_column_index_start, 0, low_column_index_end, 'Low', title_format)
        worksheet.merge_range(0, low_total_column_index, 1, low_total_column_index, 'Low Total', title_format)
        current_low_column_index = low_column_index_start
        for row in db.execute(sql_query.format(severity=low_severity)):
            worksheet.write(1, current_low_column_index, row[0], title_format)
            query_dict.update({row[0]: current_low_column_index})
            current_low_column_index += 1

        info_column_index_start = low_total_column_index + 1
        info_column_index_end = info_column_index_start + number_of_info - 1
        info_total_column_index = info_column_index_end + 1
        worksheet.merge_range(0, info_column_index_start, 0, info_column_index_end, 'Info', title_format)
        worksheet.merge_range(0, info_total_column_index, 1, info_total_column_index, 'Info Total', title_format)
        current_info_column_index = info_column_index_start
        for row in db.execute(sql_query.format(severity=info_severity)):
            worksheet.write(1, current_info_column_index, row[0], title_format)
            query_dict.update({row[0]: current_info_column_index})
            current_info_column_index += 1

        row_index = 1
        team_project = None
        for row in db.execute(
            """SELECT TEAM_NAME, PROJECT_NAME, QUERY_NAME, RESULT_SEVERITY, RESULT_QUANTITY FROM results ORDER BY 
            TEAM_NAME ASC, PROJECT_NAME ASC, RESULT_SEVERITY DESC, QUERY_NAME ASC"""
        ):
            team_name = row[0]
            project_name = row[1]
            query_name = row[2]
            result_severity = row[3]
            result_quantity = int(row[4])
            current_team_project = team_name + "_" + project_name
            if team_project != current_team_project:
                row_index += 1
                team_project = current_team_project
                worksheet.write(row_index, 0, project_name, title_format)
                row_for_total = row_index + 1
                # high_total
                high_column_start_letter = xl_col_to_name(high_column_index_start)
                high_column_end_letter = xl_col_to_name(high_column_index_end)
                func_high = f"=SUM({high_column_start_letter}{row_for_total}:{high_column_end_letter}{row_for_total})"
                worksheet.write_formula(row_index, high_total_column_index, func_high)
                # medium total
                medium_column_start_letter = xl_col_to_name(medium_column_index_start)
                medium_column_end_letter = xl_col_to_name(medium_column_index_end)
                func_medium = f"=SUM({medium_column_start_letter}{row_for_total}:{medium_column_end_letter}{row_for_total})"
                worksheet.write_formula(row_index, medium_total_column_index, func_medium)
                # low total
                low_column_start_letter = xl_col_to_name(low_column_index_start)
                low_column_end_letter = xl_col_to_name(low_column_index_end)
                func_low = f"=SUM({low_column_start_letter}{row_for_total}:{low_column_end_letter}{row_for_total})"
                worksheet.write_formula(row_index, low_total_column_index, func_low)
                # info total
                info_column_start_letter = xl_col_to_name(info_column_index_start)
                info_column_end_letter = xl_col_to_name(info_column_index_end)
                func_info = f"=SUM({info_column_start_letter}{row_for_total}:{info_column_end_letter}{row_for_total})"
                worksheet.write_formula(row_index, info_total_column_index, func_info)

            worksheet.write_number(row_index, query_dict.get(query_name), result_quantity)
    worksheet.autofit()
    workbook.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    get_data_by_api_and_write_to_db()
    create_xlsx_file()