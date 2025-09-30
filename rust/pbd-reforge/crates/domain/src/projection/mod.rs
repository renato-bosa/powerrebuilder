//! Projection Bounded Context
//!
//! Read models for queries, indexes, and caching.

pub mod index;

pub use index::{Catalogue, Location, Metrics, project, xref_symbols};
