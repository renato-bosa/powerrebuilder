//! Artifact - A unit of code/data within a PowerBuilder library.
//!
//! Artifacts represent the recoverable objects (windows, menus, functions, etc.)
//! stored in PBL/PBD archives.

use serde::{Deserialize, Serialize};
use std::fmt;

/// Unique identifier for an artifact
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ArtifactId(u64);

impl ArtifactId {
    pub fn new(id: u64) -> Self {
        Self(id)
    }

    pub fn from_name_and_kind(name: &str, kind: ArtifactKind) -> Self {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        let mut hasher = DefaultHasher::new();
        name.hash(&mut hasher);
        kind.hash(&mut hasher);
        Self(hasher.finish())
    }

    pub fn value(&self) -> u64 {
        self.0
    }
}

impl fmt::Display for ArtifactId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "art-{:016x}", self.0)
    }
}

/// Kind of PowerBuilder artifact
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ArtifactKind {
    Window,
    Menu,
    DataWindow,
    Script,
    Structure,
    Global,
    Function,
    UserObject,
    Application,
    Query,
    Pipeline,
    Proxy,
    Unknown,
}

impl fmt::Display for ArtifactKind {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Window => write!(f, "window"),
            Self::Menu => write!(f, "menu"),
            Self::DataWindow => write!(f, "datawindow"),
            Self::Script => write!(f, "script"),
            Self::Structure => write!(f, "structure"),
            Self::Global => write!(f, "global"),
            Self::Function => write!(f, "function"),
            Self::UserObject => write!(f, "userobject"),
            Self::Application => write!(f, "application"),
            Self::Query => write!(f, "query"),
            Self::Pipeline => write!(f, "pipeline"),
            Self::Proxy => write!(f, "proxy"),
            Self::Unknown => write!(f, "unknown"),
        }
    }
}

/// Byte span within a library file
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct ByteSpan {
    pub offset: usize,
    pub length: usize,
}

impl ByteSpan {
    pub fn new(offset: usize, length: usize) -> Self {
        Self { offset, length }
    }

    pub fn end(&self) -> usize {
        self.offset + self.length
    }

    pub fn contains(&self, offset: usize) -> bool {
        offset >= self.offset && offset < self.end()
    }

    pub fn overlaps(&self, other: &ByteSpan) -> bool {
        self.contains(other.offset)
            || self.contains(other.end())
            || other.contains(self.offset)
    }
}

/// Reference to an artifact within a library
///
/// This is a lightweight reference that doesn't contain the actual bytes.
/// The bytes are accessed through the library's byte slice.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArtifactRef {
    pub name: String,
    pub kind: ArtifactKind,
    pub span: ByteSpan,
}

impl ArtifactRef {
    pub fn id(&self) -> ArtifactId {
        ArtifactId::from_name_and_kind(&self.name, self.kind)
    }
}

/// Full artifact with bytes
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Artifact {
    pub id: ArtifactId,
    pub name: String,
    pub kind: ArtifactKind,
    pub span: ByteSpan,
}

/// Symbol table for cross-references
pub type SymTab = Vec<String>;

/// Classify byte spans into artifacts
///
/// Pure function that takes raw spans and symbol table to identify artifacts.
pub fn classify(spans: &[ByteSpan], symtab: &SymTab) -> Vec<Artifact> {
    spans
        .iter()
        .enumerate()
        .map(|(idx, span)| {
            // Try to find name in symbol table
            let name = symtab
                .get(idx)
                .cloned()
                .unwrap_or_else(|| format!("object_{}", idx));

            // Heuristic kind detection
            let kind = detect_kind_from_name(&name);

            Artifact {
                id: ArtifactId::from_name_and_kind(&name, kind),
                name,
                kind,
                span: *span,
            }
        })
        .collect()
}

/// Detect artifact kind from name
fn detect_kind_from_name(name: &str) -> ArtifactKind {
    let lower = name.to_lowercase();

    if lower.starts_with("w_") {
        ArtifactKind::Window
    } else if lower.starts_with("m_") {
        ArtifactKind::Menu
    } else if lower.starts_with("d_") {
        ArtifactKind::DataWindow
    } else if lower.starts_with("f_") || lower.contains("function") {
        ArtifactKind::Function
    } else if lower.starts_with("u_") {
        ArtifactKind::UserObject
    } else if lower.starts_with("s_") || lower.contains("struct") {
        ArtifactKind::Structure
    } else if lower.contains("global") {
        ArtifactKind::Global
    } else if lower.contains("application") {
        ArtifactKind::Application
    } else {
        ArtifactKind::Unknown
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_byte_span_contains() {
        let span = ByteSpan::new(100, 50);
        assert!(span.contains(100));
        assert!(span.contains(125));
        assert!(span.contains(149));
        assert!(!span.contains(150));
        assert!(!span.contains(99));
    }

    #[test]
    fn test_byte_span_overlaps() {
        let span1 = ByteSpan::new(100, 50);
        let span2 = ByteSpan::new(120, 50);
        let span3 = ByteSpan::new(200, 50);

        assert!(span1.overlaps(&span2));
        assert!(span2.overlaps(&span1));
        assert!(!span1.overlaps(&span3));
    }

    #[test]
    fn test_detect_kind_from_name() {
        assert_eq!(detect_kind_from_name("w_main"), ArtifactKind::Window);
        assert_eq!(detect_kind_from_name("m_file"), ArtifactKind::Menu);
        assert_eq!(detect_kind_from_name("d_customer"), ArtifactKind::DataWindow);
        assert_eq!(detect_kind_from_name("f_calculate"), ArtifactKind::Function);
        assert_eq!(detect_kind_from_name("u_control"), ArtifactKind::UserObject);
    }

    #[test]
    fn test_artifact_id_deterministic() {
        let id1 = ArtifactId::from_name_and_kind("test", ArtifactKind::Window);
        let id2 = ArtifactId::from_name_and_kind("test", ArtifactKind::Window);
        assert_eq!(id1, id2);

        let id3 = ArtifactId::from_name_and_kind("test", ArtifactKind::Menu);
        assert_ne!(id1, id3);
    }
}
