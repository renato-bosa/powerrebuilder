//! PowerBuilder Version Descriptor
//!
//! Version-specific behavior is data-driven through a registry pattern.
//! No hardcoded version branches in domain logic.

use serde::{Deserialize, Serialize};
use std::fmt;

/// PowerBuilder version identifier
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PBVersion {
    pub major: u16,
    pub minor: u16,
}

impl PBVersion {
    pub const fn new(major: u16, minor: u16) -> Self {
        Self { major, minor }
    }

    /// Common versions as constants
    pub const PB6: Self = Self::new(6, 0);
    pub const PB7: Self = Self::new(7, 0);
    pub const PB9: Self = Self::new(9, 0);
    pub const PB10: Self = Self::new(10, 0);
    pub const PB11: Self = Self::new(11, 0);
    pub const PB12: Self = Self::new(12, 0);
    pub const PB12_5: Self = Self::new(12, 5);
    pub const PB2017: Self = Self::new(17, 0);
    pub const PB2019: Self = Self::new(19, 0);

    pub fn as_f32(&self) -> f32 {
        self.major as f32 + (self.minor as f32 / 10.0)
    }
}

impl fmt::Display for PBVersion {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}.{}", self.major, self.minor)
    }
}

impl PartialOrd for PBVersion {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for PBVersion {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        match self.major.cmp(&other.major) {
            std::cmp::Ordering::Equal => self.minor.cmp(&other.minor),
            ord => ord,
        }
    }
}

/// Version features that affect decoding
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VersionFeatures {
    pub has_unicode: bool,
    pub has_dotnet: bool,
    pub has_generics: bool,
    pub opcode_set: OpcodeSet,
    pub max_string_length: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OpcodeSet {
    Classic,    // PB 6-9
    Extended,   // PB 10-11
    Modern,     // PB 12+
    DotNet,     // PB 12+ with .NET
}

impl PBVersion {
    /// Get features for this version
    pub fn features(&self) -> VersionFeatures {
        let has_unicode = self.major >= 10;
        let has_dotnet = self.major >= 12;
        let has_generics = self.major >= 17;

        let opcode_set = if self.major >= 12 {
            if has_dotnet {
                OpcodeSet::DotNet
            } else {
                OpcodeSet::Modern
            }
        } else if self.major >= 10 {
            OpcodeSet::Extended
        } else {
            OpcodeSet::Classic
        };

        let max_string_length = if has_unicode { 32767 } else { 16383 };

        VersionFeatures {
            has_unicode,
            has_dotnet,
            has_generics,
            opcode_set,
            max_string_length,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version_comparison() {
        assert!(PBVersion::PB6 < PBVersion::PB12);
        assert!(PBVersion::PB12 < PBVersion::PB12_5);
        assert!(PBVersion::PB12_5 < PBVersion::PB2019);
    }

    #[test]
    fn test_version_features() {
        let pb6 = PBVersion::PB6.features();
        assert!(!pb6.has_unicode);
        assert!(!pb6.has_dotnet);
        assert_eq!(pb6.opcode_set, OpcodeSet::Classic);

        let pb12 = PBVersion::PB12.features();
        assert!(pb12.has_unicode);
        assert!(pb12.has_dotnet);
        assert_eq!(pb12.opcode_set, OpcodeSet::DotNet);
    }

    #[test]
    fn test_version_display() {
        assert_eq!(PBVersion::PB12_5.to_string(), "12.5");
        assert_eq!(PBVersion::PB2019.to_string(), "19.0");
    }
}
