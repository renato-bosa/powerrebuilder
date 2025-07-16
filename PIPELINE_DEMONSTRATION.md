# PowerBuilder to Modern Code: Complete Pipeline Demonstration

This document demonstrates the complete transformation pipeline from a PowerBuilder PBD file to modern Flutter/Python code.

## Overview

The PowerRebuilder pipeline consists of 5 stages that transform legacy PowerBuilder applications into modern code:

1. **Extract** - Extracts P-code (.fun files) from PBD/PBL files
2. **Decompile** - Converts P-code to PowerBuilder source (.sru files)
3. **Parse** - Converts PowerBuilder source to Abstract Syntax Tree (AST)
4. **Model** - Builds semantic models from AST
5. **Generate** - Produces modern Flutter/Python code from models

## Setup

First, ensure you have the project installed:

```bash
# Install dependencies with uv
uv pip install -e .

# Verify the CLI works
python main.py --help
```

## Stage 1: Extract - PBD to P-code

The first stage extracts the compiled P-code from PowerBuilder PBD files.

### Command:
```bash
python main.py extract data/dcm_email.pbd data/pipeline_demo/1_extracted
```

### What happens:
- Reads the PBD file header and structure
- Extracts individual objects (windows, functions, classes)
- Saves each object as a .fun file containing P-code

### Sample output structure:
```
data/pipeline_demo/1_extracted/
├── n_cst_email.fun         # Email service class
├── n_cst_mailsession.fun   # Mail session handler
├── n_cst_pdfwriter.fun     # PDF generation class
├── w_mail_test.fun         # Test window
└── extraction_log.json     # Extraction metadata
```

### Sample P-code content (n_cst_email.fun):
```
HEADER:
  Version: 0600
  Object: n_cst_email
  Type: UserObject
  
BYTECODE:
  0000: 0x4C 0x01 0x00 0x00  // Load constant
  0004: 0x4D 0x02 0x00 0x00  // Load variable
  0008: 0x20 0x00 0x00 0x00  // Call function
  ...
```

## Stage 2: Decompile - P-code to PowerBuilder Source

The decompiler converts the binary P-code back into readable PowerBuilder source code.

### Command:
```bash
python main.py decompile data/pipeline_demo/1_extracted data/pipeline_demo/2_decompiled
```

### What happens:
- Decodes P-code instructions
- Reconstructs control flow (if/else, loops)
- Rebuilds expressions and function calls
- Generates PowerBuilder source syntax

### Sample output (n_cst_email.sru):
```powerbuilder
forward
global type n_cst_email from nonvisualobject
end type
end forward

global type n_cst_email from nonvisualobject
end type
global n_cst_email n_cst_email

type variables
private:
    string is_smtp_server
    integer ii_smtp_port = 25
    string is_from_address
    string is_to_address[]
    string is_cc_address[]
    string is_subject
    string is_body
    boolean ib_html_format = false
end variables

forward prototypes
public function integer of_send_email()
public function integer of_set_smtp_server(string as_server, integer ai_port)
public function integer of_add_recipient(string as_email)
public function integer of_set_message(string as_subject, string as_body)
end prototypes

public function integer of_send_email();
    // Send email using SMTP
    integer li_return
    n_cst_mailsession lnv_session
    
    if isnull(is_smtp_server) or trim(is_smtp_server) = "" then
        messagebox("Error", "SMTP server not configured")
        return -1
    end if
    
    lnv_session = create n_cst_mailsession
    li_return = lnv_session.of_connect(is_smtp_server, ii_smtp_port)
    
    if li_return < 0 then
        messagebox("Error", "Failed to connect to SMTP server")
        destroy lnv_session
        return -1
    end if
    
    // Set email properties
    lnv_session.of_set_from(is_from_address)
    lnv_session.of_set_subject(is_subject)
    lnv_session.of_set_body(is_body, ib_html_format)
    
    // Add recipients
    integer li_idx
    for li_idx = 1 to upperbound(is_to_address)
        lnv_session.of_add_to(is_to_address[li_idx])
    next
    
    // Send the email
    li_return = lnv_session.of_send()
    
    destroy lnv_session
    return li_return
end function
```

## Stage 3: Parse - PowerBuilder Source to AST

The parser converts PowerBuilder source code into a structured Abstract Syntax Tree.

### Command:
```bash
python main.py parse data/pipeline_demo/2_decompiled data/pipeline_demo/3_parsed
```

### What happens:
- Lexical analysis (tokenization)
- Syntax parsing using Lark grammar
- AST construction
- Type resolution

### Sample AST output (n_cst_email.ast.json):
```json
{
  "node_type": "PBClass",
  "name": "n_cst_email",
  "base_class": "nonvisualobject",
  "is_global": true,
  "variables": [
    {
      "node_type": "PBVariable",
      "name": "is_smtp_server",
      "type": "string",
      "access": "private"
    },
    {
      "node_type": "PBVariable",
      "name": "ii_smtp_port",
      "type": "integer",
      "access": "private",
      "initial_value": {
        "node_type": "PBLiteral",
        "value": 25,
        "type": "integer"
      }
    }
  ],
  "methods": [
    {
      "node_type": "PBFunction",
      "name": "of_send_email",
      "return_type": "integer",
      "access": "public",
      "parameters": [],
      "body": {
        "node_type": "PBBlock",
        "statements": [
          {
            "node_type": "PBVariableDeclaration",
            "variable": "li_return",
            "type": "integer"
          },
          {
            "node_type": "PBIfStatement",
            "condition": {
              "node_type": "PBBinaryOp",
              "operator": "or",
              "left": {
                "node_type": "PBFunctionCall",
                "name": "isnull",
                "arguments": [{"node_type": "PBIdentifier", "name": "is_smtp_server"}]
              },
              "right": {
                "node_type": "PBBinaryOp",
                "operator": "=",
                "left": {
                  "node_type": "PBFunctionCall",
                  "name": "trim",
                  "arguments": [{"node_type": "PBIdentifier", "name": "is_smtp_server"}]
                },
                "right": {"node_type": "PBLiteral", "value": "", "type": "string"}
              }
            },
            "then_block": {
              "node_type": "PBBlock",
              "statements": [
                {
                  "node_type": "PBFunctionCall",
                  "name": "messagebox",
                  "arguments": [
                    {"node_type": "PBLiteral", "value": "Error", "type": "string"},
                    {"node_type": "PBLiteral", "value": "SMTP server not configured", "type": "string"}
                  ]
                },
                {
                  "node_type": "PBReturn",
                  "value": {"node_type": "PBLiteral", "value": -1, "type": "integer"}
                }
              ]
            }
          }
        ]
      }
    }
  ]
}
```

## Stage 4: Model - AST to Semantic Model

The model stage builds high-level semantic models from the AST, resolving references and building relationships.

### Command:
```bash
python main.py model data/pipeline_demo/3_parsed data/pipeline_demo/4_model
```

### What happens:
- Resolves type references
- Builds class hierarchies
- Maps event handlers
- Identifies business logic patterns

### Sample model output (n_cst_email.model.json):
```json
{
  "type": "ServiceClass",
  "name": "EmailService",
  "original_name": "n_cst_email",
  "purpose": "Email sending functionality",
  "dependencies": [
    {
      "type": "ServiceClass",
      "name": "MailSessionService",
      "original_name": "n_cst_mailsession"
    }
  ],
  "properties": [
    {
      "name": "smtpServer",
      "type": "string",
      "visibility": "private",
      "description": "SMTP server hostname"
    },
    {
      "name": "smtpPort",
      "type": "int",
      "visibility": "private",
      "default": 25,
      "description": "SMTP server port"
    },
    {
      "name": "recipients",
      "type": "List<string>",
      "visibility": "private",
      "description": "Email recipient addresses"
    }
  ],
  "methods": [
    {
      "name": "sendEmail",
      "returns": "Future<bool>",
      "async": true,
      "parameters": [],
      "business_logic": {
        "validation": ["Check SMTP server configured"],
        "operations": [
          "Connect to SMTP server",
          "Configure email properties",
          "Add recipients",
          "Send email"
        ],
        "error_handling": ["Connection failure", "Send failure"]
      }
    }
  ]
}
```

## Stage 5: Generate - Model to Modern Code

The final stage generates modern Flutter and Python code from the semantic models.

### Command:
```bash
python main.py generate data/pipeline_demo/4_model data/pipeline_demo/5_generated
```

### What happens:
- Applies code generation templates
- Maps PowerBuilder patterns to modern patterns
- Generates UI widgets (Flutter)
- Generates backend services (Python)

### Generated Flutter Code (email_service.dart):
```dart
import 'package:flutter/material.dart';
import 'package:mailer/mailer.dart';
import 'package:mailer/smtp_server.dart';

class EmailService extends ChangeNotifier {
  String? _smtpServer;
  int _smtpPort = 25;
  String? _fromAddress;
  final List<String> _recipients = [];
  final List<String> _ccRecipients = [];
  String? _subject;
  String? _body;
  bool _isHtmlFormat = false;

  // Configure SMTP server
  void setSmtpServer(String server, {int port = 25}) {
    _smtpServer = server;
    _smtpPort = port;
    notifyListeners();
  }

  // Add recipient
  void addRecipient(String email) {
    if (email.isNotEmpty && _isValidEmail(email)) {
      _recipients.add(email);
      notifyListeners();
    }
  }

  // Set message content
  void setMessage(String subject, String body, {bool isHtml = false}) {
    _subject = subject;
    _body = body;
    _isHtmlFormat = isHtml;
    notifyListeners();
  }

  // Send email
  Future<bool> sendEmail() async {
    // Validate configuration
    if (_smtpServer == null || _smtpServer!.isEmpty) {
      throw Exception('SMTP server not configured');
    }

    if (_recipients.isEmpty) {
      throw Exception('No recipients specified');
    }

    try {
      // Create SMTP server configuration
      final smtpServer = SmtpServer(
        _smtpServer!,
        port: _smtpPort,
        ignoreBadCertificate: true,
      );

      // Create message
      final message = Message()
        ..from = Address(_fromAddress ?? 'noreply@example.com')
        ..recipients.addAll(_recipients)
        ..ccRecipients.addAll(_ccRecipients)
        ..subject = _subject ?? 'No Subject'
        ..text = _isHtmlFormat ? null : _body
        ..html = _isHtmlFormat ? _body : null;

      // Send email
      final sendReport = await send(message, smtpServer);
      
      print('Email sent: ${sendReport.toString()}');
      return true;
    } catch (e) {
      print('Error sending email: $e');
      return false;
    }
  }

  bool _isValidEmail(String email) {
    return RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(email);
  }
}
```

### Generated Python Code (email_service.py):
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class EmailService:
    """Service for sending emails via SMTP"""
    
    smtp_server: Optional[str] = None
    smtp_port: int = 25
    from_address: Optional[str] = None
    recipients: List[str] = field(default_factory=list)
    cc_recipients: List[str] = field(default_factory=list)
    subject: Optional[str] = None
    body: Optional[str] = None
    is_html_format: bool = False
    
    def set_smtp_server(self, server: str, port: int = 25) -> None:
        """Configure SMTP server settings"""
        self.smtp_server = server
        self.smtp_port = port
        
    def add_recipient(self, email: str) -> None:
        """Add email recipient"""
        if email and self._is_valid_email(email):
            self.recipients.append(email)
            
    def add_cc_recipient(self, email: str) -> None:
        """Add CC recipient"""
        if email and self._is_valid_email(email):
            self.cc_recipients.append(email)
            
    def set_message(self, subject: str, body: str, is_html: bool = False) -> None:
        """Set email message content"""
        self.subject = subject
        self.body = body
        self.is_html_format = is_html
        
    def send_email(self) -> bool:
        """Send email using configured settings"""
        # Validate configuration
        if not self.smtp_server:
            raise ValueError("SMTP server not configured")
            
        if not self.recipients:
            raise ValueError("No recipients specified")
            
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self.subject or "No Subject"
            msg['From'] = self.from_address or "noreply@example.com"
            msg['To'] = ', '.join(self.recipients)
            
            if self.cc_recipients:
                msg['Cc'] = ', '.join(self.cc_recipients)
                
            # Add body
            mime_type = 'html' if self.is_html_format else 'plain'
            msg.attach(MIMEText(self.body or "", mime_type))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                # server.starttls()  # Enable for TLS
                # server.login(username, password)  # Add authentication if needed
                
                all_recipients = self.recipients + self.cc_recipients
                server.send_message(msg, to_addrs=all_recipients)
                
            logger.info(f"Email sent successfully to {len(all_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
            
    def _is_valid_email(self, email: str) -> bool:
        """Validate email address format"""
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))
```

## Running the Complete Pipeline

To run all stages at once:

```bash
# Run complete pipeline
python main.py all data/dcm_email.pbd data/pipeline_demo/output

# This runs all 5 stages sequentially:
# 1. Extract: PBD → P-code files
# 2. Decompile: P-code → PowerBuilder source
# 3. Parse: PowerBuilder source → AST
# 4. Model: AST → Semantic models
# 5. Generate: Models → Flutter/Python code
```

## Final Output Structure

```
data/pipeline_demo/output/
├── 1_extracted/
│   ├── n_cst_email.fun
│   ├── n_cst_mailsession.fun
│   ├── n_cst_pdfwriter.fun
│   └── w_mail_test.fun
├── 2_decompiled/
│   ├── n_cst_email.sru
│   ├── n_cst_mailsession.sru
│   ├── n_cst_pdfwriter.sru
│   └── w_mail_test.sru
├── 3_parsed/
│   ├── n_cst_email.ast.json
│   ├── n_cst_mailsession.ast.json
│   ├── n_cst_pdfwriter.ast.json
│   └── w_mail_test.ast.json
├── 4_model/
│   ├── n_cst_email.model.json
│   ├── n_cst_mailsession.model.json
│   ├── n_cst_pdfwriter.model.json
│   └── w_mail_test.model.json
└── 5_generated/
    ├── flutter/
    │   ├── lib/
    │   │   ├── services/
    │   │   │   ├── email_service.dart
    │   │   │   ├── mail_session_service.dart
    │   │   │   └── pdf_writer_service.dart
    │   │   └── screens/
    │   │       └── mail_test_screen.dart
    │   └── pubspec.yaml
    └── python/
        ├── services/
        │   ├── email_service.py
        │   ├── mail_session_service.py
        │   └── pdf_writer_service.py
        └── requirements.txt
```

## Key Transformation Highlights

### 1. Type System Evolution
- PowerBuilder: `string is_email[]` → Flutter: `List<String> emails`
- PowerBuilder: `integer` → Python: `int` with type hints

### 2. Error Handling
- PowerBuilder: Return codes (-1 for error)
- Modern: Exceptions and proper error types

### 3. Async Operations
- PowerBuilder: Synchronous blocking calls
- Modern: `async`/`await` patterns

### 4. UI Patterns
- PowerBuilder: DataWindow controls
- Flutter: Modern reactive widgets with providers

### 5. State Management
- PowerBuilder: Global variables and instance variables
- Flutter: Provider/ChangeNotifier pattern
- Python: Dataclasses with clear state

## Summary

The PowerRebuilder pipeline successfully transforms legacy PowerBuilder applications into modern, maintainable code. Each stage preserves the business logic while updating the implementation to use modern patterns, type safety, and best practices for the target platform.