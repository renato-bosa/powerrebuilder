$PBExportHeader$w_main.srw
forward
global type w_main from window
end type
type cb_ok from commandbutton within w_main
end type
type sle_name from singlelineedit within w_main
end type
end forward

global type w_main from window
integer width = 1920
integer height = 1200
boolean titlebar = true
string title = "Sample Application"
boolean controlmenu = true
boolean minbox = true
boolean maxbox = true
boolean resizable = true
long backcolor = 67108864
string icon = "AppIcon!"
boolean center = true
cb_ok cb_ok
sle_name sle_name
end type
global w_main w_main

type cb_ok from commandbutton within w_main
integer x = 320
integer y = 600
integer width = 375
integer height = 100
integer taborder = 20
boolean bringtotop = true
integer textsize = -10
integer weight = 400
string facename = "Arial"
string text = "OK"
end type

event clicked;
string ls_name
ls_name = sle_name.text
if ls_name = "" then
    MessageBox("Error", "Please enter a name")
    return
end if
MessageBox("Hello", "Hello " + ls_name + "!")
close(parent)
end event

type sle_name from singlelineedit within w_main
integer x = 320
integer y = 400
integer width = 800
integer height = 100
integer taborder = 10
boolean bringtotop = true
integer textsize = -10
integer weight = 400
string facename = "Arial"
long textcolor = 33554432
string text = "Enter your name"
boolean autohscroll = true
end type