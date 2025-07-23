# PowerRebuilder Naming Collision Analysis

## Summary

Total naming collisions detected: **126**

- Critical: 0
- High: 3
- Medium: 11
- Low: 112

## Collision Details

### HIGH Severity Collisions

#### Classes: `PipelineMetrics` (6 occurrences)
**Locations:**
- `common.pipeline.modes.parallel`
- `core.async_utils`
- `decompile.async_coordinator`
- `extract.async_coordinator`
- `generate.async_coordinator`
- `parse.async_coordinator`

**Suggested Renames:**
- `common.pipeline.modes.parallel`: `PipelineMetrics` → `pipeline_PipelineMetrics`
- `core.async_utils`: `PipelineMetrics` → `async_utils_PipelineMetrics`
- `decompile.async_coordinator`: `PipelineMetrics` → `async_coordinator_PipelineMetrics`
- `extract.async_coordinator`: `PipelineMetrics` → `async_coordinator_PipelineMetrics`
- `generate.async_coordinator`: `PipelineMetrics` → `async_coordinator_PipelineMetrics`
- `parse.async_coordinator`: `PipelineMetrics` → `async_coordinator_PipelineMetrics`

#### Classes: `PipelineStage` (5 occurrences)
**Locations:**
- `common.pipeline.base`
- `common.pipeline.interfaces`
- `common.pipeline.modes.parallel`
- `contracts.interfaces`
- `core.pipeline_interfaces`

**Suggested Renames:**
- `common.pipeline.base`: `PipelineStage` → `pipeline_PipelineStage`
- `common.pipeline.interfaces`: `PipelineStage` → `pipeline_PipelineStage`
- `common.pipeline.modes.parallel`: `PipelineStage` → `pipeline_PipelineStage`
- `contracts.interfaces`: `PipelineStage` → `interfaces_PipelineStage`
- `core.pipeline_interfaces`: `PipelineStage` → `pipeline_interfaces_PipelineStage`

#### Classes: `DatabaseOperation` (4 occurrences)
**Locations:**
- `decompile.extractors.logic`
- `decompile.extractors.schema`
- `decompile.extractors.schema_extractor`
- `generate.converters.flutter.api`

**Suggested Renames:**
- `decompile.extractors.logic`: `DatabaseOperation` → `extractors_DatabaseOperation`
- `decompile.extractors.schema`: `DatabaseOperation` → `extractors_DatabaseOperation`
- `decompile.extractors.schema_extractor`: `DatabaseOperation` → `extractors_DatabaseOperation`
- `generate.converters.flutter.api`: `DatabaseOperation` → `converters_DatabaseOperation`

### MEDIUM Severity Collisions

#### Functions: `camel_to_snake` (3 occurrences)
**Locations:**
- `common.utils`
- `common.utils.strings`
- `model.utils.common`

**Suggested Renames:**
- `common.utils`: `camel_to_snake` → `utils_camel_to_snake`
- `common.utils.strings`: `camel_to_snake` → `utils_camel_to_snake`
- `model.utils.common`: `camel_to_snake` → `utils_camel_to_snake`

#### Classes: `ValidationError` (3 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`
- `decompile.core.validator`

**Suggested Renames:**
- `core.exception_hierarchy`: `ValidationError` → `exception_hierarchy_ValidationError`
- `core.exceptions`: `ValidationError` → `exceptions_ValidationError`
- `decompile.core.validator`: `ValidationError` → `core_ValidationError`

#### Classes: `SecurityError` (3 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`
- `core.security`

**Suggested Renames:**
- `core.exception_hierarchy`: `SecurityError` → `exception_hierarchy_SecurityError`
- `core.exceptions`: `SecurityError` → `exceptions_SecurityError`
- `core.security`: `SecurityError` → `security_SecurityError`

#### Classes: `ResourceLimitError` (3 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`
- `core.resource_limits`

**Suggested Renames:**
- `core.exception_hierarchy`: `ResourceLimitError` → `exception_hierarchy_ResourceLimitError`
- `core.exceptions`: `ResourceLimitError` → `exceptions_ResourceLimitError`
- `core.resource_limits`: `ResourceLimitError` → `resource_limits_ResourceLimitError`

#### Classes: `ResourceExtractionManager` (3 occurrences)
**Locations:**
- `extract.pbd.binary`
- `extract.pbd.manager`
- `extract.pbd.res_manager`

**Suggested Renames:**
- `extract.pbd.binary`: `ResourceExtractionManager` → `pbd_ResourceExtractionManager`
- `extract.pbd.manager`: `ResourceExtractionManager` → `pbd_ResourceExtractionManager`
- `extract.pbd.res_manager`: `ResourceExtractionManager` → `pbd_ResourceExtractionManager`

#### Classes: `PathValidator` (3 occurrences)
**Locations:**
- `core.security`
- `extract.security`
- `extract.security.paths`

**Suggested Renames:**
- `core.security`: `PathValidator` → `security_PathValidator`
- `extract.security`: `PathValidator` → `security_PathValidator`
- `extract.security.paths`: `PathValidator` → `security_PathValidator`

#### Classes: `PathTraversalError` (3 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`
- `core.security`

**Suggested Renames:**
- `core.exception_hierarchy`: `PathTraversalError` → `exception_hierarchy_PathTraversalError`
- `core.exceptions`: `PathTraversalError` → `exceptions_PathTraversalError`
- `core.security`: `PathTraversalError` → `security_PathTraversalError`

#### Classes: `IPipelineStage` (3 occurrences)
**Locations:**
- `common.pipeline.interfaces`
- `contracts.interfaces`
- `core.pipeline_interfaces`

**Suggested Renames:**
- `common.pipeline.interfaces`: `IPipelineStage` → `pipeline_IPipelineStage`
- `contracts.interfaces`: `IPipelineStage` → `interfaces_IPipelineStage`
- `core.pipeline_interfaces`: `IPipelineStage` → `pipeline_interfaces_IPipelineStage`

#### Classes: `IPipelineCoordinator` (3 occurrences)
**Locations:**
- `common.pipeline.interfaces`
- `contracts.interfaces`
- `core.pipeline_interfaces`

**Suggested Renames:**
- `common.pipeline.interfaces`: `IPipelineCoordinator` → `pipeline_IPipelineCoordinator`
- `contracts.interfaces`: `IPipelineCoordinator` → `interfaces_IPipelineCoordinator`
- `core.pipeline_interfaces`: `IPipelineCoordinator` → `pipeline_interfaces_IPipelineCoordinator`

#### Classes: `ExtractCoordinator` (3 occurrences)
**Locations:**
- `extract.coordinator`
- `extract.security`
- `extract.security.security_coordinator`

**Suggested Renames:**
- `extract.coordinator`: `ExtractCoordinator` → `coordinator_ExtractCoordinator`
- `extract.security`: `ExtractCoordinator` → `security_ExtractCoordinator`
- `extract.security.security_coordinator`: `ExtractCoordinator` → `security_ExtractCoordinator`

#### Classes: `Event` (3 occurrences)
**Locations:**
- `contracts.interfaces`
- `core.events_interfaces`
- `model.ast.functions`

**Suggested Renames:**
- `contracts.interfaces`: `Event` → `interfaces_Event`
- `core.events_interfaces`: `Event` → `events_interfaces_Event`
- `model.ast.functions`: `Event` → `ast_Event`

### LOW Severity Collisions

#### Functions: `truncate` (2 occurrences)
**Locations:**
- `common.utils`
- `common.utils.strings`

**Suggested Renames:**
- `common.utils`: `truncate` → `utils_truncate`
- `common.utils.strings`: `truncate` → `utils_truncate`

#### Functions: `snake_to_camel` (2 occurrences)
**Locations:**
- `common.utils`
- `common.utils.strings`

**Suggested Renames:**
- `common.utils`: `snake_to_camel` → `utils_snake_to_camel`
- `common.utils.strings`: `snake_to_camel` → `utils_snake_to_camel`

#### Functions: `sanitize_filename` (2 occurrences)
**Locations:**
- `common.utils`
- `core.security`

**Suggested Renames:**
- `common.utils`: `sanitize_filename` → `utils_sanitize_filename`
- `core.security`: `sanitize_filename` → `security_sanitize_filename`

#### Functions: `read_file_safe` (2 occurrences)
**Locations:**
- `common.utils`
- `common.utils.files`

**Suggested Renames:**
- `common.utils`: `read_file_safe` → `utils_read_file_safe`
- `common.utils.files`: `read_file_safe` → `utils_read_file_safe`

#### Functions: `pluralize` (2 occurrences)
**Locations:**
- `common.utils`
- `common.utils.strings`

**Suggested Renames:**
- `common.utils`: `pluralize` → `utils_pluralize`
- `common.utils.strings`: `pluralize` → `utils_pluralize`

#### Functions: `normalize_path` (2 occurrences)
**Locations:**
- `common.utils`
- `common.utils.files`

**Suggested Renames:**
- `common.utils`: `normalize_path` → `utils_normalize_path`
- `common.utils.files`: `normalize_path` → `utils_normalize_path`

#### Functions: `merge_dicts` (2 occurrences)
**Locations:**
- `common.utils`
- `common.utils.collections`

**Suggested Renames:**
- `common.utils`: `merge_dicts` → `utils_merge_dicts`
- `common.utils.collections`: `merge_dicts` → `utils_merge_dicts`

#### Functions: `load_grammar` (2 occurrences)
**Locations:**
- `parse.grammar.loader`
- `parse.utils.loader`

**Suggested Renames:**
- `parse.grammar.loader`: `load_grammar` → `grammar_load_grammar`
- `parse.utils.loader`: `load_grammar` → `utils_load_grammar`

#### Functions: `get_ico_size` (2 occurrences)
**Locations:**
- `extract.pbd.io`
- `extract.pbd.reader`

**Suggested Renames:**
- `extract.pbd.io`: `get_ico_size` → `pbd_get_ico_size`
- `extract.pbd.reader`: `get_ico_size` → `pbd_get_ico_size`

#### Functions: `get_file_extension` (2 occurrences)
**Locations:**
- `common.utils`
- `common.utils.files`

**Suggested Renames:**
- `common.utils`: `get_file_extension` → `utils_get_file_extension`
- `common.utils.files`: `get_file_extension` → `utils_get_file_extension`

#### Functions: `get_error_description` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `get_error_description` → `exception_hierarchy_get_error_description`
- `core.exceptions`: `get_error_description` → `exceptions_get_error_description`

#### Functions: `get_bmp_size` (2 occurrences)
**Locations:**
- `extract.pbd.io`
- `extract.pbd.reader`

**Suggested Renames:**
- `extract.pbd.io`: `get_bmp_size` → `pbd_get_bmp_size`
- `extract.pbd.reader`: `get_bmp_size` → `pbd_get_bmp_size`

#### Functions: `format_timestamp` (2 occurrences)
**Locations:**
- `common.utils`
- `common.utils.files`

**Suggested Renames:**
- `common.utils`: `format_timestamp` → `utils_format_timestamp`
- `common.utils.files`: `format_timestamp` → `utils_format_timestamp`

#### Functions: `find_duplicates` (2 occurrences)
**Locations:**
- `common.utils`
- `common.utils.collections`

**Suggested Renames:**
- `common.utils`: `find_duplicates` → `utils_find_duplicates`
- `common.utils.collections`: `find_duplicates` → `utils_find_duplicates`

#### Functions: `filter_dict` (2 occurrences)
**Locations:**
- `common.utils`
- `common.utils.collections`

**Suggested Renames:**
- `common.utils`: `filter_dict` → `utils_filter_dict`
- `common.utils.collections`: `filter_dict` → `utils_filter_dict`

#### Functions: `ensure_directory` (2 occurrences)
**Locations:**
- `common.utils`
- `common.utils.files`

**Suggested Renames:**
- `common.utils`: `ensure_directory` → `utils_ensure_directory`
- `common.utils.files`: `ensure_directory` → `utils_ensure_directory`

#### Functions: `create_model_coordinator` (2 occurrences)
**Locations:**
- `core.dependency_injection`
- `model.factory`

**Suggested Renames:**
- `core.dependency_injection`: `create_model_coordinator` → `dependency_injection_create_model_coordinator`
- `model.factory`: `create_model_coordinator` → `factory_create_model_coordinator`

#### Functions: `create_generate_coordinator` (2 occurrences)
**Locations:**
- `core.dependency_injection`
- `generate.factory`

**Suggested Renames:**
- `core.dependency_injection`: `create_generate_coordinator` → `dependency_injection_create_generate_coordinator`
- `generate.factory`: `create_generate_coordinator` → `factory_create_generate_coordinator`

#### Functions: `chunk_list` (2 occurrences)
**Locations:**
- `common.utils`
- `common.utils.collections`

**Suggested Renames:**
- `common.utils`: `chunk_list` → `utils_chunk_list`
- `common.utils.collections`: `chunk_list` → `utils_chunk_list`

#### Functions: `_is_file_handle` (2 occurrences)
**Locations:**
- `extract.pbd.scanner`
- `extract.utils.binary`

**Suggested Renames:**
- `extract.pbd.scanner`: `_is_file_handle` → `pbd__is_file_handle`
- `extract.utils.binary`: `_is_file_handle` → `utils__is_file_handle`

#### Classes: `Variable` (2 occurrences)
**Locations:**
- `generate.converters.utils.ast`
- `model.types.base`

**Suggested Renames:**
- `generate.converters.utils.ast`: `Variable` → `converters_Variable`
- `model.types.base`: `Variable` → `types_Variable`

#### Classes: `ValidationRule` (2 occurrences)
**Locations:**
- `generate.converters.flutter.dw_enhancements`
- `generate.schemas`

**Suggested Renames:**
- `generate.converters.flutter.dw_enhancements`: `ValidationRule` → `converters_ValidationRule`
- `generate.schemas`: `ValidationRule` → `schemas_ValidationRule`

#### Classes: `UntrustedInputError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `UntrustedInputError` → `exception_hierarchy_UntrustedInputError`
- `core.exceptions`: `UntrustedInputError` → `exceptions_UntrustedInputError`

#### Classes: `UnaryExpression` (2 occurrences)
**Locations:**
- `model.ast.literals`
- `model.expressions.ast_expressions`

**Suggested Renames:**
- `model.ast.literals`: `UnaryExpression` → `ast_UnaryExpression`
- `model.expressions.ast_expressions`: `UnaryExpression` → `expressions_UnaryExpression`

#### Classes: `TypeResolver` (2 occurrences)
**Locations:**
- `parse.resolution`
- `parse.transformer.resolver`

**Suggested Renames:**
- `parse.resolution`: `TypeResolver` → `resolution_TypeResolver`
- `parse.transformer.resolver`: `TypeResolver` → `transformer_TypeResolver`

#### Classes: `TypeResolutionError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `TypeResolutionError` → `exception_hierarchy_TypeResolutionError`
- `core.exceptions`: `TypeResolutionError` → `exceptions_TypeResolutionError`

#### Classes: `TypeConverter` (2 occurrences)
**Locations:**
- `generate.converters.flutter.models`
- `generate.converters.utils.types`

**Suggested Renames:**
- `generate.converters.flutter.models`: `TypeConverter` → `converters_TypeConverter`
- `generate.converters.utils.types`: `TypeConverter` → `converters_TypeConverter`

#### Classes: `TemplateError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `TemplateError` → `exception_hierarchy_TemplateError`
- `core.exceptions`: `TemplateError` → `exceptions_TemplateError`

#### Classes: `TargetLanguageError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `TargetLanguageError` → `exception_hierarchy_TargetLanguageError`
- `core.exceptions`: `TargetLanguageError` → `exceptions_TargetLanguageError`

#### Classes: `StringResourceExtractor` (2 occurrences)
**Locations:**
- `extract.pbd.binary`
- `extract.pbd.strings`

**Suggested Renames:**
- `extract.pbd.binary`: `StringResourceExtractor` → `pbd_StringResourceExtractor`
- `extract.pbd.strings`: `StringResourceExtractor` → `pbd_StringResourceExtractor`

#### Classes: `StringLiteral` (2 occurrences)
**Locations:**
- `model.ast.literals`
- `model.expressions.ast_expressions`

**Suggested Renames:**
- `model.ast.literals`: `StringLiteral` → `ast_StringLiteral`
- `model.expressions.ast_expressions`: `StringLiteral` → `expressions_StringLiteral`

#### Classes: `StandardLogger` (2 occurrences)
**Locations:**
- `common.interface_logger`
- `contracts.logger`

**Suggested Renames:**
- `common.interface_logger`: `StandardLogger` → `interface_logger_StandardLogger`
- `contracts.logger`: `StandardLogger` → `logger_StandardLogger`

#### Classes: `StageStatus` (2 occurrences)
**Locations:**
- `contracts.interfaces`
- `core.state_interfaces`

**Suggested Renames:**
- `contracts.interfaces`: `StageStatus` → `interfaces_StageStatus`
- `core.state_interfaces`: `StageStatus` → `state_interfaces_StageStatus`

#### Classes: `StackUnderflowError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `StackUnderflowError` → `exception_hierarchy_StackUnderflowError`
- `core.exceptions`: `StackUnderflowError` → `exceptions_StackUnderflowError`

#### Classes: `ServiceGenerator` (2 occurrences)
**Locations:**
- `generate.coordinators.service`
- `generate.service`

**Suggested Renames:**
- `generate.coordinators.service`: `ServiceGenerator` → `coordinators_ServiceGenerator`
- `generate.service`: `ServiceGenerator` → `service_ServiceGenerator`

#### Classes: `SemanticError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `SemanticError` → `exception_hierarchy_SemanticError`
- `core.exceptions`: `SemanticError` → `exceptions_SemanticError`

#### Classes: `Scope` (2 occurrences)
**Locations:**
- `model.symbols.scope`
- `model.symbols.table`

**Suggested Renames:**
- `model.symbols.scope`: `Scope` → `symbols_Scope`
- `model.symbols.table`: `Scope` → `symbols_Scope`

#### Classes: `SQLTransformer` (2 occurrences)
**Locations:**
- `parse.transformer.sql`
- `parse.transformer.sql_transformer`

**Suggested Renames:**
- `parse.transformer.sql`: `SQLTransformer` → `transformer_SQLTransformer`
- `parse.transformer.sql_transformer`: `SQLTransformer` → `transformer_SQLTransformer`

#### Classes: `ResourceExtractionError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `ResourceExtractionError` → `exception_hierarchy_ResourceExtractionError`
- `core.exceptions`: `ResourceExtractionError` → `exceptions_ResourceExtractionError`

#### Classes: `ResolutionContext` (2 occurrences)
**Locations:**
- `parse.resolution`
- `parse.transformer.resolver`

**Suggested Renames:**
- `parse.resolution`: `ResolutionContext` → `resolution_ResolutionContext`
- `parse.transformer.resolver`: `ResolutionContext` → `transformer_ResolutionContext`

#### Classes: `RelationshipType` (2 occurrences)
**Locations:**
- `generate.converters.data.relationships`
- `generate.schemas`

**Suggested Renames:**
- `generate.converters.data.relationships`: `RelationshipType` → `converters_RelationshipType`
- `generate.schemas`: `RelationshipType` → `schemas_RelationshipType`

#### Classes: `RecoveryStrategy` (2 occurrences)
**Locations:**
- `core.errors`
- `core.recovery`

**Suggested Renames:**
- `core.errors`: `RecoveryStrategy` → `errors_RecoveryStrategy`
- `core.recovery`: `RecoveryStrategy` → `recovery_RecoveryStrategy`

#### Classes: `RealLiteral` (2 occurrences)
**Locations:**
- `model.ast.literals`
- `model.expressions.ast_expressions`

**Suggested Renames:**
- `model.ast.literals`: `RealLiteral` → `ast_RealLiteral`
- `model.expressions.ast_expressions`: `RealLiteral` → `expressions_RealLiteral`

#### Classes: `ProgressTracker` (2 occurrences)
**Locations:**
- `common.pipeline.progress`
- `core.coordination_mixins`

**Suggested Renames:**
- `common.pipeline.progress`: `ProgressTracker` → `pipeline_ProgressTracker`
- `core.coordination_mixins`: `ProgressTracker` → `coordination_mixins_ProgressTracker`

#### Classes: `PipelineError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `PipelineError` → `exception_hierarchy_PipelineError`
- `core.exceptions`: `PipelineError` → `exceptions_PipelineError`

#### Classes: `PbEntryDefinition` (2 occurrences)
**Locations:**
- `extract.pbd.data_block`
- `extract.pbd.entry`

**Suggested Renames:**
- `extract.pbd.data_block`: `PbEntryDefinition` → `pbd_PbEntryDefinition`
- `extract.pbd.entry`: `PbEntryDefinition` → `pbd_PbEntryDefinition`

#### Classes: `ParseRecoveryError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `ParseRecoveryError` → `exception_hierarchy_ParseRecoveryError`
- `core.exceptions`: `ParseRecoveryError` → `exceptions_ParseRecoveryError`

#### Classes: `ParseError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `ParseError` → `exception_hierarchy_ParseError`
- `core.exceptions`: `ParseError` → `exceptions_ParseError`

#### Classes: `Parameter` (2 occurrences)
**Locations:**
- `model.ast.functions`
- `model.types.base`

**Suggested Renames:**
- `model.ast.functions`: `Parameter` → `ast_Parameter`
- `model.types.base`: `Parameter` → `types_Parameter`

#### Classes: `ParallelPipeline` (2 occurrences)
**Locations:**
- `common.pipeline.modes.parallel`
- `core.async_utils`

**Suggested Renames:**
- `common.pipeline.modes.parallel`: `ParallelPipeline` → `pipeline_ParallelPipeline`
- `core.async_utils`: `ParallelPipeline` → `async_utils_ParallelPipeline`

#### Classes: `PBVariable` (2 occurrences)
**Locations:**
- `model.entities.function`
- `model.expressions.pb_expressions`

**Suggested Renames:**
- `model.entities.function`: `PBVariable` → `entities_PBVariable`
- `model.expressions.pb_expressions`: `PBVariable` → `expressions_PBVariable`

#### Classes: `PBSourcedEntity` (2 occurrences)
**Locations:**
- `model.ast.pb_types`
- `model.base.pb_entity`

**Suggested Renames:**
- `model.ast.pb_types`: `PBSourcedEntity` → `ast_PBSourcedEntity`
- `model.base.pb_entity`: `PBSourcedEntity` → `base_PBSourcedEntity`

#### Classes: `PBGlobalVariable` (2 occurrences)
**Locations:**
- `model.entities.function`
- `model.system.globals`

**Suggested Renames:**
- `model.entities.function`: `PBGlobalVariable` → `entities_PBGlobalVariable`
- `model.system.globals`: `PBGlobalVariable` → `system_PBGlobalVariable`

#### Classes: `PBFunctionCall` (2 occurrences)
**Locations:**
- `model.entities.function`
- `model.expressions.pb_expressions`

**Suggested Renames:**
- `model.entities.function`: `PBFunctionCall` → `entities_PBFunctionCall`
- `model.expressions.pb_expressions`: `PBFunctionCall` → `expressions_PBFunctionCall`

#### Classes: `PBEventAttributeNode` (2 occurrences)
**Locations:**
- `model.entities.event`
- `parse.transformer.visitors.visitor`

**Suggested Renames:**
- `model.entities.event`: `PBEventAttributeNode` → `entities_PBEventAttributeNode`
- `parse.transformer.visitors.visitor`: `PBEventAttributeNode` → `transformer_PBEventAttributeNode`

#### Classes: `PBDefaultVariableNode` (2 occurrences)
**Locations:**
- `model.entities.function`
- `parse.transformer.visitors.visitor`

**Suggested Renames:**
- `model.entities.function`: `PBDefaultVariableNode` → `entities_PBDefaultVariableNode`
- `parse.transformer.visitors.visitor`: `PBDefaultVariableNode` → `transformer_PBDefaultVariableNode`

#### Classes: `PBArgumentsNode` (2 occurrences)
**Locations:**
- `model.entities.function`
- `parse.transformer.visitors.visitor`

**Suggested Renames:**
- `model.entities.function`: `PBArgumentsNode` → `entities_PBArgumentsNode`
- `parse.transformer.visitors.visitor`: `PBArgumentsNode` → `transformer_PBArgumentsNode`

#### Classes: `PBArgumentOptionNode` (2 occurrences)
**Locations:**
- `model.entities.function`
- `parse.transformer.visitors.visitor`

**Suggested Renames:**
- `model.entities.function`: `PBArgumentOptionNode` → `entities_PBArgumentOptionNode`
- `parse.transformer.visitors.visitor`: `PBArgumentOptionNode` → `transformer_PBArgumentOptionNode`

#### Classes: `PBArgumentNode` (2 occurrences)
**Locations:**
- `model.entities.function`
- `parse.transformer.visitors.visitor`

**Suggested Renames:**
- `model.entities.function`: `PBArgumentNode` → `entities_PBArgumentNode`
- `parse.transformer.visitors.visitor`: `PBArgumentNode` → `transformer_PBArgumentNode`

#### Classes: `OpcodeError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `OpcodeError` → `exception_hierarchy_OpcodeError`
- `core.exceptions`: `OpcodeError` → `exceptions_OpcodeError`

#### Classes: `NullLiteral` (2 occurrences)
**Locations:**
- `model.ast.literals`
- `model.expressions.ast_expressions`

**Suggested Renames:**
- `model.ast.literals`: `NullLiteral` → `ast_NullLiteral`
- `model.expressions.ast_expressions`: `NullLiteral` → `expressions_NullLiteral`

#### Classes: `ModelGenerator` (2 occurrences)
**Locations:**
- `generate.coordinators.model`
- `generate.models`

**Suggested Renames:**
- `generate.coordinators.model`: `ModelGenerator` → `coordinators_ModelGenerator`
- `generate.models`: `ModelGenerator` → `models_ModelGenerator`

#### Classes: `ModelError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `ModelError` → `exception_hierarchy_ModelError`
- `core.exceptions`: `ModelError` → `exceptions_ModelError`

#### Classes: `LikeExpression` (2 occurrences)
**Locations:**
- `model.ast.additional_nodes`
- `model.expressions.ast_expressions`

**Suggested Renames:**
- `model.ast.additional_nodes`: `LikeExpression` → `ast_LikeExpression`
- `model.expressions.ast_expressions`: `LikeExpression` → `expressions_LikeExpression`

#### Classes: `LibraryCorruptedError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `LibraryCorruptedError` → `exception_hierarchy_LibraryCorruptedError`
- `core.exceptions`: `LibraryCorruptedError` → `exceptions_LibraryCorruptedError`

#### Classes: `LambdaExpression` (2 occurrences)
**Locations:**
- `model.ast.functions`
- `model.expressions.ast_expressions`

**Suggested Renames:**
- `model.ast.functions`: `LambdaExpression` → `ast_LambdaExpression`
- `model.expressions.ast_expressions`: `LambdaExpression` → `expressions_LambdaExpression`

#### Classes: `InvalidFileFormatError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `InvalidFileFormatError` → `exception_hierarchy_InvalidFileFormatError`
- `core.exceptions`: `InvalidFileFormatError` → `exceptions_InvalidFileFormatError`

#### Classes: `IntegerLiteral` (2 occurrences)
**Locations:**
- `model.ast.literals`
- `model.expressions.ast_expressions`

**Suggested Renames:**
- `model.ast.literals`: `IntegerLiteral` → `ast_IntegerLiteral`
- `model.expressions.ast_expressions`: `IntegerLiteral` → `expressions_IntegerLiteral`

#### Classes: `InExpression` (2 occurrences)
**Locations:**
- `model.ast.additional_nodes`
- `model.expressions.ast_expressions`

**Suggested Renames:**
- `model.ast.additional_nodes`: `InExpression` → `ast_InExpression`
- `model.expressions.ast_expressions`: `InExpression` → `expressions_InExpression`

#### Classes: `Identifier` (2 occurrences)
**Locations:**
- `model.ast.literals`
- `model.types.base`

**Suggested Renames:**
- `model.ast.literals`: `Identifier` → `ast_Identifier`
- `model.types.base`: `Identifier` → `types_Identifier`

#### Classes: `ITransformer` (2 occurrences)
**Locations:**
- `contracts.interfaces`
- `model.types.interfaces`

**Suggested Renames:**
- `contracts.interfaces`: `ITransformer` → `interfaces_ITransformer`
- `model.types.interfaces`: `ITransformer` → `types_ITransformer`

#### Classes: `IStateManager` (2 occurrences)
**Locations:**
- `contracts.interfaces`
- `core.state_interfaces`

**Suggested Renames:**
- `contracts.interfaces`: `IStateManager` → `interfaces_IStateManager`
- `core.state_interfaces`: `IStateManager` → `state_interfaces_IStateManager`

#### Classes: `IPipelineState` (2 occurrences)
**Locations:**
- `contracts.interfaces`
- `core.state_interfaces`

**Suggested Renames:**
- `contracts.interfaces`: `IPipelineState` → `interfaces_IPipelineState`
- `core.state_interfaces`: `IPipelineState` → `state_interfaces_IPipelineState`

#### Classes: `IParser` (2 occurrences)
**Locations:**
- `contracts.interfaces`
- `model.types.interfaces`

**Suggested Renames:**
- `contracts.interfaces`: `IParser` → `interfaces_IParser`
- `model.types.interfaces`: `IParser` → `types_IParser`

#### Classes: `IModelPersistence` (2 occurrences)
**Locations:**
- `contracts.interfaces`
- `model.interfaces`

**Suggested Renames:**
- `contracts.interfaces`: `IModelPersistence` → `interfaces_IModelPersistence`
- `model.interfaces`: `IModelPersistence` → `interfaces_IModelPersistence`

#### Classes: `IModelExtractor` (2 occurrences)
**Locations:**
- `contracts.interfaces`
- `model.interfaces`

**Suggested Renames:**
- `contracts.interfaces`: `IModelExtractor` → `interfaces_IModelExtractor`
- `model.interfaces`: `IModelExtractor` → `interfaces_IModelExtractor`

#### Classes: `ILogger` (2 occurrences)
**Locations:**
- `common.interface_logger`
- `contracts.interfaces`

**Suggested Renames:**
- `common.interface_logger`: `ILogger` → `interface_logger_ILogger`
- `contracts.interfaces`: `ILogger` → `interfaces_ILogger`

#### Classes: `IEventHandler` (2 occurrences)
**Locations:**
- `contracts.interfaces`
- `core.events_interfaces`

**Suggested Renames:**
- `contracts.interfaces`: `IEventHandler` → `interfaces_IEventHandler`
- `core.events_interfaces`: `IEventHandler` → `events_interfaces_IEventHandler`

#### Classes: `IEventBus` (2 occurrences)
**Locations:**
- `contracts.interfaces`
- `core.events_interfaces`

**Suggested Renames:**
- `contracts.interfaces`: `IEventBus` → `interfaces_IEventBus`
- `core.events_interfaces`: `IEventBus` → `events_interfaces_IEventBus`

#### Classes: `IEntityValidator` (2 occurrences)
**Locations:**
- `contracts.interfaces`
- `model.interfaces`

**Suggested Renames:**
- `contracts.interfaces`: `IEntityValidator` → `interfaces_IEntityValidator`
- `model.interfaces`: `IEntityValidator` → `interfaces_IEntityValidator`

#### Classes: `IEntityFactory` (2 occurrences)
**Locations:**
- `contracts.interfaces`
- `model.interfaces`

**Suggested Renames:**
- `contracts.interfaces`: `IEntityFactory` → `interfaces_IEntityFactory`
- `model.interfaces`: `IEntityFactory` → `interfaces_IEntityFactory`

#### Classes: `IASTProcessor` (2 occurrences)
**Locations:**
- `contracts.interfaces`
- `model.interfaces`

**Suggested Renames:**
- `contracts.interfaces`: `IASTProcessor` → `interfaces_IASTProcessor`
- `model.interfaces`: `IASTProcessor` → `interfaces_IASTProcessor`

#### Classes: `GrammarError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `GrammarError` → `exception_hierarchy_GrammarError`
- `core.exceptions`: `GrammarError` → `exceptions_GrammarError`

#### Classes: `GenerationError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `GenerationError` → `exception_hierarchy_GenerationError`
- `core.exceptions`: `GenerationError` → `exceptions_GenerationError`

#### Classes: `FlutterGenerator` (2 occurrences)
**Locations:**
- `generate.coordinators.flutter`
- `generate.flutter`

**Suggested Renames:**
- `generate.coordinators.flutter`: `FlutterGenerator` → `coordinators_FlutterGenerator`
- `generate.flutter`: `FlutterGenerator` → `flutter_FlutterGenerator`

#### Classes: `FileNotFoundError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `FileNotFoundError` → `exception_hierarchy_FileNotFoundError`
- `core.exceptions`: `FileNotFoundError` → `exceptions_FileNotFoundError`

#### Classes: `ExtractionError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `ExtractionError` → `exception_hierarchy_ExtractionError`
- `core.exceptions`: `ExtractionError` → `exceptions_ExtractionError`

#### Classes: `ExistsExpression` (2 occurrences)
**Locations:**
- `model.ast.additional_nodes`
- `model.expressions.ast_expressions`

**Suggested Renames:**
- `model.ast.additional_nodes`: `ExistsExpression` → `ast_ExistsExpression`
- `model.expressions.ast_expressions`: `ExistsExpression` → `expressions_ExistsExpression`

#### Classes: `ExceptionFactory` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `ExceptionFactory` → `exception_hierarchy_ExceptionFactory`
- `core.exceptions`: `ExceptionFactory` → `exceptions_ExceptionFactory`

#### Classes: `EventType` (2 occurrences)
**Locations:**
- `contracts.interfaces`
- `core.events_interfaces`

**Suggested Renames:**
- `contracts.interfaces`: `EventType` → `interfaces_EventType`
- `core.events_interfaces`: `EventType` → `events_interfaces_EventType`

#### Classes: `ErrorRecoveryTransformer` (2 occurrences)
**Locations:**
- `parse.error_recovery.strategy`
- `parse.parser.powerbuilder`

**Suggested Renames:**
- `parse.error_recovery.strategy`: `ErrorRecoveryTransformer` → `error_recovery_ErrorRecoveryTransformer`
- `parse.parser.powerbuilder`: `ErrorRecoveryTransformer` → `parser_ErrorRecoveryTransformer`

#### Classes: `EnhancedImageExtractor` (2 occurrences)
**Locations:**
- `extract.pbd.binary`
- `extract.pbd.images`

**Suggested Renames:**
- `extract.pbd.binary`: `EnhancedImageExtractor` → `pbd_EnhancedImageExtractor`
- `extract.pbd.images`: `EnhancedImageExtractor` → `pbd_EnhancedImageExtractor`

#### Classes: `DetailedLoggerAdapter` (2 occurrences)
**Locations:**
- `common.interface_logger`
- `contracts.logger`

**Suggested Renames:**
- `common.interface_logger`: `DetailedLoggerAdapter` → `interface_logger_DetailedLoggerAdapter`
- `contracts.logger`: `DetailedLoggerAdapter` → `logger_DetailedLoggerAdapter`

#### Classes: `DesignSystemConverter` (2 occurrences)
**Locations:**
- `generate.converters.flutter.design_system`
- `generate.converters.flutter.themes`

**Suggested Renames:**
- `generate.converters.flutter.design_system`: `DesignSystemConverter` → `converters_DesignSystemConverter`
- `generate.converters.flutter.themes`: `DesignSystemConverter` → `converters_DesignSystemConverter`

#### Classes: `DependencyError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `DependencyError` → `exception_hierarchy_DependencyError`
- `core.exceptions`: `DependencyError` → `exceptions_DependencyError`

#### Classes: `DecompileError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `DecompileError` → `exception_hierarchy_DecompileError`
- `core.exceptions`: `DecompileError` → `exceptions_DecompileError`

#### Classes: `DecompilationLimitError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `DecompilationLimitError` → `exception_hierarchy_DecompilationLimitError`
- `core.exceptions`: `DecompilationLimitError` → `exceptions_DecompilationLimitError`

#### Classes: `DatabaseSchemaExtractor` (2 occurrences)
**Locations:**
- `decompile.extractors.schema`
- `decompile.extractors.schema_extractor`

**Suggested Renames:**
- `decompile.extractors.schema`: `DatabaseSchemaExtractor` → `extractors_DatabaseSchemaExtractor`
- `decompile.extractors.schema_extractor`: `DatabaseSchemaExtractor` → `extractors_DatabaseSchemaExtractor`

#### Classes: `DatabaseOperationFormatter` (2 occurrences)
**Locations:**
- `generate.converters.data.db_formatter`
- `generate.converters.flutter.api`

**Suggested Renames:**
- `generate.converters.data.db_formatter`: `DatabaseOperationFormatter` → `converters_DatabaseOperationFormatter`
- `generate.converters.flutter.api`: `DatabaseOperationFormatter` → `converters_DatabaseOperationFormatter`

#### Classes: `DataWindowDefinition` (2 occurrences)
**Locations:**
- `decompile.extractors.datawindow`
- `generate.converters.flutter.datawindows`

**Suggested Renames:**
- `decompile.extractors.datawindow`: `DataWindowDefinition` → `extractors_DataWindowDefinition`
- `generate.converters.flutter.datawindows`: `DataWindowDefinition` → `converters_DataWindowDefinition`

#### Classes: `DataWindowColumn` (2 occurrences)
**Locations:**
- `decompile.extractors.datawindow`
- `generate.converters.flutter.datawindows`

**Suggested Renames:**
- `decompile.extractors.datawindow`: `DataWindowColumn` → `extractors_DataWindowColumn`
- `generate.converters.flutter.datawindows`: `DataWindowColumn` → `converters_DataWindowColumn`

#### Classes: `CoordinatorError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `CoordinatorError` → `exception_hierarchy_CoordinatorError`
- `core.exceptions`: `CoordinatorError` → `exceptions_CoordinatorError`

#### Classes: `ConversionError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `ConversionError` → `exception_hierarchy_ConversionError`
- `core.exceptions`: `ConversionError` → `exceptions_ConversionError`

#### Classes: `ControlFlowError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `ControlFlowError` → `exception_hierarchy_ControlFlowError`
- `core.exceptions`: `ControlFlowError` → `exceptions_ControlFlowError`

#### Classes: `ConfigurationError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `ConfigurationError` → `exception_hierarchy_ConfigurationError`
- `core.exceptions`: `ConfigurationError` → `exceptions_ConfigurationError`

#### Classes: `CodeGenerator` (2 occurrences)
**Locations:**
- `generate.base`
- `generate.templates.python.python`

**Suggested Renames:**
- `generate.base`: `CodeGenerator` → `base_CodeGenerator`
- `generate.templates.python.python`: `CodeGenerator` → `templates_CodeGenerator`

#### Classes: `CodeGenerationLimitError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `CodeGenerationLimitError` → `exception_hierarchy_CodeGenerationLimitError`
- `core.exceptions`: `CodeGenerationLimitError` → `exceptions_CodeGenerationLimitError`

#### Classes: `BooleanLiteral` (2 occurrences)
**Locations:**
- `model.ast.literals`
- `model.expressions.ast_expressions`

**Suggested Renames:**
- `model.ast.literals`: `BooleanLiteral` → `ast_BooleanLiteral`
- `model.expressions.ast_expressions`: `BooleanLiteral` → `expressions_BooleanLiteral`

#### Classes: `BlockType` (2 occurrences)
**Locations:**
- `decompile.types`
- `model.types.decompile`

**Suggested Renames:**
- `decompile.types`: `BlockType` → `types_BlockType`
- `model.types.decompile`: `BlockType` → `types_BlockType`

#### Classes: `BinaryExpression` (2 occurrences)
**Locations:**
- `model.ast.literals`
- `model.expressions.ast_expressions`

**Suggested Renames:**
- `model.ast.literals`: `BinaryExpression` → `ast_BinaryExpression`
- `model.expressions.ast_expressions`: `BinaryExpression` → `expressions_BinaryExpression`

#### Classes: `BetweenExpression` (2 occurrences)
**Locations:**
- `model.ast.additional_nodes`
- `model.expressions.ast_expressions`

**Suggested Renames:**
- `model.ast.additional_nodes`: `BetweenExpression` → `ast_BetweenExpression`
- `model.expressions.ast_expressions`: `BetweenExpression` → `expressions_BetweenExpression`

#### Classes: `ASTConstructionError` (2 occurrences)
**Locations:**
- `core.exception_hierarchy`
- `core.exceptions`

**Suggested Renames:**
- `core.exception_hierarchy`: `ASTConstructionError` → `exception_hierarchy_ASTConstructionError`
- `core.exceptions`: `ASTConstructionError` → `exceptions_ASTConstructionError`

## Common Patterns Analysis

### Common Name Suffixes
- *Coordinator: 27 occurrences
- *Manager: 16 occurrences
- *Factory: 12 occurrences

## Import Collision Risks

The following scenarios would cause import conflicts after flattening:


### `from powerrebuilder import PipelineMetrics`
Would be ambiguous between:
- `common.pipeline.modes.parallel.PipelineMetrics`
- `core.async_utils.PipelineMetrics`
- `decompile.async_coordinator.PipelineMetrics`
- `extract.async_coordinator.PipelineMetrics`
- `generate.async_coordinator.PipelineMetrics`
- `parse.async_coordinator.PipelineMetrics`

### `from powerrebuilder import BlockType`
Would be ambiguous between:
- `decompile.types.BlockType`
- `model.types.decompile.BlockType`

### `from powerrebuilder import ValidationError`
Would be ambiguous between:
- `core.exception_hierarchy.ValidationError`
- `core.exceptions.ValidationError`
- `decompile.core.validator.ValidationError`

### `from powerrebuilder import DataWindowColumn`
Would be ambiguous between:
- `decompile.extractors.datawindow.DataWindowColumn`
- `generate.converters.flutter.datawindows.DataWindowColumn`

### `from powerrebuilder import DataWindowDefinition`
Would be ambiguous between:
- `decompile.extractors.datawindow.DataWindowDefinition`
- `generate.converters.flutter.datawindows.DataWindowDefinition`

### `from powerrebuilder import DatabaseSchemaExtractor`
Would be ambiguous between:
- `decompile.extractors.schema.DatabaseSchemaExtractor`
- `decompile.extractors.schema_extractor.DatabaseSchemaExtractor`

### `from powerrebuilder import DatabaseOperation`
Would be ambiguous between:
- `decompile.extractors.logic.DatabaseOperation`
- `decompile.extractors.schema.DatabaseOperation`
- `decompile.extractors.schema_extractor.DatabaseOperation`
- `generate.converters.flutter.api.DatabaseOperation`

### `from powerrebuilder import ResourceLimitError`
Would be ambiguous between:
- `core.exception_hierarchy.ResourceLimitError`
- `core.exceptions.ResourceLimitError`
- `core.resource_limits.ResourceLimitError`

### `from powerrebuilder import RecoveryStrategy`
Would be ambiguous between:
- `core.errors.RecoveryStrategy`
- `core.recovery.RecoveryStrategy`

### `from powerrebuilder import IPipelineCoordinator`
Would be ambiguous between:
- `common.pipeline.interfaces.IPipelineCoordinator`
- `contracts.interfaces.IPipelineCoordinator`
- `core.pipeline_interfaces.IPipelineCoordinator`

### `from powerrebuilder import PipelineStage`
Would be ambiguous between:
- `common.pipeline.base.PipelineStage`
- `common.pipeline.interfaces.PipelineStage`
- `common.pipeline.modes.parallel.PipelineStage`
- `contracts.interfaces.PipelineStage`
- `core.pipeline_interfaces.PipelineStage`

### `from powerrebuilder import IPipelineStage`
Would be ambiguous between:
- `common.pipeline.interfaces.IPipelineStage`
- `contracts.interfaces.IPipelineStage`
- `core.pipeline_interfaces.IPipelineStage`

### `from powerrebuilder import ParallelPipeline`
Would be ambiguous between:
- `common.pipeline.modes.parallel.ParallelPipeline`
- `core.async_utils.ParallelPipeline`

### `from powerrebuilder import ModelError`
Would be ambiguous between:
- `core.exception_hierarchy.ModelError`
- `core.exceptions.ModelError`

### `from powerrebuilder import OpcodeError`
Would be ambiguous between:
- `core.exception_hierarchy.OpcodeError`
- `core.exceptions.OpcodeError`

### `from powerrebuilder import GenerationError`
Would be ambiguous between:
- `core.exception_hierarchy.GenerationError`
- `core.exceptions.GenerationError`

### `from powerrebuilder import ParseRecoveryError`
Would be ambiguous between:
- `core.exception_hierarchy.ParseRecoveryError`
- `core.exceptions.ParseRecoveryError`

### `from powerrebuilder import PipelineError`
Would be ambiguous between:
- `core.exception_hierarchy.PipelineError`
- `core.exceptions.PipelineError`

### `from powerrebuilder import CodeGenerationLimitError`
Would be ambiguous between:
- `core.exception_hierarchy.CodeGenerationLimitError`
- `core.exceptions.CodeGenerationLimitError`

### `from powerrebuilder import ResourceExtractionError`
Would be ambiguous between:
- `core.exception_hierarchy.ResourceExtractionError`
- `core.exceptions.ResourceExtractionError`

### `from powerrebuilder import ConversionError`
Would be ambiguous between:
- `core.exception_hierarchy.ConversionError`
- `core.exceptions.ConversionError`

### `from powerrebuilder import ControlFlowError`
Would be ambiguous between:
- `core.exception_hierarchy.ControlFlowError`
- `core.exceptions.ControlFlowError`

### `from powerrebuilder import GrammarError`
Would be ambiguous between:
- `core.exception_hierarchy.GrammarError`
- `core.exceptions.GrammarError`

### `from powerrebuilder import LibraryCorruptedError`
Would be ambiguous between:
- `core.exception_hierarchy.LibraryCorruptedError`
- `core.exceptions.LibraryCorruptedError`

### `from powerrebuilder import StackUnderflowError`
Would be ambiguous between:
- `core.exception_hierarchy.StackUnderflowError`
- `core.exceptions.StackUnderflowError`

### `from powerrebuilder import DecompileError`
Would be ambiguous between:
- `core.exception_hierarchy.DecompileError`
- `core.exceptions.DecompileError`

### `from powerrebuilder import ASTConstructionError`
Would be ambiguous between:
- `core.exception_hierarchy.ASTConstructionError`
- `core.exceptions.ASTConstructionError`

### `from powerrebuilder import TemplateError`
Would be ambiguous between:
- `core.exception_hierarchy.TemplateError`
- `core.exceptions.TemplateError`

### `from powerrebuilder import SecurityError`
Would be ambiguous between:
- `core.exception_hierarchy.SecurityError`
- `core.exceptions.SecurityError`
- `core.security.SecurityError`

### `from powerrebuilder import FileNotFoundError`
Would be ambiguous between:
- `core.exception_hierarchy.FileNotFoundError`
- `core.exceptions.FileNotFoundError`

### `from powerrebuilder import TargetLanguageError`
Would be ambiguous between:
- `core.exception_hierarchy.TargetLanguageError`
- `core.exceptions.TargetLanguageError`

### `from powerrebuilder import CoordinatorError`
Would be ambiguous between:
- `core.exception_hierarchy.CoordinatorError`
- `core.exceptions.CoordinatorError`

### `from powerrebuilder import InvalidFileFormatError`
Would be ambiguous between:
- `core.exception_hierarchy.InvalidFileFormatError`
- `core.exceptions.InvalidFileFormatError`

### `from powerrebuilder import UntrustedInputError`
Would be ambiguous between:
- `core.exception_hierarchy.UntrustedInputError`
- `core.exceptions.UntrustedInputError`

### `from powerrebuilder import PathTraversalError`
Would be ambiguous between:
- `core.exception_hierarchy.PathTraversalError`
- `core.exceptions.PathTraversalError`
- `core.security.PathTraversalError`

### `from powerrebuilder import DecompilationLimitError`
Would be ambiguous between:
- `core.exception_hierarchy.DecompilationLimitError`
- `core.exceptions.DecompilationLimitError`

### `from powerrebuilder import DependencyError`
Would be ambiguous between:
- `core.exception_hierarchy.DependencyError`
- `core.exceptions.DependencyError`

### `from powerrebuilder import ExceptionFactory`
Would be ambiguous between:
- `core.exception_hierarchy.ExceptionFactory`
- `core.exceptions.ExceptionFactory`

### `from powerrebuilder import SemanticError`
Would be ambiguous between:
- `core.exception_hierarchy.SemanticError`
- `core.exceptions.SemanticError`

### `from powerrebuilder import ConfigurationError`
Would be ambiguous between:
- `core.exception_hierarchy.ConfigurationError`
- `core.exceptions.ConfigurationError`

### `from powerrebuilder import ParseError`
Would be ambiguous between:
- `core.exception_hierarchy.ParseError`
- `core.exceptions.ParseError`

### `from powerrebuilder import ExtractionError`
Would be ambiguous between:
- `core.exception_hierarchy.ExtractionError`
- `core.exceptions.ExtractionError`

### `from powerrebuilder import TypeResolutionError`
Would be ambiguous between:
- `core.exception_hierarchy.TypeResolutionError`
- `core.exceptions.TypeResolutionError`

### `from powerrebuilder import IPipelineState`
Would be ambiguous between:
- `contracts.interfaces.IPipelineState`
- `core.state_interfaces.IPipelineState`

### `from powerrebuilder import StageStatus`
Would be ambiguous between:
- `contracts.interfaces.StageStatus`
- `core.state_interfaces.StageStatus`

### `from powerrebuilder import IStateManager`
Would be ambiguous between:
- `contracts.interfaces.IStateManager`
- `core.state_interfaces.IStateManager`

### `from powerrebuilder import PathValidator`
Would be ambiguous between:
- `core.security.PathValidator`
- `extract.security.PathValidator`
- `extract.security.paths.PathValidator`

### `from powerrebuilder import EventType`
Would be ambiguous between:
- `contracts.interfaces.EventType`
- `core.events_interfaces.EventType`

### `from powerrebuilder import Event`
Would be ambiguous between:
- `contracts.interfaces.Event`
- `core.events_interfaces.Event`
- `model.ast.functions.Event`

### `from powerrebuilder import IEventBus`
Would be ambiguous between:
- `contracts.interfaces.IEventBus`
- `core.events_interfaces.IEventBus`

### `from powerrebuilder import IEventHandler`
Would be ambiguous between:
- `contracts.interfaces.IEventHandler`
- `core.events_interfaces.IEventHandler`

### `from powerrebuilder import ProgressTracker`
Would be ambiguous between:
- `common.pipeline.progress.ProgressTracker`
- `core.coordination_mixins.ProgressTracker`

### `from powerrebuilder import IASTProcessor`
Would be ambiguous between:
- `contracts.interfaces.IASTProcessor`
- `model.interfaces.IASTProcessor`

### `from powerrebuilder import ILogger`
Would be ambiguous between:
- `common.interface_logger.ILogger`
- `contracts.interfaces.ILogger`

### `from powerrebuilder import ITransformer`
Would be ambiguous between:
- `contracts.interfaces.ITransformer`
- `model.types.interfaces.ITransformer`

### `from powerrebuilder import IModelPersistence`
Would be ambiguous between:
- `contracts.interfaces.IModelPersistence`
- `model.interfaces.IModelPersistence`

### `from powerrebuilder import IEntityValidator`
Would be ambiguous between:
- `contracts.interfaces.IEntityValidator`
- `model.interfaces.IEntityValidator`

### `from powerrebuilder import IEntityFactory`
Would be ambiguous between:
- `contracts.interfaces.IEntityFactory`
- `model.interfaces.IEntityFactory`

### `from powerrebuilder import IParser`
Would be ambiguous between:
- `contracts.interfaces.IParser`
- `model.types.interfaces.IParser`

### `from powerrebuilder import IModelExtractor`
Would be ambiguous between:
- `contracts.interfaces.IModelExtractor`
- `model.interfaces.IModelExtractor`

### `from powerrebuilder import StandardLogger`
Would be ambiguous between:
- `common.interface_logger.StandardLogger`
- `contracts.logger.StandardLogger`

### `from powerrebuilder import DetailedLoggerAdapter`
Would be ambiguous between:
- `common.interface_logger.DetailedLoggerAdapter`
- `contracts.logger.DetailedLoggerAdapter`

### `from powerrebuilder import ResolutionContext`
Would be ambiguous between:
- `parse.resolution.ResolutionContext`
- `parse.transformer.resolver.ResolutionContext`

### `from powerrebuilder import TypeResolver`
Would be ambiguous between:
- `parse.resolution.TypeResolver`
- `parse.transformer.resolver.TypeResolver`

### `from powerrebuilder import SQLTransformer`
Would be ambiguous between:
- `parse.transformer.sql.SQLTransformer`
- `parse.transformer.sql_transformer.SQLTransformer`

### `from powerrebuilder import PBDefaultVariableNode`
Would be ambiguous between:
- `model.entities.function.PBDefaultVariableNode`
- `parse.transformer.visitors.visitor.PBDefaultVariableNode`

### `from powerrebuilder import PBEventAttributeNode`
Would be ambiguous between:
- `model.entities.event.PBEventAttributeNode`
- `parse.transformer.visitors.visitor.PBEventAttributeNode`

### `from powerrebuilder import PBArgumentsNode`
Would be ambiguous between:
- `model.entities.function.PBArgumentsNode`
- `parse.transformer.visitors.visitor.PBArgumentsNode`

### `from powerrebuilder import PBArgumentOptionNode`
Would be ambiguous between:
- `model.entities.function.PBArgumentOptionNode`
- `parse.transformer.visitors.visitor.PBArgumentOptionNode`

### `from powerrebuilder import PBArgumentNode`
Would be ambiguous between:
- `model.entities.function.PBArgumentNode`
- `parse.transformer.visitors.visitor.PBArgumentNode`

### `from powerrebuilder import ErrorRecoveryTransformer`
Would be ambiguous between:
- `parse.error_recovery.strategy.ErrorRecoveryTransformer`
- `parse.parser.powerbuilder.ErrorRecoveryTransformer`

### `from powerrebuilder import Identifier`
Would be ambiguous between:
- `model.ast.literals.Identifier`
- `model.types.base.Identifier`

### `from powerrebuilder import Variable`
Would be ambiguous between:
- `generate.converters.utils.ast.Variable`
- `model.types.base.Variable`

### `from powerrebuilder import Parameter`
Would be ambiguous between:
- `model.ast.functions.Parameter`
- `model.types.base.Parameter`

### `from powerrebuilder import PBGlobalVariable`
Would be ambiguous between:
- `model.entities.function.PBGlobalVariable`
- `model.system.globals.PBGlobalVariable`

### `from powerrebuilder import StringLiteral`
Would be ambiguous between:
- `model.ast.literals.StringLiteral`
- `model.expressions.ast_expressions.StringLiteral`

### `from powerrebuilder import RealLiteral`
Would be ambiguous between:
- `model.ast.literals.RealLiteral`
- `model.expressions.ast_expressions.RealLiteral`

### `from powerrebuilder import NullLiteral`
Would be ambiguous between:
- `model.ast.literals.NullLiteral`
- `model.expressions.ast_expressions.NullLiteral`

### `from powerrebuilder import BooleanLiteral`
Would be ambiguous between:
- `model.ast.literals.BooleanLiteral`
- `model.expressions.ast_expressions.BooleanLiteral`

### `from powerrebuilder import ExistsExpression`
Would be ambiguous between:
- `model.ast.additional_nodes.ExistsExpression`
- `model.expressions.ast_expressions.ExistsExpression`

### `from powerrebuilder import IntegerLiteral`
Would be ambiguous between:
- `model.ast.literals.IntegerLiteral`
- `model.expressions.ast_expressions.IntegerLiteral`

### `from powerrebuilder import UnaryExpression`
Would be ambiguous between:
- `model.ast.literals.UnaryExpression`
- `model.expressions.ast_expressions.UnaryExpression`

### `from powerrebuilder import BetweenExpression`
Would be ambiguous between:
- `model.ast.additional_nodes.BetweenExpression`
- `model.expressions.ast_expressions.BetweenExpression`

### `from powerrebuilder import LikeExpression`
Would be ambiguous between:
- `model.ast.additional_nodes.LikeExpression`
- `model.expressions.ast_expressions.LikeExpression`

### `from powerrebuilder import LambdaExpression`
Would be ambiguous between:
- `model.ast.functions.LambdaExpression`
- `model.expressions.ast_expressions.LambdaExpression`

### `from powerrebuilder import BinaryExpression`
Would be ambiguous between:
- `model.ast.literals.BinaryExpression`
- `model.expressions.ast_expressions.BinaryExpression`

### `from powerrebuilder import InExpression`
Would be ambiguous between:
- `model.ast.additional_nodes.InExpression`
- `model.expressions.ast_expressions.InExpression`

### `from powerrebuilder import PBFunctionCall`
Would be ambiguous between:
- `model.entities.function.PBFunctionCall`
- `model.expressions.pb_expressions.PBFunctionCall`

### `from powerrebuilder import PBVariable`
Would be ambiguous between:
- `model.entities.function.PBVariable`
- `model.expressions.pb_expressions.PBVariable`

### `from powerrebuilder import Scope`
Would be ambiguous between:
- `model.symbols.scope.Scope`
- `model.symbols.table.Scope`

### `from powerrebuilder import PBSourcedEntity`
Would be ambiguous between:
- `model.ast.pb_types.PBSourcedEntity`
- `model.base.pb_entity.PBSourcedEntity`

### `from powerrebuilder import ServiceGenerator`
Would be ambiguous between:
- `generate.coordinators.service.ServiceGenerator`
- `generate.service.ServiceGenerator`

### `from powerrebuilder import ModelGenerator`
Would be ambiguous between:
- `generate.coordinators.model.ModelGenerator`
- `generate.models.ModelGenerator`

### `from powerrebuilder import FlutterGenerator`
Would be ambiguous between:
- `generate.coordinators.flutter.FlutterGenerator`
- `generate.flutter.FlutterGenerator`

### `from powerrebuilder import ValidationRule`
Would be ambiguous between:
- `generate.converters.flutter.dw_enhancements.ValidationRule`
- `generate.schemas.ValidationRule`

### `from powerrebuilder import RelationshipType`
Would be ambiguous between:
- `generate.converters.data.relationships.RelationshipType`
- `generate.schemas.RelationshipType`

### `from powerrebuilder import CodeGenerator`
Would be ambiguous between:
- `generate.base.CodeGenerator`
- `generate.templates.python.python.CodeGenerator`

### `from powerrebuilder import TypeConverter`
Would be ambiguous between:
- `generate.converters.flutter.models.TypeConverter`
- `generate.converters.utils.types.TypeConverter`

### `from powerrebuilder import DesignSystemConverter`
Would be ambiguous between:
- `generate.converters.flutter.design_system.DesignSystemConverter`
- `generate.converters.flutter.themes.DesignSystemConverter`

### `from powerrebuilder import DatabaseOperationFormatter`
Would be ambiguous between:
- `generate.converters.data.db_formatter.DatabaseOperationFormatter`
- `generate.converters.flutter.api.DatabaseOperationFormatter`

### `from powerrebuilder import ExtractCoordinator`
Would be ambiguous between:
- `extract.coordinator.ExtractCoordinator`
- `extract.security.ExtractCoordinator`
- `extract.security.security_coordinator.ExtractCoordinator`

### `from powerrebuilder import ResourceExtractionManager`
Would be ambiguous between:
- `extract.pbd.binary.ResourceExtractionManager`
- `extract.pbd.manager.ResourceExtractionManager`
- `extract.pbd.res_manager.ResourceExtractionManager`

### `from powerrebuilder import EnhancedImageExtractor`
Would be ambiguous between:
- `extract.pbd.binary.EnhancedImageExtractor`
- `extract.pbd.images.EnhancedImageExtractor`

### `from powerrebuilder import StringResourceExtractor`
Would be ambiguous between:
- `extract.pbd.binary.StringResourceExtractor`
- `extract.pbd.strings.StringResourceExtractor`

### `from powerrebuilder import PbEntryDefinition`
Would be ambiguous between:
- `extract.pbd.data_block.PbEntryDefinition`
- `extract.pbd.entry.PbEntryDefinition`

### `from powerrebuilder import create_model_coordinator`
Would be ambiguous between:
- `core.dependency_injection.create_model_coordinator`
- `model.factory.create_model_coordinator`

### `from powerrebuilder import create_generate_coordinator`
Would be ambiguous between:
- `core.dependency_injection.create_generate_coordinator`
- `generate.factory.create_generate_coordinator`

### `from powerrebuilder import get_error_description`
Would be ambiguous between:
- `core.exception_hierarchy.get_error_description`
- `core.exceptions.get_error_description`

### `from powerrebuilder import sanitize_filename`
Would be ambiguous between:
- `common.utils.sanitize_filename`
- `core.security.sanitize_filename`

### `from powerrebuilder import load_grammar`
Would be ambiguous between:
- `parse.grammar.loader.load_grammar`
- `parse.utils.loader.load_grammar`

### `from powerrebuilder import format_timestamp`
Would be ambiguous between:
- `common.utils.format_timestamp`
- `common.utils.files.format_timestamp`

### `from powerrebuilder import filter_dict`
Would be ambiguous between:
- `common.utils.filter_dict`
- `common.utils.collections.filter_dict`

### `from powerrebuilder import ensure_directory`
Would be ambiguous between:
- `common.utils.ensure_directory`
- `common.utils.files.ensure_directory`

### `from powerrebuilder import camel_to_snake`
Would be ambiguous between:
- `common.utils.camel_to_snake`
- `common.utils.strings.camel_to_snake`
- `model.utils.common.camel_to_snake`

### `from powerrebuilder import get_file_extension`
Would be ambiguous between:
- `common.utils.get_file_extension`
- `common.utils.files.get_file_extension`

### `from powerrebuilder import merge_dicts`
Would be ambiguous between:
- `common.utils.merge_dicts`
- `common.utils.collections.merge_dicts`

### `from powerrebuilder import read_file_safe`
Would be ambiguous between:
- `common.utils.read_file_safe`
- `common.utils.files.read_file_safe`

### `from powerrebuilder import normalize_path`
Would be ambiguous between:
- `common.utils.normalize_path`
- `common.utils.files.normalize_path`

### `from powerrebuilder import pluralize`
Would be ambiguous between:
- `common.utils.pluralize`
- `common.utils.strings.pluralize`

### `from powerrebuilder import truncate`
Would be ambiguous between:
- `common.utils.truncate`
- `common.utils.strings.truncate`

### `from powerrebuilder import snake_to_camel`
Would be ambiguous between:
- `common.utils.snake_to_camel`
- `common.utils.strings.snake_to_camel`

### `from powerrebuilder import find_duplicates`
Would be ambiguous between:
- `common.utils.find_duplicates`
- `common.utils.collections.find_duplicates`

### `from powerrebuilder import chunk_list`
Would be ambiguous between:
- `common.utils.chunk_list`
- `common.utils.collections.chunk_list`

### `from powerrebuilder import _is_file_handle`
Would be ambiguous between:
- `extract.pbd.scanner._is_file_handle`
- `extract.utils.binary._is_file_handle`

### `from powerrebuilder import get_bmp_size`
Would be ambiguous between:
- `extract.pbd.io.get_bmp_size`
- `extract.pbd.reader.get_bmp_size`

### `from powerrebuilder import get_ico_size`
Would be ambiguous between:
- `extract.pbd.io.get_ico_size`
- `extract.pbd.reader.get_ico_size`