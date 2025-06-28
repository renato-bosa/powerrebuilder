#!/usr/bin/env python3
"""Demo script for end-to-end PowerBuilder to Flutter conversion."""

import sys
from datetime import datetime
from pathlib import Path

from common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.logging_config import configure_pipeline_logging
from common.pipeline.pipeline_coordinator import PipelineCoordinator


def create_sample_app(demo_dir: Path) -> Path:








    """Create a sample PowerBuilder application."""
    app_dir = demo_dir / "sample_pb_app"
    app_dir.mkdir(parents=True, exist_ok=True)

    print("Creating sample PowerBuilder application...")

    # Create main window
    (app_dir / "w_employee_manager.srw").write_text('''
forward
global type w_employee_manager from window
end type
type cb_add from commandbutton within w_employee_manager
end type
type cb_delete from commandbutton within w_employee_manager
end type
type cb_save from commandbutton within w_employee_manager
end type
type dw_employee from datawindow within w_employee_manager
end type
end forward

global type w_employee_manager from window
integer width = 3000
integer height = 2000
boolean titlebar = true
string title = "Employee Manager"
boolean controlmenu = true
boolean minbox = true
boolean maxbox = true
boolean resizable = true
cb_add cb_add
cb_delete cb_delete
cb_save cb_save
dw_employee dw_employee
end type

type cb_add from commandbutton within w_employee_manager
integer x = 100
integer y = 1700
integer width = 400
integer height = 100
string text = "Add"
end type

event cb_add::clicked()
    long ll_row
    ll_row = dw_employee.InsertRow(0)
    dw_employee.ScrollToRow(ll_row)
    dw_employee.SetFocus()
end event

type cb_delete from commandbutton within w_employee_manager
integer x = 600
integer y = 1700
integer width = 400
integer height = 100
string text = "Delete"
end type

event cb_delete::clicked()
    long ll_row
    ll_row = dw_employee.GetRow()
    if ll_row > 0 then
        dw_employee.DeleteRow(ll_row)
    end if
end event

type cb_save from commandbutton within w_employee_manager
integer x = 1100
integer y = 1700
integer width = 400
integer height = 100
string text = "Save"
end type

event cb_save::clicked()
    if dw_employee.Update() = 1 then
        Commit;
        MessageBox("Success", "Data saved successfully")
    else
        Rollback;
        MessageBox("Error", "Failed to save data")
    end if
end event

type dw_employee from datawindow within w_employee_manager
integer x = 100
integer y = 100
integer width = 2800
integer height = 1500
string title = "none"
string dataobject = "d_employee"
boolean hscrollbar = true
boolean vscrollbar = true
boolean livescroll = true
borderstyle borderstyle = stylelowered!
end type

on w_employee_manager.create
this.cb_add=create cb_add
this.cb_delete=create cb_delete
this.cb_save=create cb_save
this.dw_employee=create dw_employee
this.Control[]={this.cb_add,this.cb_delete,this.cb_save,this.dw_employee}
end on

on w_employee_manager.destroy
destroy(this.cb_add)
destroy(this.cb_delete)
destroy(this.cb_save)
destroy(this.dw_employee)
end on

event open()
    // Connect to database
    dw_employee.SetTransObject(SQLCA)
    dw_employee.Retrieve()
end event
''')

    # Create DataWindow
    (app_dir / "d_employee.srd").write_text('''
release 12.5;
datawindow(units=0 timer_interval=0 color=1073741824 processing=1 print.preview=no)
header(height=72 color="536870912")
summary(height=0 color="536870912")
footer(height=0 color="536870912")
detail(height=84 color="536870912")
table(column=(type=number updatewhereclause=yes key=yes name=emp_id dbname="employee.emp_id" )
     column=(type=char(50) updatewhereclause=yes name=first_name dbname="employee.first_name" )
     column=(type=char(50) updatewhereclause=yes name=last_name dbname="employee.last_name" )
     column=(type=char(100) updatewhereclause=yes name=email dbname="employee.email" )
     column=(type=char(20) updatewhereclause=yes name=phone dbname="employee.phone" )
     column=(type=date updatewhereclause=yes name=hire_date dbname="employee.hire_date" )
     column=(type=decimal(2) updatewhereclause=yes name=salary dbname="employee.salary" )
     retrieve="SELECT emp_id, first_name, last_name, email, phone, hire_date, salary FROM employee ORDER BY last_name, first_name" 
     update="employee" updatewhere=1 updatekeyinplace=no )
text(band=header alignment="2" text="ID" border="0" color="33554432" x="9" y="8" height="56" width="178")
text(band=header alignment="2" text="First Name" border="0" color="33554432" x="197" y="8" height="56" width="379")
text(band=header alignment="2" text="Last Name" border="0" color="33554432" x="585" y="8" height="56" width="379")
text(band=header alignment="2" text="Email" border="0" color="33554432" x="974" y="8" height="56" width="663")
text(band=header alignment="2" text="Phone" border="0" color="33554432" x="1646" y="8" height="56" width="379")
text(band=header alignment="2" text="Hire Date" border="0" color="33554432" x="2034" y="8" height="56" width="320")
text(band=header alignment="2" text="Salary" border="0" color="33554432" x="2363" y="8" height="56" width="347")
column(band=detail id=1 alignment="1" tabsequence=10 border="0" color="33554432" x="9" y="8" height="68" width="178" format="[general]" name=emp_id edit.limit=0 edit.case=any edit.focusrectangle=no edit.autoselect=yes edit.autohscroll=yes)
column(band=detail id=2 alignment="0" tabsequence=20 border="0" color="33554432" x="197" y="8" height="68" width="379" format="[general]" name=first_name edit.limit=50 edit.case=any edit.focusrectangle=no edit.autoselect=yes edit.autohscroll=yes)
column(band=detail id=3 alignment="0" tabsequence=30 border="0" color="33554432" x="585" y="8" height="68" width="379" format="[general]" name=last_name edit.limit=50 edit.case=any edit.focusrectangle=no edit.autoselect=yes edit.autohscroll=yes)
column(band=detail id=4 alignment="0" tabsequence=40 border="0" color="33554432" x="974" y="8" height="68" width="663" format="[general]" name=email edit.limit=100 edit.case=any edit.focusrectangle=no edit.autoselect=yes edit.autohscroll=yes)
column(band=detail id=5 alignment="0" tabsequence=50 border="0" color="33554432" x="1646" y="8" height="68" width="379" format="[general]" name=phone edit.limit=20 edit.case=any edit.focusrectangle=no edit.autoselect=yes edit.autohscroll=yes)
column(band=detail id=6 alignment="0" tabsequence=60 border="0" color="33554432" x="2034" y="8" height="68" width="320" format="mm/dd/yyyy" name=hire_date edit.limit=0 edit.case=any edit.focusrectangle=no edit.autoselect=yes edit.autohscroll=yes)
column(band=detail id=7 alignment="1" tabsequence=70 border="0" color="33554432" x="2363" y="8" height="68" width="347" format="$#,##0.00" name=salary edit.limit=0 edit.case=any edit.focusrectangle=no edit.autoselect=yes edit.autohscroll=yes)
''')

    # Create business logic
    (app_dir / "n_employee_service.sru").write_text('''
forward
global type n_employee_service from nonvisualobject
end type
end forward

global type n_employee_service from nonvisualobject
end type
global n_employee_service n_employee_service

public function boolean validate_employee(string as_first_name, string as_last_name, string as_email)
    // Validate employee data
    if IsNull(as_first_name) or Trim(as_first_name) = "" then
        MessageBox("Validation Error", "First name is required")
        return false
    end if

    if IsNull(as_last_name) or Trim(as_last_name) = "" then
        MessageBox("Validation Error", "Last name is required")
        return false
    end if

    if IsNull(as_email) or Trim(as_email) = "" then
        MessageBox("Validation Error", "Email is required")
        return false
    end if

    // Simple email validation
    if Pos(as_email, "@") = 0 or Pos(as_email, ".") = 0 then
        MessageBox("Validation Error", "Invalid email format")
        return false
    end if

    return true
end function

public function decimal calculate_annual_bonus(decimal ad_salary, date ad_hire_date)
    decimal ld_bonus
    integer li_years_employed

    // Calculate years employed
    li_years_employed = Year(Today()) - Year(ad_hire_date)

    // Calculate bonus based on tenure
    if li_years_employed >= 10 then
        ld_bonus = ad_salary * 0.15
    elseif li_years_employed >= 5 then
        ld_bonus = ad_salary * 0.10
    elseif li_years_employed >= 2 then
        ld_bonus = ad_salary * 0.05
    else
        ld_bonus = 0
    end if

    return ld_bonus
end function
''')

    print(f"Sample app created at: {app_dir}")
    return app_dir


def run_conversion(app_dir: Path, output_dir: Path) -> dict:








    """Run the conversion pipeline."""
    print("\nStarting PowerBuilder to Flutter conversion...")
    print("=" * 60)

    # Configure logging
    configure_pipeline_logging(verbose=True)

    # Create pipeline
    pipeline = PipelineCoordinator(
        input_dir=str(app_dir),
        output_dir=str(output_dir),
    )

    # Run conversion
    start_time = datetime.now()
    result = pipeline.process_directory(str(app_dir))
    end_time = datetime.now()

    duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 60)
    print(f"Conversion completed in {duration:.2f} seconds")

    return result


def display_results(result: dict, output_dir: Path) -> None:







    """Display conversion results."""
    print("\nConversion Results:")
    print("-" * 40)

    # Check status
    if result.get("status") == "success":
        print("✓ Conversion successful!")
    else:
        print("⚠ Conversion completed with issues")

    # Display statistics
    stats = result.get("statistics", {})
    print(f"\nFiles processed: {stats.get("total_files", 0)}")
    print(f"Successful: {stats.get("successful", 0)}")
    print(f"Failed: {stats.get("failed", 0)}")

    # List generated files
    print("\nGenerated Flutter files:")
    flutter_files = list(output_dir.rglob("*.dart"))
    for file in flutter_files[:10]:  # Show first 10
        print(f"  - {file.relative_to(output_dir)}")

    if len(flutter_files) > 10:
        print(f"  ... and {len(flutter_files) - 10} more files")

    print(f"\nTotal Flutter files generated: {len(flutter_files)}")

    # Show sample generated code
    if flutter_files:
        sample_file = flutter_files[0]
        print(f"\nSample generated code ({sample_file.name}):")
        print("-" * 40)
        content = sample_file.read_text()
        print(content[:500] + "..." if len(content) > 500 else content)


def main() -> None:







    """Main demo function."""
    print("SIME Finch - PowerBuilder to Flutter Conversion Demo")
    print("=" * 60)

    # Setup demo directory
    demo_dir = Path("demo_output")
    demo_dir.mkdir(exist_ok=True)

    # Create sample app
    app_dir = create_sample_app(demo_dir)

    # Setup output directory
    output_dir = demo_dir / "flutter_app"
    output_dir.mkdir(exist_ok=True)

    # Run conversion
    result = run_conversion(app_dir, output_dir)

    # Display results
    display_results(result, output_dir)

    print("\n" + "=" * 60)
    print("Demo completed!")
    print(f"Sample PowerBuilder app: {app_dir}")
    print(f"Generated Flutter app: {output_dir}")
    print("\nNext steps:")
    print("1. cd", output_dir)
    print("2. flutter pub get")
    print("3. flutter run")


if __name__ == "__main__":
    main()
