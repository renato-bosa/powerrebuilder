//! Conservative whole-function comparison against exported PowerBuilder source.
//!
//! This intentionally performs normalized statement comparison followed by a
//! narrowly-scoped, syntax-directed semantic canonicalization, never fuzzy
//! matching. The evidence records which comparison proved a complete function.
//! A mismatch means "not proven by this comparator", not necessarily that the
//! reconstruction is behaviorally different.

use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

use super::semantic_preview::{
    FunctionComparisonEvidence, FunctionComparisonResult, FunctionVerificationBasis,
    SemanticPreview, VerificationStatus,
};

pub const COMPARISON_METHOD: &str = "normalized_then_safe_semantic_v2";

#[derive(Debug, Clone)]
pub struct KnownSourceCatalog {
    routines_by_object: HashMap<String, Vec<SourceRoutine>>,
    pub source_file_count: usize,
    pub routine_count: usize,
}

#[derive(Debug, Clone)]
struct SourceRoutine {
    name: String,
    parameter_types: Vec<String>,
    source_reference: String,
    normalized_body: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct RoutineIdentity {
    name: String,
    parameter_types: Vec<String>,
}

impl KnownSourceCatalog {
    pub fn load(root: &Path) -> Result<Self, String> {
        if !root.is_dir() {
            return Err(format!(
                "known-source directory does not exist: {}",
                root.display()
            ));
        }
        let mut files = Vec::new();
        collect_source_files(root, &mut files)?;
        let mut routines_by_object = HashMap::<String, Vec<SourceRoutine>>::new();
        let mut routine_count = 0;
        for path in &files {
            let bytes = fs::read(path)
                .map_err(|error| format!("failed to read {}: {error}", path.display()))?;
            let source = String::from_utf8_lossy(&bytes);
            let routines = parse_source_routines(&source, path);
            routine_count += routines.len();
            let Some(stem) = path.file_stem().and_then(|stem| stem.to_str()) else {
                continue;
            };
            routines_by_object
                .entry(stem.to_ascii_lowercase())
                .or_default()
                .extend(routines);
        }
        Ok(Self {
            routines_by_object,
            source_file_count: files.len(),
            routine_count,
        })
    }

    pub fn compare(
        &self,
        entry_name: &str,
        routine_occurrence: usize,
        preview: &mut SemanticPreview,
    ) {
        let object_name = entry_name
            .rsplit_once('.')
            .map_or(entry_name, |(stem, _)| stem)
            .to_ascii_lowercase();
        let reconstructed = normalized_preview_body(&preview.powerscript_like);
        let mut evidence = FunctionComparisonEvidence {
            method: COMPARISON_METHOD,
            verification_basis: None,
            source_reference: None,
            result: FunctionComparisonResult::SourceFileNotFound,
            normalized_source_statements: 0,
            normalized_reconstructed_statements: reconstructed.len(),
        };

        let Some(routines) = self.routines_by_object.get(&object_name) else {
            preview.evidence.function_comparison = Some(evidence);
            return;
        };
        let Some(identity) = parse_routine_identity(&preview.signature, false) else {
            evidence.result = FunctionComparisonResult::SourceRoutineNotFound;
            preview.evidence.function_comparison = Some(evidence);
            return;
        };
        let candidates = routines
            .iter()
            .filter(|routine| {
                routine.name == identity.name
                    && (routine.parameter_types == identity.parameter_types
                        || routine.parameter_types.is_empty())
            })
            .collect::<Vec<_>>();
        let routine = match candidates.as_slice() {
            [] => {
                evidence.result = FunctionComparisonResult::SourceRoutineNotFound;
                preview.evidence.function_comparison = Some(evidence);
                return;
            }
            [routine] => *routine,
            _ if routine_occurrence < candidates.len() => candidates[routine_occurrence],
            _ => {
                evidence.result = FunctionComparisonResult::AmbiguousSourceRoutine;
                preview.evidence.function_comparison = Some(evidence);
                return;
            }
        };

        evidence.source_reference = Some(routine.source_reference.clone());
        evidence.normalized_source_statements = routine.normalized_body.len();
        if !preview.evidence.semantic_rules_complete {
            evidence.result = FunctionComparisonResult::SemanticRulesIncomplete;
        } else if reconstructed == routine.normalized_body {
            evidence.result = FunctionComparisonResult::Verified;
            evidence.verification_basis = Some(FunctionVerificationBasis::NormalizedEquality);
            preview.evidence.function_reconstruction = VerificationStatus::Verified;
        } else if safe_canonical_body(&reconstructed)
            == safe_canonical_body(&routine.normalized_body)
        {
            evidence.result = FunctionComparisonResult::Verified;
            evidence.verification_basis =
                Some(FunctionVerificationBasis::SafeSemanticCanonicalization);
            preview.evidence.function_reconstruction = VerificationStatus::Verified;
        } else {
            evidence.result = FunctionComparisonResult::NormalizedBodyMismatch;
            preview.evidence.function_reconstruction = VerificationStatus::Mismatch;
        }
        preview.evidence.function_comparison = Some(evidence);
    }
}

fn collect_source_files(directory: &Path, files: &mut Vec<PathBuf>) -> Result<(), String> {
    for entry in fs::read_dir(directory)
        .map_err(|error| format!("failed to enumerate {}: {error}", directory.display()))?
    {
        let path = entry
            .map_err(|error| format!("failed to enumerate {}: {error}", directory.display()))?
            .path();
        if path.is_dir() {
            collect_source_files(&path, files)?;
        } else if path
            .extension()
            .and_then(|extension| extension.to_str())
            .is_some_and(|extension| {
                matches!(
                    extension.to_ascii_lowercase().as_str(),
                    "sra" | "srf" | "srm" | "sru" | "srw"
                )
            })
        {
            files.push(path);
        }
    }
    Ok(())
}

fn parse_source_routines(source: &str, path: &Path) -> Vec<SourceRoutine> {
    let lines = source.lines().collect::<Vec<_>>();
    let mut routines = Vec::new();
    let mut index = 0;
    let mut in_prototypes = false;
    while index < lines.len() {
        let line = lines[index];
        let trimmed = line.trim();
        if trimmed.eq_ignore_ascii_case("type prototypes")
            || trimmed.eq_ignore_ascii_case("forward prototypes")
        {
            in_prototypes = true;
            index += 1;
            continue;
        }
        if in_prototypes {
            if trimmed.eq_ignore_ascii_case("end prototypes") {
                in_prototypes = false;
            }
            index += 1;
            continue;
        }
        let Some((identity, terminator, inline_body)) = parse_source_header(line) else {
            index += 1;
            continue;
        };
        let start_line = index + 1;
        let mut body = String::new();
        if !inline_body.is_empty() {
            body.push_str(inline_body);
            body.push('\n');
        }
        index += 1;
        while index < lines.len() && !lines[index].trim().eq_ignore_ascii_case(terminator) {
            body.push_str(lines[index]);
            body.push('\n');
            index += 1;
        }
        if index == lines.len() {
            continue;
        }
        routines.push(SourceRoutine {
            name: identity.name,
            parameter_types: identity.parameter_types,
            source_reference: format!("{}:{start_line}", path.display()),
            normalized_body: normalize_body(&body),
        });
        index += 1;
    }
    routines
}

fn parse_source_header(line: &str) -> Option<(RoutineIdentity, &'static str, &str)> {
    let trimmed = line.trim_start();
    let lower = trimmed.to_ascii_lowercase();
    if lower.starts_with("on ") {
        let owner_and_name = trimmed[3..].trim();
        let name = owner_and_name
            .rsplit_once('.')
            .map_or(owner_and_name, |(_, name)| name)
            .trim()
            .to_ascii_lowercase();
        return Some((
            RoutineIdentity {
                name,
                parameter_types: Vec::new(),
            },
            "end on",
            "",
        ));
    }

    let (header, inline_body) = split_first_semicolon(trimmed)?;
    let header_lower = header.to_ascii_lowercase();
    let (terminator, require_parameters) = if header_lower.starts_with("event ") {
        ("end event", false)
    } else if contains_word(&header_lower, "function") {
        ("end function", true)
    } else if contains_word(&header_lower, "subroutine") {
        ("end subroutine", true)
    } else {
        return None;
    };
    let identity = parse_routine_identity(header, require_parameters)?;
    Some((identity, terminator, inline_body))
}

fn parse_routine_identity(header: &str, require_parameters: bool) -> Option<RoutineIdentity> {
    let lower = header.trim().to_ascii_lowercase();
    if lower.starts_with("event ") {
        // PB permits both `event control::clicked (...)` and
        // `event type string pfc_value (...)`.  In either form, the routine
        // name is the final token before the parameter list.
        let before_parameters = lower[6..].split(['(', ';']).next()?.trim();
        let raw_name = before_parameters
            .split_whitespace()
            .last()?
            .rsplit_once("::")
            .map_or(
                before_parameters.split_whitespace().last().unwrap(),
                |(_, name)| name,
            )
            .to_string();
        let parameter_types = parse_parameter_types(&lower).unwrap_or_default();
        return Some(RoutineIdentity {
            name: raw_name,
            parameter_types,
        });
    }

    for keyword in ["function", "subroutine"] {
        let Some(position) = word_position(&lower, keyword) else {
            continue;
        };
        let after = lower[position + keyword.len()..].trim_start();
        let open = after.find('(')?;
        let before_open = after[..open].trim();
        let name = before_open.split_whitespace().last()?.to_string();
        let parameter_types = parse_parameter_types(after)?;
        return Some(RoutineIdentity {
            name,
            parameter_types,
        });
    }
    (!require_parameters).then(|| RoutineIdentity {
        name: lower,
        parameter_types: Vec::new(),
    })
}

fn parse_parameter_types(header: &str) -> Option<Vec<String>> {
    let open = header.find('(')?;
    let close = header.rfind(')')?;
    let parameters = &header[open + 1..close];
    if parameters.trim().is_empty() {
        return Some(Vec::new());
    }
    parameters
        .split(',')
        .map(|parameter| {
            parameter
                .split_whitespace()
                .find(|word| !matches!(*word, "ref" | "readonly"))
                .map(normalize_type_name)
        })
        .collect()
}

fn normalize_type_name(name: &str) -> String {
    match name.trim().to_ascii_lowercase().as_str() {
        "int" => "integer".to_string(),
        "bool" => "boolean".to_string(),
        "unsignedinteger" => "uint".to_string(),
        "unsignedlong" => "ulong".to_string(),
        "character" => "char".to_string(),
        other => other.to_string(),
    }
}

fn normalized_preview_body(preview: &str) -> Vec<String> {
    let mut lines = preview.lines();
    lines.next();
    let mut body = lines.collect::<Vec<_>>();
    if body.last().is_some_and(|line| line.trim() == "end") {
        body.pop();
    }
    normalize_body(&body.join("\n"))
}

fn normalize_body(body: &str) -> Vec<String> {
    let without_comments = strip_comments(body);
    let joined_continuations = join_continuations(&without_comments);
    let mut statements = split_statements(&joined_continuations)
        .into_iter()
        .map(|statement| normalize_statement(&statement))
        .filter(|statement| !statement.is_empty())
        .collect::<Vec<_>>();
    while statements
        .last()
        .is_some_and(|statement| statement == "return")
    {
        statements.pop();
    }
    statements
}

/// Canonicalizes only PowerScript forms for which this oracle has a local,
/// syntax-directed equivalence proof. It deliberately does not reorder
/// expressions, fold constants, infer omitted source, or rewrite the preview.
fn safe_canonical_body(statements: &[String]) -> Vec<String> {
    let mut canonical = Vec::new();
    for statement in statements {
        if let Some((header, body)) = split_inline_if(statement) {
            canonical.push(canonicalize_safe_statement(&header));
            canonical.push(canonicalize_safe_statement(&body));
            canonical.push("endif".to_string());
        } else if let Some(declarations) = split_grouped_declaration(statement) {
            canonical.extend(declarations);
        } else {
            canonical.push(canonicalize_safe_statement(statement));
        }
    }
    canonical
}

fn canonicalize_safe_statement(statement: &str) -> String {
    let canonical = if let Some(expression) = unwrap_keyword_expression(statement, "return") {
        format!("return{expression}")
    } else if let Some(expression) = unwrap_keyword_expression(statement, "destroy") {
        format!("destroy{expression}")
    } else if statement.starts_with("if") && statement.ends_with("then") {
        let condition = &statement[2..statement.len() - 4];
        format!("if{}then", strip_safe_boolean_groups(condition))
    } else {
        statement.to_string()
    };
    canonicalize_string_delimiters(&canonical)
}

fn canonicalize_string_delimiters(statement: &str) -> String {
    let mut output = String::with_capacity(statement.len());
    let mut delimiter = None;
    let mut escaped = false;
    for character in statement.chars() {
        if let Some(quote) = delimiter {
            if escaped {
                output.push(character);
                escaped = false;
            } else if character == '~' {
                output.push(character);
                escaped = true;
            } else if character == quote {
                output.push('"');
                delimiter = None;
            } else {
                output.push(character);
            }
        } else if matches!(character, '\'' | '"') {
            delimiter = Some(character);
            output.push('"');
        } else {
            output.push(character);
        }
    }
    output
}

fn split_inline_if(statement: &str) -> Option<(String, String)> {
    if !statement.starts_with("if") {
        return None;
    }
    let matches = find_all_outside_string(statement, "then", 2);
    let [then] = matches.as_slice() else {
        return None;
    };
    let body_start = then + 4;
    (body_start < statement.len()).then(|| {
        (
            statement[..body_start].to_string(),
            statement[body_start..].to_string(),
        )
    })
}

fn unwrap_keyword_expression<'a>(statement: &'a str, keyword: &str) -> Option<&'a str> {
    let rest = statement.strip_prefix(keyword)?;
    if !rest.starts_with('(') || matching_parenthesis(rest, 0)? != rest.len() - 1 {
        return None;
    }
    Some(&rest[1..rest.len() - 1])
}

fn split_grouped_declaration(statement: &str) -> Option<Vec<String>> {
    const TYPES: &[&str] = &[
        "datetime", "decimal", "boolean", "integer", "string", "double", "ulong", "uint", "long",
        "real", "blob", "byte", "char", "date", "time", "any",
    ];
    let type_name = TYPES
        .iter()
        .find(|type_name| statement.starts_with(**type_name))?;
    let names = &statement[type_name.len()..];
    if !names.contains(',')
        || names.split(',').any(|name| {
            name.is_empty() || !name.chars().all(|c| c.is_ascii_alphanumeric() || c == '_')
        })
    {
        return None;
    }
    Some(
        names
            .split(',')
            .map(|name| format!("{type_name}{name}"))
            .collect(),
    )
}

fn strip_safe_boolean_groups(condition: &str) -> String {
    let mut output = condition.to_string();
    loop {
        let mut stack = Vec::new();
        let mut candidate = None;
        let mut delimiter = None;
        let mut escaped = false;
        for (index, character) in output.char_indices() {
            if let Some(quote) = delimiter {
                if escaped {
                    escaped = false;
                } else if character == '~' {
                    escaped = true;
                } else if character == quote {
                    delimiter = None;
                }
                continue;
            }
            if matches!(character, '\'' | '"') {
                delimiter = Some(character);
            } else if character == '(' {
                stack.push(index);
            } else if character == ')' {
                let Some(open) = stack.pop() else { continue };
                let previous = output[..open].chars().next_back();
                let left = &output[..open];
                if previous.is_some_and(is_word_character)
                    && !left.ends_with("and")
                    && !left.ends_with("or")
                {
                    continue;
                }
                let inside = &output[open + 1..index];
                let right = &output[index + 1..];
                if boolean_group_is_redundant(inside, left, right) {
                    candidate = Some((open, index));
                    break;
                }
            }
        }
        let Some((open, close)) = candidate else {
            break;
        };
        output.remove(close);
        output.remove(open);
    }
    output
}

fn boolean_group_is_redundant(inside: &str, left: &str, right: &str) -> bool {
    let left_op = ["and", "or"].into_iter().find(|op| left.ends_with(op));
    let right_op = ["and", "or"].into_iter().find(|op| right.starts_with(op));
    let operand_context =
        (left.is_empty() || left_op.is_some()) && (right.is_empty() || right_op.is_some());
    if !operand_context {
        return false;
    }
    if has_top_level_comparison(inside) && top_level_logical_root(inside).is_none() {
        return true;
    }
    let Some(root) = top_level_logical_root(inside) else {
        return false;
    };
    left_op.is_none_or(|op| op == root) && right_op.is_none_or(|op| op == root)
}

fn top_level_logical_root(expression: &str) -> Option<&'static str> {
    for operator in ["or", "and"] {
        let mut offset = 0;
        while let Some(relative) = expression[offset..].find(operator) {
            let position = offset + relative;
            let left = &expression[..position];
            let right = &expression[position + operator.len()..];
            if has_top_level_comparison(left) && has_top_level_comparison(right) {
                return Some(operator);
            }
            offset = position + operator.len();
        }
    }
    None
}

fn has_top_level_comparison(expression: &str) -> bool {
    let mut depth = 0usize;
    let mut delimiter = None;
    let mut escaped = false;
    for character in expression.chars() {
        if let Some(quote) = delimiter {
            if escaped {
                escaped = false;
            } else if character == '~' {
                escaped = true;
            } else if character == quote {
                delimiter = None;
            }
        } else if matches!(character, '\'' | '"') {
            delimiter = Some(character);
        } else if character == '(' {
            depth += 1;
        } else if character == ')' {
            depth = depth.saturating_sub(1);
        } else if depth == 0 && matches!(character, '=' | '<' | '>') {
            return true;
        }
    }
    false
}

fn matching_parenthesis(source: &str, open: usize) -> Option<usize> {
    let mut depth = 0usize;
    let mut delimiter = None;
    let mut escaped = false;
    for (index, character) in source.char_indices().skip_while(|(index, _)| *index < open) {
        if let Some(quote) = delimiter {
            if escaped {
                escaped = false;
            } else if character == '~' {
                escaped = true;
            } else if character == quote {
                delimiter = None;
            }
        } else if matches!(character, '\'' | '"') {
            delimiter = Some(character);
        } else if character == '(' {
            depth += 1;
        } else if character == ')' {
            depth = depth.checked_sub(1)?;
            if depth == 0 {
                return Some(index);
            }
        }
    }
    None
}

fn find_all_outside_string(source: &str, needle: &str, start: usize) -> Vec<usize> {
    let mut matches = Vec::new();
    let mut delimiter = None;
    let mut escaped = false;
    for (index, character) in source.char_indices() {
        if let Some(quote) = delimiter {
            if escaped {
                escaped = false;
            } else if character == '~' {
                escaped = true;
            } else if character == quote {
                delimiter = None;
            }
        } else if matches!(character, '\'' | '"') {
            delimiter = Some(character);
        } else if index >= start && source[index..].starts_with(needle) {
            matches.push(index);
        }
    }
    matches
}

fn strip_comments(source: &str) -> String {
    let characters = source.chars().collect::<Vec<_>>();
    let mut output = String::with_capacity(source.len());
    let mut index = 0;
    let mut string_delimiter = None;
    let mut escaped = false;
    let mut line_comment = false;
    let mut block_comment = false;
    while index < characters.len() {
        let current = characters[index];
        let next = characters.get(index + 1).copied();
        if line_comment {
            if current == '\n' {
                line_comment = false;
                output.push(current);
            }
        } else if block_comment {
            if current == '*' && next == Some('/') {
                block_comment = false;
                index += 1;
            } else if current == '\n' {
                output.push(current);
            }
        } else if let Some(delimiter) = string_delimiter {
            output.push(current);
            if escaped {
                escaped = false;
            } else if current == '~' {
                escaped = true;
            } else if current == delimiter {
                string_delimiter = None;
            }
        } else if matches!(current, '\'' | '"') {
            string_delimiter = Some(current);
            output.push(current);
        } else if current == '/' && next == Some('/') {
            line_comment = true;
            index += 1;
        } else if current == '/' && next == Some('*') {
            block_comment = true;
            index += 1;
        } else {
            output.push(current);
        }
        index += 1;
    }
    output
}

fn join_continuations(source: &str) -> String {
    let mut output = String::with_capacity(source.len());
    let mut string_delimiter = None;
    let mut escaped = false;
    let mut continuation = false;
    for character in source.chars() {
        if continuation {
            if character.is_whitespace() {
                continue;
            }
            continuation = false;
        }
        if let Some(delimiter) = string_delimiter {
            output.push(character);
            if escaped {
                escaped = false;
            } else if character == '~' {
                escaped = true;
            } else if character == delimiter {
                string_delimiter = None;
            }
        } else if matches!(character, '\'' | '"') {
            string_delimiter = Some(character);
            output.push(character);
        } else if character == '&' {
            continuation = true;
        } else {
            output.push(character);
        }
    }
    output
}

fn split_statements(source: &str) -> Vec<String> {
    let mut statements = Vec::new();
    let mut current = String::new();
    let mut string_delimiter = None;
    let mut escaped = false;
    for character in source.chars() {
        if let Some(delimiter) = string_delimiter {
            current.push(character);
            if escaped {
                escaped = false;
            } else if character == '~' {
                escaped = true;
            } else if character == delimiter {
                string_delimiter = None;
            }
        } else if matches!(character, '\'' | '"') {
            string_delimiter = Some(character);
            current.push(character);
        } else if matches!(character, '\n' | '\r' | ';') {
            if !current.trim().is_empty() {
                statements.push(std::mem::take(&mut current));
            } else {
                current.clear();
            }
        } else {
            current.push(character);
        }
    }
    if !current.trim().is_empty() {
        statements.push(current);
    }
    statements
}

fn normalize_statement(statement: &str) -> String {
    let mut output = String::with_capacity(statement.len());
    let mut word = String::new();
    let mut string_delimiter = None;
    let mut escaped = false;
    let flush_word = |word: &mut String, output: &mut String| {
        if !word.is_empty() {
            output.push_str(&normalize_type_name(word));
            word.clear();
        }
    };
    for character in statement.chars() {
        if string_delimiter.is_none() && matches!(character, '\'' | '"') {
            flush_word(&mut word, &mut output);
            string_delimiter = Some(character);
            output.push(character);
        } else if let Some(delimiter) = string_delimiter {
            if escaped {
                output.push(character);
                escaped = false;
            } else if character == '~' {
                output.push(character);
                escaped = true;
            } else if character == delimiter {
                string_delimiter = None;
                output.push(character);
            } else {
                output.extend(character.to_lowercase());
            }
        } else if character.is_alphanumeric() || character == '_' || character == '\u{0001}' {
            word.extend(character.to_lowercase());
        } else {
            flush_word(&mut word, &mut output);
            if !character.is_whitespace() {
                output.push(character);
            }
        }
    }
    flush_word(&mut word, &mut output);
    output.replace("this.", "")
}

fn split_first_semicolon(line: &str) -> Option<(&str, &str)> {
    let mut string_delimiter = None;
    let mut escaped = false;
    for (index, character) in line.char_indices() {
        if let Some(delimiter) = string_delimiter {
            if escaped {
                escaped = false;
            } else if character == '~' {
                escaped = true;
            } else if character == delimiter {
                string_delimiter = None;
            }
        } else if matches!(character, '\'' | '"') {
            string_delimiter = Some(character);
        } else if character == ';' {
            return Some((&line[..index], &line[index + 1..]));
        }
    }
    None
}

fn contains_word(source: &str, word: &str) -> bool {
    word_position(source, word).is_some()
}

fn word_position(source: &str, word: &str) -> Option<usize> {
    source.match_indices(word).find_map(|(position, _)| {
        let before = source[..position].chars().next_back();
        let after = source[position + word.len()..].chars().next();
        (!before.is_some_and(is_word_character) && !after.is_some_and(is_word_character))
            .then_some(position)
    })
}

fn is_word_character(character: char) -> bool {
    character.is_alphanumeric() || character == '_'
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::pb::semantic_cfg::SemanticControlFlow;
    use crate::pb::semantic_preview::SemanticEvidence;

    fn preview(body: &str, semantic_rules_complete: bool) -> SemanticPreview {
        let signature = "public function long of_value(integer ai_value)";
        SemanticPreview {
            signature: signature.to_string(),
            declarations: Vec::new(),
            statements: Vec::new(),
            instruction_count: 1,
            supported_instruction_count: usize::from(semantic_rules_complete),
            semantic_coverage_percent: if semantic_rules_complete { 100.0 } else { 0.0 },
            semantically_complete: semantic_rules_complete,
            evidence: SemanticEvidence {
                instructions_structurally_decoded: true,
                control_flow_validated: true,
                semantic_rules_complete,
                known_source_constructs: Vec::new(),
                function_reconstruction: VerificationStatus::NotAssessed,
                function_comparison: None,
                object_recompilation: VerificationStatus::NotAssessed,
            },
            control_flow: SemanticControlFlow {
                valid: true,
                errors: Vec::new(),
                blocks: Vec::new(),
                edges: Vec::new(),
                exception_regions: Vec::new(),
            },
            reconstructed_ifs: Vec::new(),
            try_catch_structures: Vec::new(),
            unresolved: Vec::new(),
            powerscript_like: format!("{signature}\n{body}\nend"),
        }
    }

    fn catalog_with_value_body(body: &str) -> KnownSourceCatalog {
        KnownSourceCatalog {
            routines_by_object: HashMap::from([(
                "object".to_string(),
                vec![SourceRoutine {
                    name: "of_value".to_string(),
                    parameter_types: vec!["integer".to_string()],
                    source_reference: "object.sru:1".to_string(),
                    normalized_body: normalize_body(body),
                }],
            )]),
            source_file_count: 1,
            routine_count: 1,
        }
    }

    #[test]
    fn parses_functions_events_and_on_handlers_without_forward_prototypes() {
        let source = r#"
type prototypes
function ulong api_call() library 'x.dll' alias for 'api;ansi'
end prototypes
forward prototypes
public function long of_value (integer ai_value)
end prototypes
public function long of_value (integer ai_value);return ai_value
end function
event dw_1::clicked;call super::clicked;this.TriggerEvent ( "ue_changed" )
end event
event type string pfc_value(string as_value);return as_value
end event
on object.create
call super::create
end on
"#;
        let routines = parse_source_routines(source, Path::new("object.sru"));

        assert_eq!(routines.len(), 4);
        assert_eq!(routines[0].name, "of_value");
        assert_eq!(routines[0].parameter_types, vec!["integer"]);
        assert_eq!(routines[1].name, "clicked");
        assert_eq!(routines[2].name, "pfc_value");
        assert_eq!(routines[2].parameter_types, vec!["string"]);
        assert_eq!(routines[3].name, "create");
    }

    #[test]
    fn normalizes_powerbuilder_type_aliases() {
        assert_eq!(normalize_type_name("unsignedinteger"), "uint");
        assert_eq!(normalize_type_name("unsignedlong"), "ulong");
        assert_eq!(normalize_type_name("character"), "char");
    }

    #[test]
    fn normalizes_only_documented_superficial_differences() {
        let source = r#"
// comment
int li_rc
li_rc = this.of_value ( 1 ) + &
    2
return
"#;
        let reconstructed = r#"
integer li_rc
li_rc = of_value(1) + 2
return
"#;

        assert_eq!(normalize_body(source), normalize_body(reconstructed));
    }

    #[test]
    fn normalizes_single_and_double_quoted_strings_without_splitting_contents() {
        let single = "ls_value = 'Security Scanner; // literal'";
        let double = "ls_value = \"Security Scanner; // literal\"";

        assert_ne!(normalize_body(single), normalize_body(double));
        assert_eq!(normalize_body(single).len(), 1);
        assert_eq!(
            safe_canonical_body(&normalize_body(single)),
            safe_canonical_body(&normalize_body(double))
        );
    }

    #[test]
    fn safely_canonicalizes_inline_if_and_block_if() {
        let inline = normalize_body("if ai_value < 0 then return -1");
        let block = normalize_body("if ai_value < 0 then\nreturn -1\nend if");

        assert_ne!(inline, block);
        assert_eq!(safe_canonical_body(&inline), safe_canonical_body(&block));
    }

    #[test]
    fn safely_canonicalizes_redundant_boolean_operand_parentheses() {
        let source =
            normalize_body("if IsNull(as_value) or Len(as_value) = 0 then\nreturn -1\nend if");
        let reconstructed =
            normalize_body("if IsNull(as_value) or (Len(as_value) = 0) then\nreturn -1\nend if");
        let associated_source = normalize_body(
            "if IsNull(ai_style) or (ai_style > 1 or ai_style < 0) then\nreturn -1\nend if",
        );
        let associated_reconstructed = normalize_body(
            "if IsNull(ai_style) or (ai_style > 1) or (ai_style < 0) then\nreturn -1\nend if",
        );

        assert_eq!(
            safe_canonical_body(&source),
            safe_canonical_body(&reconstructed)
        );
        assert_eq!(
            safe_canonical_body(&associated_source),
            safe_canonical_body(&associated_reconstructed)
        );
    }

    #[test]
    fn safely_canonicalizes_grouped_declarations_and_keyword_parentheses() {
        let source =
            normalize_body("string ls_first, ls_second\nreturn (ls_first)\ndestroy lnv_value");
        let reconstructed = normalize_body(
            "string ls_first\nstring ls_second\nreturn ls_first\ndestroy(lnv_value)",
        );

        assert_eq!(
            safe_canonical_body(&source),
            safe_canonical_body(&reconstructed)
        );
    }

    #[test]
    fn safe_canonicalization_rejects_semantic_changes() {
        let different_guard = (
            normalize_body("if ai_value < 0 then return -1"),
            normalize_body("if ai_value <= 0 then\nreturn -1\nend if"),
        );
        let different_body = (
            normalize_body("if ai_value < 0 then return -1"),
            normalize_body("if ai_value < 0 then\nreturn 0\nend if"),
        );
        let different_precedence = (
            normalize_body("if (a = 1 or b = 2) and c = 3 then\nreturn -1\nend if"),
            normalize_body("if a = 1 or b = 2 and c = 3 then\nreturn -1\nend if"),
        );
        let initialized_declaration = (
            normalize_body("integer a = 1, b = 2"),
            normalize_body("integer a = 1\ninteger b = 2"),
        );
        let different_string = (
            normalize_body("return 'Failure'"),
            normalize_body("return \"Success\""),
        );
        let ambiguous_then_token = (
            normalize_body("if lengthen(ai_value) then return -1"),
            normalize_body("if lengthen(ai_value) then\nreturn -1\nend if"),
        );

        for (left, right) in [
            different_guard,
            different_body,
            different_precedence,
            initialized_declaration,
            different_string,
            ambiguous_then_token,
        ] {
            assert_ne!(safe_canonical_body(&left), safe_canonical_body(&right));
        }
    }

    #[test]
    fn structured_if_does_not_equal_goto_preview() {
        let source = "if value then\nreturn 1\nend if";
        let reconstructed = "if not value then goto L_0010\nreturn 1";

        assert_ne!(normalize_body(source), normalize_body(reconstructed));
    }

    #[test]
    fn whole_function_verification_is_distinct_from_rule_coverage() {
        let catalog = catalog_with_value_body("return ai_value");

        let mut equal = preview("return ai_value", true);
        catalog.compare("object.udo", 0, &mut equal);
        assert_eq!(
            equal.evidence.function_reconstruction,
            VerificationStatus::Verified
        );
        assert_eq!(
            equal
                .evidence
                .function_comparison
                .as_ref()
                .unwrap()
                .verification_basis,
            Some(FunctionVerificationBasis::NormalizedEquality)
        );

        let mut safely_equivalent = preview("if ai_value < 0 then\nreturn -1\nend if", true);
        let safe_catalog = catalog_with_value_body("if ai_value < 0 then return -1");
        safe_catalog.compare("object.udo", 0, &mut safely_equivalent);
        assert_eq!(
            safely_equivalent.evidence.function_reconstruction,
            VerificationStatus::Verified
        );
        assert_eq!(
            safely_equivalent
                .evidence
                .function_comparison
                .unwrap()
                .verification_basis,
            Some(FunctionVerificationBasis::SafeSemanticCanonicalization)
        );

        let mut different = preview("return ai_value + 1", true);
        catalog.compare("object.udo", 0, &mut different);
        assert_eq!(
            different.evidence.function_reconstruction,
            VerificationStatus::Mismatch
        );
        assert_eq!(
            different.evidence.function_comparison.unwrap().result,
            FunctionComparisonResult::NormalizedBodyMismatch
        );

        let mut incomplete = preview("return ai_value", false);
        catalog.compare("object.udo", 0, &mut incomplete);
        assert_eq!(
            incomplete.evidence.function_reconstruction,
            VerificationStatus::NotAssessed
        );
        assert_eq!(
            incomplete.evidence.function_comparison.unwrap().result,
            FunctionComparisonResult::SemanticRulesIncomplete
        );
    }
}
