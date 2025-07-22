#!/usr/bin/env python3
"""
PowerBuilder Pipeline CLI Demonstration

This script shows the exact commands and transformations at each stage.
"""



def print_section(title, content):
    """Print a formatted section"""


def show_transformation(stage, before, after):
    """Show before/after transformation"""


def main():

    # Overview
    print_section(
        "PIPELINE OVERVIEW",
        """
The PowerRebuilder pipeline transforms legacy PowerBuilder applications through 5 stages:

1. EXTRACT   : PBD/PBL → P-code files (.fun)
2. DECOMPILE : P-code → PowerBuilder source (.sru)
3. PARSE     : PowerBuilder source → AST (JSON)
4. MODEL     : AST → Semantic models
5. GENERATE  : Models → Flutter/Python code

Let's walk through each stage with real examples!
""",
    )

    # Stage 1: Extract
    print_section(
        "STAGE 1: EXTRACT",
        """
Command: python main.py extract input.pbd output/1_extracted

This extracts compiled P-code from PowerBuilder Dynamic libraries (PBD files).
PBD files contain compiled PowerBuilder objects like windows, user objects, etc.
""",
    )

    show_transformation(
        "Extract Stage",
        """Binary PBD file structure:
HEADER: PBD0600
OBJECTS:
  - n_cst_email (UserObject, 2048 bytes)
  - w_mail_test (Window, 4096 bytes)
  - n_cst_mailsession (UserObject, 1536 bytes)""",
        """Extracted P-code files:
output/1_extracted/
├── n_cst_email.fun      # Email service P-code
├── w_mail_test.fun      # Test window P-code
└── n_cst_mailsession.fun # Mail session P-code

Sample n_cst_email.fun (hex view):
0000: 4C 01 00 00 4D 02 00 00  # Load constants
0008: 20 00 00 00 53 74 72 69  # "String" type
0010: 6E 67 00 00 69 73 5F 73  # "is_smtp_server"
...""",
    )

    # Stage 2: Decompile
    print_section(
        "STAGE 2: DECOMPILE",
        """
Command: python main.py decompile output/1_extracted output/2_decompiled

Converts binary P-code back into readable PowerBuilder source code.
The decompiler analyzes opcodes, reconstructs control flow, and generates source.
""",
    )

    show_transformation(
        "Decompile Stage",
        """P-code opcodes:
4C 01 00 00  # LOAD_CONST 1
4D 02 00 00  # LOAD_VAR 2
20 00 00 00  # CALL_FUNC 0
15 00 00 00  # JUMP_IF_FALSE 0
...""",
        """PowerBuilder source (n_cst_email.sru):
forward
global type n_cst_email from nonvisualobject
end type
end forward

global type n_cst_email from nonvisualobject
end type

type variables
private:
    string is_smtp_server
    integer ii_smtp_port = 25
    string is_to_address[]
end variables

public function integer of_send_email();
    integer li_return
    n_cst_mailsession lnv_session

    if isnull(is_smtp_server) then
        messagebox("Error", "SMTP server not configured")
        return -1
    end if

    lnv_session = create n_cst_mailsession
    li_return = lnv_session.of_send()
    destroy lnv_session

    return li_return
end function""",
    )

    # Stage 3: Parse
    print_section(
        "STAGE 3: PARSE",
        """
Command: python main.py parse output/2_decompiled output/3_parsed

Parses PowerBuilder source code into an Abstract Syntax Tree (AST).
Uses Lark grammar to parse and builds a structured representation.
""",
    )

    show_transformation(
        "Parse Stage",
        """PowerBuilder source:
public function integer of_send_email();
    if isnull(is_smtp_server) then
        messagebox("Error", "SMTP server not configured")
        return -1
    end if
end function""",
        """AST (n_cst_email.ast.json):
{
  "node_type": "PBFunction",
  "name": "of_send_email",
  "return_type": "integer",
  "access": "public",
  "body": {
    "node_type": "PBBlock",
    "statements": [{
      "node_type": "PBIfStatement",
      "condition": {
        "node_type": "PBFunctionCall",
        "name": "isnull",
        "arguments": [{
          "node_type": "PBIdentifier",
          "name": "is_smtp_server"
        }]
      },
      "then_block": {
        "statements": [{
          "node_type": "PBFunctionCall",
          "name": "messagebox",
          "arguments": [
            {"node_type": "PBLiteral", "value": "Error"},
            {"node_type": "PBLiteral", "value": "SMTP server not configured"}
          ]
        }]
      }
    }]
  }
}""",
    )

    # Stage 4: Model
    print_section(
        "STAGE 4: MODEL",
        """
Command: python main.py model output/3_parsed output/4_model

Builds semantic models from the AST, identifying patterns and relationships.
This stage understands the business logic and prepares for code generation.
""",
    )

    show_transformation(
        "Model Stage",
        """AST with function calls and variables""",
        """Semantic Model (n_cst_email.model.json):
{
  "type": "ServiceClass",
  "name": "EmailService",
  "purpose": "Email sending functionality",
  "properties": [{
    "name": "smtpServer",
    "type": "string",
    "visibility": "private"
  }],
  "methods": [{
    "name": "sendEmail",
    "returns": "Future<bool>",
    "async": true,
    "business_logic": {
      "validation": ["Check SMTP server configured"],
      "operations": ["Create mail session", "Send email"],
      "error_handling": ["Show error message", "Return error code"]
    }
  }],
  "dependencies": ["MailSessionService"]
}""",
    )

    # Stage 5: Generate
    print_section(
        "STAGE 5: GENERATE",
        """
Command: python main.py generate output/4_model output/5_generated

Generates modern Flutter and Python code from the semantic models.
Applies templates and best practices for the target platforms.
""",
    )

    show_transformation(
        "Generate Stage - Flutter",
        """Semantic model with email service""",
        """Generated Flutter (email_service.dart):
import 'package:flutter/material.dart';
import 'package:mailer/mailer.dart';

class EmailService extends ChangeNotifier {
  String? _smtpServer;
  int _smtpPort = 25;
  final List<String> _recipients = [];

  Future<bool> sendEmail() async {
    if (_smtpServer == null || _smtpServer!.isEmpty) {
      throw Exception('SMTP server not configured');
    }

    try {
      final smtpServer = SmtpServer(_smtpServer!, port: _smtpPort);
      final message = Message()
        ..from = Address('noreply@example.com')
        ..recipients.addAll(_recipients)
        ..subject = 'Email Subject'
        ..text = 'Email body';

      await send(message, smtpServer);
      return true;
    } catch (e) {
      print('Error sending email: $e');
      return false;
    }
  }
}""",
    )

    show_transformation(
        "Generate Stage - Python",
        """Semantic model with email service""",
        """Generated Python (email_service.py):
import smtplib
from email.mime.text import MIMEText
from typing import List, Optional

class EmailService:
    def __init__(self):
        self.smtp_server: Optional[str] = None
        self.smtp_port: int = 25
        self.recipients: List[str] = []

    def send_email(self) -> bool:
        if not self.smtp_server:
            raise ValueError("SMTP server not configured")

        try:
            msg = MIMEText("Email body")
            msg['Subject'] = "Email Subject"
            msg['From'] = "noreply@example.com"
            msg['To'] = ', '.join(self.recipients)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False""",
    )

    # Complete Pipeline
    print_section(
        "RUNNING THE COMPLETE PIPELINE",
        """
To run all stages at once:

python main.py all input.pbd output/

This will:
1. Extract P-code from the PBD
2. Decompile to PowerBuilder source
3. Parse to AST
4. Build semantic models
5. Generate Flutter and Python code

The final output structure:
output/
├── 1_extracted/     # P-code files (.fun)
├── 2_decompiled/    # PowerBuilder source (.sru)
├── 3_parsed/        # AST files (.ast.json)
├── 4_model/         # Semantic models (.model.json)
└── 5_generated/     # Modern code
    ├── flutter/     # Dart files
    └── python/      # Python files
""",
    )



if __name__ == "__main__":
    main()
