# PowerRebuilder Pipeline Demo

## Quick Start

### View the Pipeline Demonstration

```bash
# See the complete pipeline transformation with examples
python demo_cli_pipeline.py
```

### Run the Actual Pipeline

```bash
# Run all stages on a PBD file
python main.py all data/dcm_email.pbd output/

# Or run each stage individually:
python main.py extract data/dcm_email.pbd output/1_extracted
python main.py decompile output/1_extracted output/2_decompiled  
python main.py parse output/2_decompiled output/3_parsed
python main.py model output/3_parsed output/4_model
python main.py generate output/4_model output/5_generated
```

## Pipeline Stages

1. **Extract**: PBD → P-code files (.fun)
2. **Decompile**: P-code → PowerBuilder source (.sru)
3. **Parse**: PowerBuilder source → AST (JSON)
4. **Model**: AST → Semantic models
5. **Generate**: Models → Flutter/Python code

## Example Transformation

### Input: PowerBuilder Code
```powerbuilder
public function integer of_send_email();
    if isnull(is_smtp_server) then
        messagebox("Error", "SMTP server not configured")
        return -1
    end if
    
    lnv_session = create n_cst_mailsession
    li_return = lnv_session.of_send()
    destroy lnv_session
    
    return li_return
end function
```

### Output: Modern Flutter
```dart
Future<bool> sendEmail() async {
  if (_smtpServer == null || _smtpServer!.isEmpty) {
    throw Exception('SMTP server not configured');
  }
  
  try {
    final session = MailSessionService();
    final result = await session.send();
    return result;
  } catch (e) {
    print('Error sending email: $e');
    return false;
  }
}
```

### Output: Modern Python
```python
async def send_email(self) -> bool:
    if not self.smtp_server:
        raise ValueError("SMTP server not configured")
        
    try:
        session = MailSessionService()
        result = await session.send()
        return result
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
```

## Documentation

- [Pipeline Architecture](PIPELINE_DEMONSTRATION.md) - Detailed walkthrough
- [Quick Reference](docs/QUICK_REFERENCE.md) - Command reference
- [Architecture](docs/ARCHITECTURE.md) - System design