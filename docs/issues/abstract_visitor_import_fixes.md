# Abstract Visitor Import Fixes

## Summary

Fixed import issues in `parse/visitors/abstract_visitor.py` where many classes were being imported from incorrect module paths.

## Changes Made

### 1. Fixed Existing Import Paths

- `model.entities.function_entities`: Now correctly imports `PBArgumentNode`, `PBArgumentOptionNode`, `PBArgumentsNode`, and `PBDefaultVariableNode`
- `model.pb_datawindow`: Correctly imports DataWindow-related node classes
- `model.entities.pb_event`: Correctly imports event-related node classes
- `model.ast`: Correctly imports `Type` as `PBBasicTypeNode` and `CustomType` as `PBCustomTypeNode`

### 2. Created Stub Classes

Since many of the expression-related nodes referenced in the abstract visitor don't actually exist in the codebase, stub classes were created as dataclasses inheriting from `PBNode`. These include:

- `PBAccessOrTypeNode`
- `PBArrayDesignationNode`
- `PBAssignationNode`
- `PBAssignationStatementNode`
- `PBBooleanValueNode`
- `PBCallStatementNode`
- `PBCaseElseNode`
- `PBCaseNode`
- `PBChooseCaseNode`
- `PBConditionNode`
- `PBConstantNode`
- `PBContinueStatementNode`
- `PBCreateInstructionNode`
- `PBCreateUsingInstructionNode`
- `PBCustomCallStatementNode`
- `PBDescriptorNode`
- `PBDestroyStatementNode`
- `PBDoLoopUntilNode`
- `PBDoLoopWhileNode`
- `PBDoUntilLoopNode`
- `PBDoWhileLoopNode`
- `PBDynamicMethodInvocationNode`
- `PBElseIfNode`
- `PBElseNode`
- `PBElseOnLineNode`
- `PBEndForwardNode`
- `PBExitStatementNode`
- `PBExportNode`
- `PBExpressionActionNode`
- `PBExpressionListNode`
- `PBExpressionNode`
- `PBExpressionOperatorNode`

### 3. Fixed Related Import Issues

Also fixed import paths in other files:
- `parse/visitors/position_tracker.py`: Changed `model.source.source` to `model.source`
- `parse/visitors/transformer.py`: Changed `model.library.library` to `model.library` and `model.ui.ui_elements` to `model.ui`

## Notes

The abstract visitor was ported from `reference/moose-pb-parser/PowerBuilder-Parser-Visitor/PWBASTAbstractVisitor.class.st` but many of the node classes it references were never implemented in this codebase. The stub classes allow the file to compile and be imported without errors. These stubs should be replaced with proper implementations as needed, or the corresponding visitor methods should be removed if they're not required.

## Verification

All imports now work correctly:
```python
from parse.visitors.abstract_visitor import PowerBuilderASTVisitor
# Successfully imports without errors
```