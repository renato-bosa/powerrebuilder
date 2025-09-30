//! Application Layer - Use Cases and Services
//!
//! Orchestrates domain logic to fulfill business workflows.
//! No domain logic here - pure orchestration.

pub mod ports;
pub mod services;
pub mod usecases;

/// Application-level errors
#[derive(Debug, thiserror::Error)]
pub enum AppErr {
    #[error("Domain error: {0}")]
    Domain(String),

    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Invalid state: {0}")]
    InvalidState(String),
}

pub type AppResult<T> = Result<T, AppErr>;
